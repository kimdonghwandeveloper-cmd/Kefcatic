import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class MarketplaceTemplate(TimestampMixin, Base):
    __tablename__ = "marketplace_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    role_type: Mapped[str | None] = mapped_column(String)
    required_connectors: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    required_permissions: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    default_config: Mapped[dict | None] = mapped_column(JSONB)
    version: Mapped[str] = mapped_column(String, nullable=False, default="1.0.0")
    install_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_rating: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    reviews: Mapped[list["TemplateReview"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class TemplateReview(Base):
    __tablename__ = "template_reviews"
    __table_args__ = (
        UniqueConstraint("template_id", "user_id", name="uq_template_reviews_user_template"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_templates.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    template: Mapped[MarketplaceTemplate] = relationship(back_populates="reviews")
