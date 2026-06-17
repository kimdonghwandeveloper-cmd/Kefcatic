"""Marketplace API.

SR-06: Installing a marketplace template forces the user to re-confirm each
       action_type approval_mode. The template's own settings are ignored.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.assistant import Assistant
from app.models.marketplace import MarketplaceTemplate, TemplateReview
from app.models.policy import PermissionPolicy
from app.models.user import User
from app.schemas.marketplace import (
    AdminReviewRequest,
    MarketplaceInstallRequest,
    MarketplaceTemplateCreate,
    MarketplaceTemplateOut,
    ReviewCreate,
    ReviewOut,
)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# ── Browse ────────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=list[MarketplaceTemplateOut])
async def list_marketplace_templates(
    q: str | None = Query(None, description="Search name/description"),
    connector: str | None = Query(None, description="Filter by required connector"),
    role_type: str | None = Query(None),
    sort: str = Query("install_count", description="install_count | avg_rating | created_at"),
    official_only: bool = False,
    session: AsyncSession = Depends(get_async_session),
) -> list[MarketplaceTemplate]:
    stmt = select(MarketplaceTemplate).where(MarketplaceTemplate.status == "approved")

    if official_only:
        stmt = stmt.where(MarketplaceTemplate.is_official.is_(True))
    if role_type:
        stmt = stmt.where(MarketplaceTemplate.role_type == role_type)
    if q:
        stmt = stmt.where(
            MarketplaceTemplate.name.ilike(f"%{q}%")
            | MarketplaceTemplate.description.ilike(f"%{q}%")
        )
    if connector:
        stmt = stmt.where(MarketplaceTemplate.required_connectors.any(connector))

    sort_col = {
        "install_count": MarketplaceTemplate.install_count.desc(),
        "avg_rating": MarketplaceTemplate.avg_rating.desc(),
        "created_at": MarketplaceTemplate.created_at.desc(),
    }.get(sort, MarketplaceTemplate.install_count.desc())
    stmt = stmt.order_by(sort_col)

    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/templates/{template_id}", response_model=MarketplaceTemplateOut)
async def get_marketplace_template(
    template_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> MarketplaceTemplate:
    tpl = await session.get(MarketplaceTemplate, template_id)
    if not tpl or tpl.status != "approved":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return tpl


# ── Submit ────────────────────────────────────────────────────────────────────

@router.post("/templates", response_model=MarketplaceTemplateOut, status_code=status.HTTP_201_CREATED)
async def submit_template(
    body: MarketplaceTemplateCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> MarketplaceTemplate:
    """Submit a new template for review. Initial status: pending."""
    tpl = MarketplaceTemplate(
        author_id=current_user.id,
        name=body.name,
        description=body.description,
        role_type=body.role_type,
        required_connectors=body.required_connectors,
        required_permissions=body.required_permissions,
        default_config=body.default_config,
        version=body.version,
        status="pending",
    )
    session.add(tpl)
    await session.flush()
    return tpl


# ── Install (SR-06) ───────────────────────────────────────────────────────────

@router.post("/templates/{template_id}/install", response_model=dict, status_code=status.HTTP_201_CREATED)
async def install_template(
    template_id: uuid.UUID,
    body: MarketplaceInstallRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Install a marketplace template as a new assistant.

    SR-06: Caller must supply approval_modes for every required_permission.
    """
    tpl = await session.get(MarketplaceTemplate, template_id)
    if not tpl or tpl.status != "approved":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Extract action_types from required_permissions ("action_type:mode" format)
    required_action_types = [p.split(":")[0] for p in (tpl.required_permissions or [])]
    missing = [a for a in required_action_types if a not in body.approval_modes]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing approval_mode for: {missing}",
        )

    # Create assistant from template
    assistant = Assistant(
        user_id=current_user.id,
        name=body.name or tpl.name,
        description=tpl.description,
        role_type=tpl.role_type,
        config=tpl.default_config,
        is_active=False,
        is_template=False,
    )
    session.add(assistant)
    await session.flush()

    # SR-06: create policies from USER's chosen modes only
    from app.api.templates import _risk_for_action, _reversible_for_action
    for action_type, approval_mode in body.approval_modes.items():
        session.add(PermissionPolicy(
            assistant_id=assistant.id,
            action_type=action_type,
            approval_mode=approval_mode,
            risk_level=_risk_for_action(action_type),
            is_reversible=_reversible_for_action(action_type),
        ))

    # Increment install count
    tpl.install_count += 1

    return {"assistant_id": str(assistant.id), "template_id": str(tpl.id)}


