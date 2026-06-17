from uuid import UUID

from pydantic import BaseModel


class TemplateOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    role_type: str | None
    config: dict | None
    is_template: bool

    model_config = {"from_attributes": True}


class InstallTemplateRequest(BaseModel):
    # SR-06: user must explicitly confirm each action_type approval_mode
    # Key: action_type, Value: approval_mode the user chose
    approval_modes: dict[str, str]
    name: str | None = None  # override template name


class SaveAsTemplateRequest(BaseModel):
    name: str
    description: str | None = None
