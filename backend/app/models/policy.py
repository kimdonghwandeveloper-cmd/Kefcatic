import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PermissionPolicy(Base):
    __tablename__ = "permission_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assistant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistants.id", ondelete="CASCADE"),
        nullable=False,
    )
    # e.g. 'comment.reply', 'comment.hide'
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    # auto | draft_only | require_approval | always_manual | disabled
    approval_mode: Mapped[str] = mapped_column(String, nullable=False)
    # low | medium | high
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    is_reversible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    assistant: Mapped["Assistant"] = relationship(back_populates="permission_policies")  # type: ignore[name-defined]
