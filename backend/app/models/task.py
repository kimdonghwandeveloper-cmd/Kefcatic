import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TaskRun(Base):
    __tablename__ = "task_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assistant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistants.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("triggers.id", ondelete="SET NULL")
    )
    # pending | running | waiting_approval | completed | failed | cancelled
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    result_summary: Mapped[dict | None] = mapped_column(JSONB)

    assistant: Mapped["Assistant"] = relationship(back_populates="task_runs")  # type: ignore[name-defined]
    trigger: Mapped["Trigger | None"] = relationship(back_populates="task_runs")  # type: ignore[name-defined]
    action_logs: Mapped[list["ActionLog"]] = relationship(  # type: ignore[name-defined]
        back_populates="task_run", cascade="all, delete-orphan"
    )
