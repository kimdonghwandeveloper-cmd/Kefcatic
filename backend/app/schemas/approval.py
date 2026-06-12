from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ActionLogOut(BaseModel):
    id: str
    task_run_id: str
    action_type: str
    status: str
    input_data: dict | None
    output_data: dict | None
    external_resource_id: str | None
    executed_at: datetime | None
    approved_by: str | None
    approved_at: datetime | None

    model_config = {"from_attributes": True}


class ApprovalRequestOut(BaseModel):
    id: str
    action_log_id: str
    requested_at: datetime
    status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    reviewer_note: str | None
    action_log: ActionLogOut | None = None

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    reviewer_note: str | None = None
    modified_input: dict | None = None  # "수정 후 승인" 시 사용


class BulkApproveRequest(BaseModel):
    action_log_ids: list[str]
