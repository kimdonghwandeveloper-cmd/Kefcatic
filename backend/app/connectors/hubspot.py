"""HubSpot CRM connector (contacts + deals).

Credentials dict keys:
  access_token  — OAuth2 bearer token (decrypted by ConnectorCredentialService)
  refresh_token — OAuth2 refresh token

Required scopes:
  crm.objects.contacts.read, crm.objects.contacts.write
  crm.objects.deals.read,     crm.objects.deals.write

The CRM object type ('contacts' or 'deals') is chosen per call via the
`object_type` kwarg/data key, or via config['object_type']; defaults to 'contacts'.
"""
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorItem, register_connector
from app.connectors.oauth_helper import (
    build_hubspot_auth_url,
    ensure_fresh_hubspot_token,
    exchange_hubspot_code,
)
from app.core.config import settings

_HUBSPOT_API = "https://api.hubapi.com"
_CRM_OBJECTS = f"{_HUBSPOT_API}/crm/v3/objects"

_SUPPORTED_OBJECTS = {"contacts", "deals"}

_DEFAULT_PROPERTIES = {
    "contacts": ["email", "firstname", "lastname", "phone", "company"],
    "deals": ["dealname", "amount", "dealstage", "pipeline", "closedate"],
}

_SCOPES = [
    "crm.objects.contacts.read",
    "crm.objects.contacts.write",
    "crm.objects.deals.read",
    "crm.objects.deals.write",
]

_HUBSPOT_REDIRECT_URI = "http://localhost:8000/api/connectors/hubspot/callback"


def build_auth_url(state: str) -> str:
    redirect_uri = getattr(settings, "hubspot_redirect_uri", _HUBSPOT_REDIRECT_URI)
    return build_hubspot_auth_url(_SCOPES, state, redirect_uri)


async def exchange_code(code: str) -> dict:
    redirect_uri = getattr(settings, "hubspot_redirect_uri", _HUBSPOT_REDIRECT_URI)
    return await exchange_hubspot_code(code, redirect_uri)


@register_connector
class HubSpotConnector(BaseConnector):
    connector_type = "hubspot"

    async def _fresh_headers(self) -> dict[str, str]:
        self.credentials = await ensure_fresh_hubspot_token(self.credentials)
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    def _object_type(self, override: str | None = None) -> str:
        obj = override or self.config.get("object_type", "contacts")
        if obj not in _SUPPORTED_OBJECTS:
            raise ValueError(f"Unsupported HubSpot object type: {obj}")
        return obj

    async def validate_credentials(self) -> bool:
        token = self.credentials.get("access_token", "")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_HUBSPOT_API}/oauth/v1/access-tokens/{token}",
            )
            return resp.status_code == 200

    async def list_items(self, **kwargs: Any) -> list[ConnectorItem]:
        """List CRM records.

        kwargs:
          object_type (str)  — 'contacts' or 'deals'
          max_results (int)  — default 20 (HubSpot 'limit')
          after (str)        — pagination cursor
          properties (list)  — properties to fetch
        """
        object_type = self._object_type(kwargs.get("object_type"))
        properties = kwargs.get("properties", _DEFAULT_PROPERTIES[object_type])
        params: dict[str, Any] = {
            "limit": kwargs.get("max_results", 20),
            "properties": properties,
        }
        if after := kwargs.get("after"):
            params["after"] = after

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_CRM_OBJECTS}/{object_type}",
                headers=await self._fresh_headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        return [_record_to_item(r, object_type) for r in data.get("results", [])]

    async def read_item(self, item_id: str) -> ConnectorItem:
        """Read a single record. item_id may be 'object_type:id' or just 'id'."""
        if ":" in item_id:
            object_type, _, record_id = item_id.partition(":")
            object_type = self._object_type(object_type)
        else:
            object_type, record_id = self._object_type(), item_id

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_CRM_OBJECTS}/{object_type}/{record_id}",
                headers=await self._fresh_headers(),
                params={"properties": _DEFAULT_PROPERTIES[object_type]},
            )
            resp.raise_for_status()
            record = resp.json()
        return _record_to_item(record, object_type)

    async def create_item(self, data: dict) -> ConnectorItem:
        """Create a CRM record.

        data keys:
          object_type (str)  — 'contacts' or 'deals'
          properties (dict)  — record properties (required)
        """
        object_type = self._object_type(data.get("object_type"))
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_CRM_OBJECTS}/{object_type}",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                json={"properties": data["properties"]},
            )
            resp.raise_for_status()
            record = resp.json()
        return _record_to_item(record, object_type)

    async def update_item(self, item_id: str, data: dict) -> ConnectorItem:
        """Patch a CRM record's properties. item_id may be 'object_type:id' or 'id'."""
        if ":" in item_id:
            object_type, _, record_id = item_id.partition(":")
            object_type = self._object_type(object_type)
        else:
            object_type, record_id = self._object_type(data.get("object_type")), item_id

        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{_CRM_OBJECTS}/{object_type}/{record_id}",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                json={"properties": data["properties"]},
            )
            resp.raise_for_status()
            record = resp.json()
        return _record_to_item(record, object_type)

    async def delete_item(self, item_id: str) -> bool:
        """Archive a CRM record. item_id may be 'object_type:id' or 'id'."""
        if ":" in item_id:
            object_type, _, record_id = item_id.partition(":")
            object_type = self._object_type(object_type)
        else:
            object_type, record_id = self._object_type(), item_id

        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{_CRM_OBJECTS}/{object_type}/{record_id}",
                headers=await self._fresh_headers(),
            )
        return resp.status_code in (200, 204)

    async def search(self, query: str, **kwargs: Any) -> list[ConnectorItem]:
        """Full-text search within an object type via the CRM search API."""
        object_type = self._object_type(kwargs.get("object_type"))
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_CRM_OBJECTS}/{object_type}/search",
                headers={**await self._fresh_headers(), "Content-Type": "application/json"},
                json={
                    "query": query,
                    "limit": kwargs.get("max_results", 20),
                    "properties": _DEFAULT_PROPERTIES[object_type],
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return [_record_to_item(r, object_type) for r in data.get("results", [])]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _record_to_item(record: dict, object_type: str) -> ConnectorItem:
    props = record.get("properties", {})
    return ConnectorItem(
        id=f"{object_type}:{record.get('id', '')}",
        content=props,
        metadata={
            "object_type": object_type,
            "record_id": record.get("id", ""),
            "archived": record.get("archived", False),
            "updated_at": record.get("updatedAt", ""),
        },
        created_at=record.get("createdAt", ""),
    )
