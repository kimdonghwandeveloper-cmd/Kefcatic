"""Assistant CRUD endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.assistant import Assistant
from app.models.policy import PermissionPolicy
from app.models.trigger import Trigger
from app.models.user import User
from app.schemas.assistant import AssistantCreate, AssistantOut, AssistantUpdate

router = APIRouter(prefix="/assistants", tags=["assistants"])


@router.get("", response_model=list[AssistantOut])
async def list_assistants(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> list[Assistant]:
    result = await session.execute(
        select(Assistant).where(
            Assistant.user_id == current_user.id,
            Assistant.is_template.is_(False),
        )
    )
    return result.scalars().all()


@router.post("", response_model=AssistantOut, status_code=status.HTTP_201_CREATED)
async def create_assistant(
    body: AssistantCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> Assistant:
    assistant = Assistant(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        role_type=body.role_type,
        system_prompt=body.system_prompt,
        config=body.config,
    )
    session.add(assistant)
    await session.flush()

    # Create default permission policies from config if provided
    if body.config and "approval_modes" in body.config:
        for action_type, mode in body.config["approval_modes"].items():
            policy = PermissionPolicy(
                assistant_id=assistant.id,
                action_type=action_type,
                approval_mode=mode,
                risk_level=_risk_for_action(action_type),
                is_reversible=_reversible_for_action(action_type),
            )
            session.add(policy)

    # Create a schedule trigger if cron_expression provided
    if body.config and "cron_expression" in body.config:
        from datetime import UTC, datetime
        from croniter import croniter
        cron_expr = body.config["cron_expression"]
        try:
            next_run = croniter(cron_expr, datetime.now(UTC)).get_next(datetime)
        except Exception:
            next_run = None
        trigger = Trigger(
            assistant_id=assistant.id,
            trigger_type="schedule",
            cron_expression=cron_expr,
            next_run_at=next_run,
        )
        session.add(trigger)

    return assistant


@router.get("/{assistant_id}", response_model=AssistantOut)
async def get_assistant(
    assistant_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> Assistant:
    assistant = await session.get(Assistant, assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found")
    return assistant


@router.patch("/{assistant_id}", response_model=AssistantOut)
async def update_assistant(
    assistant_id: uuid.UUID,
    body: AssistantUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> Assistant:
    assistant = await session.get(Assistant, assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(assistant, field, value)
    return assistant


def _risk_for_action(action_type: str) -> str:
    high = {"youtube.comment.hide", "youtube.comment.delete", "gmail.email.send"}
    medium = {"youtube.comment.reply", "gmail.draft.create"}
    return "high" if action_type in high else "medium" if action_type in medium else "low"


def _reversible_for_action(action_type: str) -> bool:
    return action_type in {
        "youtube.comment.reply",
        "youtube.comment.hide",
        "gmail.draft.create",
    }
