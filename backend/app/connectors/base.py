from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ConnectorItem(BaseModel):
    id: str
    content: Any
    metadata: dict
    created_at: str


class BaseConnector(ABC):
    connector_type: str  # class-level constant, set by subclass

    def __init__(self, credentials: dict, config: dict | None = None) -> None:
        self.credentials = credentials
        self.config = config or {}

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Verify that stored credentials are still valid."""

    @abstractmethod
    async def list_items(self, **kwargs: Any) -> list[ConnectorItem]:
        """Return a list of items from the connected service."""

    @abstractmethod
    async def read_item(self, item_id: str) -> ConnectorItem:
        """Return a single item by ID."""

    async def create_item(self, data: dict) -> ConnectorItem:
        raise NotImplementedError(f"{self.__class__.__name__} does not support create_item")

    async def update_item(self, item_id: str, data: dict) -> ConnectorItem:
        raise NotImplementedError(f"{self.__class__.__name__} does not support update_item")

    async def delete_item(self, item_id: str) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__} does not support delete_item")

    async def search(self, query: str, **kwargs: Any) -> list[ConnectorItem]:
        raise NotImplementedError(f"{self.__class__.__name__} does not support search")


CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {}


def register_connector(cls: type[BaseConnector]) -> type[BaseConnector]:
    CONNECTOR_REGISTRY[cls.connector_type] = cls
    return cls
