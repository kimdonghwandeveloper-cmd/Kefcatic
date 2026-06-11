"""SR-03: connector_credentials decryption is ONLY allowed through this service.

Never access the raw credentials JSONB in API routers.
Never log decrypted tokens.
"""
import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_data, encrypt_data
from app.models.connector import ConnectorCredential


class ConnectorCredentialService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_decrypted(self, credential_id: uuid.UUID) -> dict:
        """Return the decrypted credentials dict for the given credential row."""
        result = await self._session.execute(
            select(ConnectorCredential).where(ConnectorCredential.id == credential_id)
        )
        credential = result.scalar_one_or_none()
        if credential is None:
            raise ValueError(f"ConnectorCredential {credential_id} not found")

        encrypted_json = credential.credentials.get("_encrypted")
        if encrypted_json is None:
            # Legacy plain-text path (dev only); should not exist in production
            return dict(credential.credentials)

        return json.loads(decrypt_data(encrypted_json))

    async def store_encrypted(
        self,
        user_id: uuid.UUID,
        connector_type: str,
        credentials: dict,
        scopes: list[str] | None = None,
    ) -> ConnectorCredential:
        """Encrypt and persist credentials. Returns the saved model instance."""
        encrypted_json = encrypt_data(json.dumps(credentials))
        cred = ConnectorCredential(
            user_id=user_id,
            connector_type=connector_type,
            credentials={"_encrypted": encrypted_json},
            scopes=scopes,
        )
        self._session.add(cred)
        await self._session.flush()
        return cred
