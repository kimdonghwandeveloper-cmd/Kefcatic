import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ConnectorCredential(TimestampMixin, Base):
    __tablename__ = "connector_credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    connector_type: Mapped[str] = mapped_column(String, nullable=False)
    # Fernet-encrypted JSONB; only accessible via ConnectorCredentialService.get_decrypted()
    credentials: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scopes: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="connector_credentials")  # type: ignore[name-defined]
    assistant_connectors: Mapped[list["AssistantConnector"]] = relationship(
        back_populates="credential", cascade="all, delete-orphan"
    )


class AssistantConnector(Base):
    __tablename__ = "assistant_connectors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assistant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistants.id", ondelete="CASCADE"),
        nullable=False,
    )
    credential_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connector_credentials.id", ondelete="CASCADE"),
        nullable=False,
    )
    connector_type: Mapped[str] = mapped_column(String, nullable=False)
    granted_permissions: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    config: Mapped[dict | None] = mapped_column(JSONB)

    assistant: Mapped["Assistant"] = relationship(back_populates="connectors")  # type: ignore[name-defined]
    credential: Mapped["ConnectorCredential"] = relationship(
        back_populates="assistant_connectors"
    )
