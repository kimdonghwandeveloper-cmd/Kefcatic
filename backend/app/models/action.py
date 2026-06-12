import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    # pending_approval | approved | rejected | executed | failed | rolled_back
    status: Mapped[str] = mapped_column(String, nullable=False)
    input_data: Mapped[dict | None] = mapped_column(JSONB)
    output_data: Mapped[dict | None] = mapped_column(JSONB)
    # Only populated when is_reversible=True; holds data needed to undo the action
    rollback_data: Mapped[dict | None] = mapped_column(JSONB)
    # ID of the external resource created (e.g. YouTube reply ID); required before rollback
    external_resource_id: Mapped[str | None] = mapped_column(String)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    task_run: Mapped["TaskRun"] = relationship(back_populates="action_logs")  # type: ignore[name-defined]
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(  # type: ignore[name-defined]
        back_populates="action_log", cascade="all, delete-orphan"
    )
