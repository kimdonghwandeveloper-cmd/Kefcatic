"""Action Engine — core execution gate.

SR-01: approval_mode is checked before every external API call.
"""
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Callable

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import ActionLog
from app.models.approval import ApprovalRequest
from app.models.policy import PermissionPolicy


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApprovalMode(str, Enum):
    AUTO = "auto"
    DRAFT_ONLY = "draft_only"
    REQUIRE_APPROVAL = "require_approval"
    ALWAYS_MANUAL = "always_manual"
    DISABLED = "disabled"


class ActionDefinition(BaseModel):
    action_type: str
    description: str
    input_schema: dict
    output_schema: dict
    required_permission: str
    risk_level: RiskLevel
    default_approval_mode: ApprovalMode
    is_reversible: bool


ACTION_REGISTRY: dict[str, ActionDefinition] = {}
ACTION_HANDLERS: dict[str, Callable] = {}


def register_action(definition: ActionDefinition, handler: Callable) -> None:
    ACTION_REGISTRY[definition.action_type] = definition
    ACTION_HANDLERS[definition.action_type] = handler


# ── YouTube action definitions ────────────────────────────────────────────────

_YOUTUBE_ACTIONS: list[ActionDefinition] = [
    ActionDefinition(
        action_type="youtube.comment.list",
        description="채널의 최근 댓글 목록 조회",
        input_schema={"max_results": "integer", "page_token": "string"},
        output_schema={"comments": "array"},
        required_permission="comments.read",
        risk_level=RiskLevel.LOW,
        default_approval_mode=ApprovalMode.AUTO,
        is_reversible=False,
    ),
    ActionDefinition(
        action_type="youtube.comment.reply",
        description="댓글에 답글 작성",
        input_schema={"comment_id": "string", "text": "string"},
        output_schema={"reply_id": "string"},
        required_permission="comments.reply",
        risk_level=RiskLevel.MEDIUM,
        default_approval_mode=ApprovalMode.REQUIRE_APPROVAL,
        is_reversible=True,
    ),
    ActionDefinition(
        action_type="youtube.comment.hide",
        description="댓글 숨김 처리",
        input_schema={"comment_id": "string"},
        output_schema={"success": "boolean"},
        required_permission="comments.moderate",
        risk_level=RiskLevel.HIGH,
        default_approval_mode=ApprovalMode.REQUIRE_APPROVAL,
        is_reversible=True,
    ),
]

for _action in _YOUTUBE_ACTIONS:
    ACTION_REGISTRY[_action.action_type] = _action

# ── Gmail action definitions ──────────────────────────────────────────────────

_GMAIL_ACTIONS: list[ActionDefinition] = [
    ActionDefinition(
        action_type="gmail.message.list",
        description="받은편지함 미확인 메일 목록 조회",
        input_schema={"max_results": "integer"},
        output_schema={"messages": "array"},
        required_permission="messages.read",
        risk_level=RiskLevel.LOW,
        default_approval_mode=ApprovalMode.AUTO,
        is_reversible=False,
    ),
    ActionDefinition(
        action_type="gmail.draft.create",
        description="답장 초안 작성",
        input_schema={"thread_id": "string", "to": "string", "subject": "string", "body": "string"},
        output_schema={"draft_id": "string"},
        required_permission="drafts.create",
        risk_level=RiskLevel.MEDIUM,
        default_approval_mode=ApprovalMode.REQUIRE_APPROVAL,
        is_reversible=True,
    ),
    ActionDefinition(
        action_type="gmail.message.label",
        description="메일 레이블 변경 (읽음/중요 등)",
        input_schema={"message_id": "string", "add_labels": "array", "remove_labels": "array"},
        output_schema={"success": "boolean"},
        required_permission="messages.modify",
        risk_level=RiskLevel.LOW,
        default_approval_mode=ApprovalMode.AUTO,
        is_reversible=True,
    ),
]

for _action in _GMAIL_ACTIONS:
    ACTION_REGISTRY[_action.action_type] = _action

# ── Google Drive action definitions ──────────────────────────────────────────

