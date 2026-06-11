from pydantic import BaseModel


class ConnectorOut(BaseModel):
    id: str
    connector_type: str
    scopes: list[str] | None

    model_config = {"from_attributes": True}
