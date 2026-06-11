"""Connector endpoints — YouTube OAuth2 connect flow."""
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.connector import ConnectorCredential
from app.models.user import User
from app.schemas.connector import ConnectorOut
from app.services.connector_credential_service import ConnectorCredentialService

router = APIRouter(prefix="/connectors", tags=["connectors"])

_pending_states: dict[str, str] = {}  # state → user_id


@router.get("/youtube/auth-url")
async def youtube_auth_url(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    from app.connectors.youtube import build_auth_url

    state = secrets.token_urlsafe(16)
    _pending_states[state] = str(current_user.id)
    return {"url": build_auth_url(state)}


@router.get("/youtube/callback")
async def youtube_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> ConnectorOut:
    import uuid

    from app.connectors.youtube import exchange_code

    user_id_str = _pending_states.pop(state, None)
    if user_id_str is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")

    token_data = await exchange_code(code)
    credentials = {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token", ""),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    scopes = token_data.get("scope", "").split()

    svc = ConnectorCredentialService(session)
    cred = await svc.store_encrypted(
        user_id=uuid.UUID(user_id_str),
        connector_type="youtube",
        credentials=credentials,
        scopes=scopes,
    )
    return ConnectorOut(
        id=str(cred.id),
        connector_type=cred.connector_type,
        scopes=cred.scopes,
    )


@router.get("", response_model=list[ConnectorOut])
async def list_connectors(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> list[ConnectorCredential]:
    result = await session.execute(
        select(ConnectorCredential).where(
            ConnectorCredential.user_id == current_user.id
        )
    )
    return result.scalars().all()