_DRIVE_ACTIONS: list[ActionDefinition] = [
    ActionDefinition(
        action_type="drive.file.list",
        description="Drive 파일 목록 조회",
        input_schema={"folder_id": "string", "max_results": "integer"},
        output_schema={"files": "array"},
        required_permission="files.read",
        risk_level=RiskLevel.LOW,
        default_approval_mode=ApprovalMode.AUTO,
        is_reversible=False,
    ),
    ActionDefinition(
        action_type="drive.file.read",
        description="파일 내용 읽기 (Google Docs, PDF)",
        input_schema={"file_id": "string"},
        output_schema={"content": "string"},
        required_permission="files.read",
        risk_level=RiskLevel.LOW,
        default_approval_mode=ApprovalMode.AUTO,
        is_reversible=False,
    ),
    ActionDefinition(
        action_type="drive.document.create",
        description="Google Docs 문서 생성",
        input_schema={"title": "string", "content": "string"},
        output_schema={"file_id": "string"},
        required_permission="files.create",
        risk_level=RiskLevel.MEDIUM,
        default_approval_mode=ApprovalMode.REQUIRE_APPROVAL,
        is_reversible=True,
    ),
]

for _action in _DRIVE_ACTIONS:
    ACTION_REGISTRY[_action.action_type] = _action


# ── Execution gate ────────────────────────────────────────────────────────────

class ActionResult(BaseModel):
    action_log_id: uuid.UUID
    status: str  # executed | draft | pending_approval | rejected | disabled
    output_data: dict | None = None
    approval_request_id: uuid.UUID | None = None


async def execute_action(
    session: AsyncSession,
    *,
    task_run_id: uuid.UUID,
    action_type: str,
    assistant_id: uuid.UUID,
    input_data: dict,
    handler: Callable | None = None,
) -> ActionResult:
    """Gate every external API call through the approval_mode check (SR-01)."""

    definition = ACTION_REGISTRY.get(action_type)
    if definition is None:
        raise ValueError(f"Unknown action_type: {action_type}")

    # Resolve approval_mode from permission_policies, fall back to default
    result = await session.execute(
        select(PermissionPolicy).where(
            PermissionPolicy.assistant_id == assistant_id,
            PermissionPolicy.action_type == action_type,
        )
    )
    policy = result.scalar_one_or_none()
    approval_mode = ApprovalMode(policy.approval_mode) if policy else definition.default_approval_mode

    # Create the action_log entry
    action_log = ActionLog(
        task_run_id=task_run_id,
        action_type=action_type,
        status="pending_approval",
        input_data=input_data,
        rollback_data=None,
        external_resource_id=None,
    )
    session.add(action_log)
    await session.flush()  # obtain action_log.id

    # SR-01 gate
    if approval_mode == ApprovalMode.DISABLED:
        action_log.status = "rejected"
        return ActionResult(action_log_id=action_log.id, status="disabled")

    if approval_mode == ApprovalMode.DRAFT_ONLY:
        action_log.status = "draft"
        # output_data holds the draft; no external API call
        action_log.output_data = {"draft": input_data}
        return ActionResult(
            action_log_id=action_log.id,
            status="draft",
            output_data=action_log.output_data,
        )

    if approval_mode in (ApprovalMode.REQUIRE_APPROVAL, ApprovalMode.ALWAYS_MANUAL):
        # SR-04: only one pending approval_request per task_run + action_type
        existing = await session.execute(
            select(ApprovalRequest)
            .join(ActionLog, ApprovalRequest.action_log_id == ActionLog.id)
            .where(
                ActionLog.task_run_id == task_run_id,
                ActionLog.action_type == action_type,
                ApprovalRequest.status == "pending",
            )
        )
        existing_req = existing.scalar_one_or_none()
        if existing_req:
            return ActionResult(
                action_log_id=existing_req.action_log_id,
                status="pending_approval",
                approval_request_id=existing_req.id,
            )

        approval_req = ApprovalRequest(
            action_log_id=action_log.id,
            requested_at=datetime.now(UTC),
            status="pending",
        )
        session.add(approval_req)
        await session.flush()
        action_log.status = "pending_approval"
        return ActionResult(
            action_log_id=action_log.id,
            status="pending_approval",
            approval_request_id=approval_req.id,
        )

    # ApprovalMode.AUTO — proceed with the external call
    resolved_handler = handler or ACTION_HANDLERS.get(action_type)
    if resolved_handler is None:
        raise NotImplementedError(f"No handler registered for {action_type}")

    try:
        output = await resolved_handler(input_data)
        action_log.status = "executed"
        action_log.output_data = output
        action_log.executed_at = datetime.now(UTC)
        if definition.is_reversible and isinstance(output, dict):
            action_log.external_resource_id = output.get("id") or output.get("reply_id")
            action_log.rollback_data = {"original_input": input_data}
        return ActionResult(
            action_log_id=action_log.id,
            status="executed",
            output_data=output,
        )
    except Exception as exc:
        action_log.status = "failed"
        action_log.output_data = {"error": str(exc)}
        raise
