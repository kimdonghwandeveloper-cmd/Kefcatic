import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Assistant(TimestampMixin, Base):
    __tablename__ = "assistants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    role_type: Mapped[str | None] = mapped_column(String)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    config: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    template_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assistants.id", ondelete="SET NULL")
    )

    user: Mapped["User"] = relationship(back_populates="assistants")  # type: ignore[name-defined]
    connectors: Mapped[list["AssistantConnector"]] = relationship(  # type: ignore[name-defined]
        back_populates="assistant", cascade="all, delete-orphan"
    )
    permission_policies: Mapped[list["PermissionPolicy"]] = relationship(  # type: ignore[name-defined]
        back_populates="assistant", cascade="all, delete-orphan"
    )
    triggers: Mapped[list["Trigger"]] = relationship(  # type: ignore[name-defined]
        back_populates="assistant", cascade="all, delete-orphan"
    )
    task_runs: Mapped[list["TaskRun"]] = relationship(  # type: ignore[name-defined]
        back_populates="assistant", cascade="all, delete-orphan"
    )
    memories: Mapped[list["AssistantMemory"]] = relationship(  # type: ignore[name-defined]
        back_populates="assistant", cascade="all, delete-orphan"
    )
