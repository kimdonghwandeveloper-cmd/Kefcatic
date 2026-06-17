from uuid import UUID

from pydantic import BaseModel


class AssistantOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    role_type: str | None
    is_active: bool
    is_template: bool
    system_prompt: str | None

    model_config = {"from_attributes": True}


class AssistantCreate(BaseModel):
    name: str
    description: str | None = None
    role_type: str | None = None
    system_prompt: str | None = None
    config: dict | None = None


class AssistantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    config: dict | None = None
    is_active: bool | None = None
