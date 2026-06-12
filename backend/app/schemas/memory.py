from pydantic import BaseModel


class MemoryOut(BaseModel):
    id: str
    assistant_id: str
    memory_type: str
    key: str
    value: str

    model_config = {"from_attributes": True}


class MemoryCreate(BaseModel):
    memory_type: str  # preference | instruction | context
    key: str
    value: str


class MemoryUpdate(BaseModel):
    value: str
