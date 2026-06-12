import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MarketplaceTemplateOut(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    name: str
    description: str | None
    role_type: str | None
    required_connectors: list[str]
    required_permissions: list[str]
    default_config: dict | None
    version: str
    install_count: int
    avg_rating: float | None
    status: str
    is_official: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MarketplaceTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    role_type: str | None = None
    required_connectors: list[str] = []
    required_permissions: list[str] = []
    default_config: dict | None = None
    version: str = "1.0.0"


class MarketplaceInstallRequest(BaseModel):
    # SR-06: user must explicitly supply approval_mode for each action_type
    approval_modes: dict[str, str]
    name: str | None = None


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class ReviewOut(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminReviewRequest(BaseModel):
    comment: str | None = None
