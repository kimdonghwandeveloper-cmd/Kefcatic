import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def now_utc() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String)
    avatar_url: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = now_utc()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(back_populates="user")
    assistants: Mapped[list["Assistant"]] = relationship(back_populates="user")
    connector_credentials: Mapped[list["ConnectorCredential"]] = relationship(back_populates="user")


class OAuthAccount(Base):
    """Platform login credentials (who logged in via Google/GitHub)."""

    __tablename__ = "oauth_accounts"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)  # 'google', 'github'
    provider_account_id: Mapped[str] = mapped_column(String, nullable=False)
    # Stored encrypted — login session only
    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = now_utc()

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")


class Assistant(Base):
    __tablename__ = "assistants"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    role_type: Mapped[str | None] = mapped_column(String)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    config: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    template_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assistants.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = now_utc()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="assistants")
    connectors: Mapped[list["AssistantConnector"]] = relationship(back_populates="assistant")
    permission_policies: Mapped[list["PermissionPolicy"]] = relationship(back_populates="assistant")
    triggers: Mapped[list["Trigger"]] = relationship(back_populates="assistant")
    task_runs: Mapped[list["TaskRun"]] = relationship(back_populates="assistant")
    memories: Mapped[list["AssistantMemory"]] = relationship(back_populates="assistant")


class ConnectorCredential(Base):
    """External service credentials (what APIs the assistant can call). Separate from oauth_accounts."""

    __tablename__ = "connector_credentials"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    connector_type: Mapped[str] = mapped_column(String, nullable=False)  # 'youtube', 'gmail', ...
    # Fernet-encrypted JSONB — access only via ConnectorCredentialService.get_decrypted() (SR-03)
    credentials: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scopes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = now_utc()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="connector_credentials")
    assistant_connectors: Mapped[list["AssistantConnector"]] = relationship(
        back_populates="credential"
    )


class AssistantConnector(Base):
    __tablename__ = "assistant_connectors"

    id: Mapped[uuid.UUID] = uuid_pk()
    assistant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False
    )
    credential_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connector_credentials.id", ondelete="CASCADE"),
        nullable=False,
    )
    connector_type: Mapped[str] = mapped_column(String, nullable=False)
    granted_permissions: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    config: Mapped[dict | None] = mapped_column(JSONB)

    assistant: Mapped["Assistant"] = relationship(back_populates="connectors")
    credential: Mapped["ConnectorCredential"] = relationship(back_populates="assistant_connectors")


class PermissionPolicy(Base):
    __tablename__ = "permission_policies"

    id: Mapped[uuid.UUID] = uuid_pk()
    assistant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    # 'auto' | 'draft_only' | 'require_approval' | 'always_manual' | 'disabled'
    approval_mode: Mapped[str] = mapped_column(String, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)  # 'low' | 'medium' | 'high'
    is_reversible: Mapped[bool] = mapped_column(Boolean, default=True)

    assistant: Mapped["Assistant"] = relationship(back_populates="permission_policies")


class Trigger(Base):
    __tablename__ = "triggers"

    id: Mapped[uuid.UUID] = uuid_pk()
    assistant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False
    )
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)  # 'schedule' | 'event' | 'webhook'
    cron_expression: Mapped[str | None] = mapped_column(String)
    event_type: Mapped[str | None] = mapped_column(String)
    config: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Used by Celery Beat DB-scan dispatcher — updated after each fire
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assistant: Mapped["Assistant"] = relationship(back_populates="triggers")
    task_runs: Mapped[list["TaskRun"]] = relationship(back_populates="trigger")


class TaskRun(Base):
    __tablename__ = "task_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    assistant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False
    )
    trigger_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("triggers.id", ondelete="SET NULL")
    )
    # 'pending' | 'running' | 'waiting_approval' | 'completed' | 'failed' | 'cancelled'
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    result_summary: Mapped[dict | None] = mapped_column(JSONB)

    assistant: Mapped["Assistant"] = relationship(back_populates="task_runs")
    trigger: Mapped["Trigger | None"] = relationship(back_populates="task_runs")
    action_logs: Mapped[list["ActionLog"]] = relationship(back_populates="task_run")


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    task_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    # 'pending_approval' | 'approved' | 'rejected' | 'executed' | 'failed' | 'rolled_back'
    status: Mapped[str] = mapped_column(String, nullable=False)
    input_data: Mapped[dict | None] = mapped_column(JSONB)
    output_data: Mapped[dict | None] = mapped_column(JSONB)
    # Only populated when is_reversible=true
    rollback_data: Mapped[dict | None] = mapped_column(JSONB)
    # ID of the resource created in the external service (e.g. YouTube reply ID)
    # Required for rollback — never attempt rollback if NULL (SR-02)
    external_resource_id: Mapped[str | None] = mapped_column(String)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    task_run: Mapped["TaskRun"] = relationship(back_populates="action_logs")
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(back_populates="action_log")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    action_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("action_logs.id", ondelete="CASCADE"), nullable=False
    )
    requested_at: Mapped[datetime] = now_utc()
    # 'pending' | 'approved' | 'rejected'
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    # Modified input when user edits before approving
    modified_input: Mapped[dict | None] = mapped_column(JSONB)

    action_log: Mapped["ActionLog"] = relationship(back_populates="approval_requests")


class AssistantMemory(Base):
    __tablename__ = "assistant_memories"

    id: Mapped[uuid.UUID] = uuid_pk()
    assistant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False
    )
    memory_type: Mapped[str] = mapped_column(String, nullable=False)  # 'preference' | 'instruction' | 'context'
    key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = now_utc()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    assistant: Mapped["Assistant"] = relationship(back_populates="memories")
