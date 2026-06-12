from datetime import datetime

from pydantic import BaseModel


class TaskRunOut(BaseModel):
    id: str
    assistant_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    result_summary: dict | None

    model_config = {"from_attributes": True}
