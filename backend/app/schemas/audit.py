from datetime import datetime

from pydantic import BaseModel

from app.schemas.approval import ActionLogOut


class TaskRunDetailOut(BaseModel):
    id: str
    assistant_id: str
    trigger_id: str | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    result_summary: dict | None
    action_logs: list[ActionLogOut] = []

    model_config = {"from_attributes": True}


class TaskRunListOut(BaseModel):
    id: str
    assistant_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    result_summary: dict | None

    model_config = {"from_attributes": True}


class PaginatedTaskRuns(BaseModel):
    items: list[TaskRunListOut]
    total: int
    page: int
    page_size: int
