from datetime import datetime
from uuid import UUID

from pydantic import BaseModel



class ActionLogOut(BaseModel):
    id: UUID
    task_run_id: UUID
    action_type: str
    status: str
    input_data: dict | None
    output_data: dict | None
    external_resource_id: str | None
    executed_at: datetime | None
    approved_by: UUID | None
    approved_at: datetime | None

    model_config = {"from_attributes": True}


class ApprovalRequestOut(BaseModel):
    id: UUID
    action_log_id: UUID
    requested_at: datetime
    status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    reviewer_note: str | None
    action_log: ActionLogOut | None = None

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    reviewer_note: str | None = None
    modified_input: dict | None = None  # "수정 후 승인" 시 사용


class BulkApproveRequest(BaseModel):
    action_log_ids: list[UUID]