# ── Reviews ───────────────────────────────────────────────────────────────────

@router.get("/templates/{template_id}/reviews", response_model=list[ReviewOut])
async def list_reviews(
    template_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> list[TemplateReview]:
    tpl = await session.get(MarketplaceTemplate, template_id)
    if not tpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    result = await session.execute(
        select(TemplateReview)
        .where(TemplateReview.template_id == template_id)
        .order_by(TemplateReview.created_at.desc())
    )
    return result.scalars().all()


@router.post("/templates/{template_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    template_id: uuid.UUID,
    body: ReviewCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> TemplateReview:
    tpl = await session.get(MarketplaceTemplate, template_id)
    if not tpl or tpl.status != "approved":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Prevent duplicate review
    existing = await session.execute(
        select(TemplateReview).where(
            TemplateReview.template_id == template_id,
            TemplateReview.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already reviewed")

    review = TemplateReview(
        template_id=template_id,
        user_id=current_user.id,
        rating=body.rating,
        comment=body.comment,
    )
    session.add(review)
    await session.flush()

    # Recalculate avg_rating
    avg_result = await session.execute(
        select(func.avg(TemplateReview.rating)).where(TemplateReview.template_id == template_id)
    )
    tpl.avg_rating = float(avg_result.scalar() or 0)

    return review


# ── Report ────────────────────────────────────────────────────────────────────

@router.post("/templates/{template_id}/report", status_code=status.HTTP_204_NO_CONTENT)
async def report_template(
    template_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Flag a template for admin review. Idempotent — no body required."""
    tpl = await session.get(MarketplaceTemplate, template_id)
    if not tpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    # Mark as under review if not already
    if tpl.status == "approved":
        tpl.status = "under_review"


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.post("/admin/templates/{template_id}/approve", response_model=MarketplaceTemplateOut)
async def admin_approve(
    template_id: uuid.UUID,
    body: AdminReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> MarketplaceTemplate:
    """Approve a pending template. Admin only (is_superuser check)."""
    _require_admin(current_user)
    tpl = await session.get(MarketplaceTemplate, template_id)
    if not tpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    tpl.status = "approved"
    return tpl


@router.post("/admin/templates/{template_id}/reject", response_model=MarketplaceTemplateOut)
async def admin_reject(
    template_id: uuid.UUID,
    body: AdminReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> MarketplaceTemplate:
    """Reject a pending template. Admin only."""
    _require_admin(current_user)
    tpl = await session.get(MarketplaceTemplate, template_id)
    if not tpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    tpl.status = "rejected"
    return tpl


@router.get("/admin/templates", response_model=list[MarketplaceTemplateOut])
async def admin_list_pending(
    status_filter: str = Query("pending"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    session: AsyncSession = Depends(get_async_session),
) -> list[MarketplaceTemplate]:
    """List templates by status for admin dashboard."""
    _require_admin(current_user)
    result = await session.execute(
        select(MarketplaceTemplate)
        .where(MarketplaceTemplate.status == status_filter)
        .order_by(MarketplaceTemplate.created_at.asc())
    )
    return result.scalars().all()


@router.post("/admin/templates/{template_id}/official", response_model=MarketplaceTemplateOut)
async def admin_set_official(
    template_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> MarketplaceTemplate:
    """Grant official badge to an approved template."""
    _require_admin(current_user)
    tpl = await session.get(MarketplaceTemplate, template_id)
    if not tpl or tpl.status != "approved":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approved template not found")
    tpl.is_official = True
    return tpl


def _require_admin(user: User) -> None:
    if not getattr(user, "is_superuser", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
