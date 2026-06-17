"""Template system endpoints.

SR-06: Installing a template forces the user to re-confirm each action_type
       approval_mode. The template author's 'auto' setting is NEVER inherited.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.assistant import Assistant
from app.models.policy import PermissionPolicy
from app.models.user import User
from app.schemas.template import InstallTemplateRequest, SaveAsTemplateRequest, TemplateOut

router = APIRouter(prefix="/assistants", tags=["templates"])


@router.get("/templates", response_model=list[TemplateOut])
async def list_templates(
    session: AsyncSession = Depends(get_async_session),
) -> list[Assistant]:
    """List all published templates (official seeds + user-saved)."""
    result = await session.execute(
        select(Assistant).where(Assistant.is_template.is_(True))
    )
    return result.scalars().all()


@router.get("/templates/{template_id}", response_model=TemplateOut)
async def get_template(
    template_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> Assistant:
    template = await session.get(Assistant, template_id)
    if not template or not template.is_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.post("/from-template/{template_id}", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def install_template(
    template_id: uuid.UUID,
    body: InstallTemplateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> Assistant:
    """Create a new assistant from a template.

    SR-06: The caller must supply approval_modes for every action_type the
    template uses. The template's own approval settings are ignored entirely.
    """
    template = await session.get(Assistant, template_id)
    if not template or not template.is_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Determine which action_types this template requires
    template_config = template.config or {}
    required_actions: list[str] = template_config.get("required_action_types", [])

    # Verify the user supplied a mode for every required action
    missing = [a for a in required_actions if a not in body.approval_modes]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing approval_mode for: {missing}",
        )

    # Create the new assistant (copy of template)
    new_assistant = Assistant(
        user_id=current_user.id,
        name=body.name or template.name,
        description=template.description,
        role_type=template.role_type,
        system_prompt=template.system_prompt,
        config=template.config,
        is_active=False,  # user activates manually after connecting credentials
        is_template=False,
        template_source_id=template.id,
    )
    session.add(new_assistant)
    await session.flush()

    # SR-06: create PermissionPolicy rows from the USER's chosen modes (not template's)
    for action_type, approval_mode in body.approval_modes.items():
        policy = PermissionPolicy(
            assistant_id=new_assistant.id,
            action_type=action_type,
            approval_mode=approval_mode,
            risk_level=_risk_for_action(action_type),
            is_reversible=_reversible_for_action(action_type),
        )
        session.add(policy)

    return new_assistant


@router.post("/{assistant_id}/save-as-template", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def save_as_template(
    assistant_id: uuid.UUID,
    body: SaveAsTemplateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> Assistant:
    """Save an existing assistant as a reusable template."""
    assistant = await session.get(Assistant, assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found")

    # Collect the action_types this assistant has policies for
    result = await session.execute(
        select(PermissionPolicy).where(PermissionPolicy.assistant_id == assistant_id)
    )
    policies = result.scalars().all()
    required_action_types = [p.action_type for p in policies]

    template = Assistant(
        user_id=current_user.id,
        name=body.name,
        description=body.description or assistant.description,
        role_type=assistant.role_type,
        system_prompt=assistant.system_prompt,
        config={
            **(assistant.config or {}),
            "required_action_types": required_action_types,
        },
        is_active=False,
        is_template=True,
    )
    session.add(template)
    await session.flush()
    return template


def _risk_for_action(action_type: str) -> str:
    high = {"youtube.comment.hide", "gmail.email.send", "drive.file.delete"}
    medium = {"youtube.comment.reply", "gmail.draft.create", "drive.document.create"}
    return "high" if action_type in high else "medium" if action_type in medium else "low"


def _reversible_for_action(action_type: str) -> bool:
    return action_type in {
        "youtube.comment.reply",
        "youtube.comment.hide",
        "gmail.draft.create",
        "drive.document.create",
    }
