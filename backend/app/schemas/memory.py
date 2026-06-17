from uuid import UUID

from pydantic import BaseModel


class MemoryOut(BaseModel):
    id: UUID
    assistant_id: UUID
    memory_type: str
    key: str
    value: str

    model_config = {"from_attributes": True}


class MemoryCreate(BaseModel):
    memory_type: str = "fact"  # preference | instruction | context | fact
    key: str
    value: str


class MemoryUpdate(BaseModel):
    value: str
