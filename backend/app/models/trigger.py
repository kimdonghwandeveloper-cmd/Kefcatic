import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Trigger(Base):
    __tablename__ = "triggers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assistant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistants.id", ondelete="CASCADE"),
        nullable=False,
    )
    # schedule | event | webhook
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String)
    event_type: Mapped[str | None] = mapped_column(String)
    config: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Used by Celery Beat DB-scan; updated after each dispatch
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assistant: Mapped["Assistant"] = relationship(back_populates="triggers")  # type: ignore[name-defined]
    task_runs: Mapped[list["TaskRun"]] = relationship(  # type: ignore[name-defined]
        back_populates="trigger"
    )
