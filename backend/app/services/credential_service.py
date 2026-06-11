import json

from app.core.security import decrypt_credentials, encrypt_credentials


class ConnectorCredentialService:
    """SR-03: All connector credential decryption must go through this service."""

    @staticmethod
    def encrypt(data: dict) -> dict:
        """Encrypt a credentials dict for storage in connector_credentials.credentials."""
        return {"_encrypted": encrypt_credentials(json.dumps(data))}

    @staticmethod
    def get_decrypted(stored: dict) -> dict:
        """
        SR-03: Decrypt connector credentials.
        Never call this from API routers — service layer only.
        Never log the return value.
        """
        encrypted = stored.get("_encrypted")
        if not encrypted:
            # Already-plaintext credentials (dev/test only)
            return stored
        return json.loads(decrypt_credentials(encrypted))
