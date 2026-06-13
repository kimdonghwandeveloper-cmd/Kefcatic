"""Connector endpoints — OAuth2 connect flows for YouTube, Gmail, Google Drive."""
import secrets
import uuid
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


# ── Generic OAuth helpers ─────────────────────────────────────────────────────

def _save_state(user_id: str) -> str:
    state = secrets.token_urlsafe(16)
    _pending_states[state] = user_id
    return state


def _pop_state(state: str) -> str:
    user_id = _pending_states.pop(state, None)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")
    return user_id


async def _store_connector(
    session: AsyncSession,
    user_id: str,
    connector_type: str,
    token_data: dict,
) -> ConnectorCredential:
    credentials = {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token", ""),
    }
    # Google delimits scopes with spaces; Slack uses commas.
    raw_scope = token_data.get("scope", "")
    scopes = [s for s in raw_scope.replace(",", " ").split() if s]
    svc = ConnectorCredentialService(session)
    return await svc.store_encrypted(
        user_id=uuid.UUID(user_id),
        connector_type=connector_type,
        credentials=credentials,
        scopes=scopes,
    )


# ── YouTube ───────────────────────────────────────────────────────────────────

@router.get("/youtube/auth-url")
async def youtube_auth_url(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    from app.connectors.youtube import build_auth_url
    return {"url": build_auth_url(_save_state(str(current_user.id)))}


@router.get("/youtube/callback")
async def youtube_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> ConnectorOut:
    from app.connectors.youtube import exchange_code
    user_id = _pop_state(state)
    token_data = await exchange_code(code)
    cred = await _store_connector(session, user_id, "youtube", token_data)
    return ConnectorOut(id=str(cred.id), connector_type=cred.connector_type, scopes=cred.scopes)


# ── Gmail ─────────────────────────────────────────────────────────────────────

@router.get("/gmail/auth-url")
async def gmail_auth_url(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    from app.connectors.gmail import build_auth_url
    return {"url": build_auth_url(_save_state(str(current_user.id)))}


@router.get("/gmail/callback")
async def gmail_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> ConnectorOut:
    from app.connectors.gmail import exchange_code
    user_id = _pop_state(state)
    token_data = await exchange_code(code)
    cred = await _store_connector(session, user_id, "gmail", token_data)
    return ConnectorOut(id=str(cred.id), connector_type=cred.connector_type, scopes=cred.scopes)


# ── Google Drive ──────────────────────────────────────────────────────────────

@router.get("/google-drive/auth-url")
async def drive_auth_url(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    from app.connectors.google_drive import build_auth_url
    return {"url": build_auth_url(_save_state(str(current_user.id)))}


@router.get("/google-drive/callback")
async def drive_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> ConnectorOut:
    from app.connectors.google_drive import exchange_code
    user_id = _pop_state(state)
    token_data = await exchange_code(code)
    cred = await _store_connector(session, user_id, "google_drive", token_data)
    return ConnectorOut(id=str(cred.id), connector_type=cred.connector_type, scopes=cred.scopes)


# ── Google Calendar ───────────────────────────────────────────────────────────

@router.get("/google-calendar/auth-url")
async def calendar_auth_url(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    from app.connectors.google_calendar import build_auth_url
    return {"url": build_auth_url(_save_state(str(current_user.id)))}


@router.get("/google-calendar/callback")
async def calendar_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> ConnectorOut:
    from app.connectors.google_calendar import exchange_code
    user_id = _pop_state(state)
    token_data = await exchange_code(code)
    cred = await _store_connector(session, user_id, "google_calendar", token_data)
    return ConnectorOut(id=str(cred.id), connector_type=cred.connector_type, scopes=cred.scopes)


# ── Google Sheets ─────────────────────────────────────────────────────────────

@router.get("/google-sheets/auth-url")
async def sheets_auth_url(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    from app.connectors.google_sheets import build_auth_url
    return {"url": build_auth_url(_save_state(str(current_user.id)))}


@router.get("/google-sheets/callback")
async def sheets_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> ConnectorOut:
    from app.connectors.google_sheets import exchange_code
    user_id = _pop_state(state)
    token_data = await exchange_code(code)
    cred = await _store_connector(session, user_id, "google_sheets", token_data)
    return ConnectorOut(id=str(cred.id), connector_type=cred.connector_type, scopes=cred.scopes)


# ── Slack ─────────────────────────────────────────────────────────────────────

@router.get("/slack/auth-url")
async def slack_auth_url(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    from app.connectors.slack import build_auth_url
    return {"url": build_auth_url(_save_state(str(current_user.id)))}


@router.get("/slack/callback")
async def slack_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> ConnectorOut:
    from app.connectors.slack import exchange_code
    user_id = _pop_state(state)
    token_data = await exchange_code(code)
    cred = await _store_connector(session, user_id, "slack", token_data)
    return ConnectorOut(id=str(cred.id), connector_type=cred.connector_type, scopes=cred.scopes)


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ConnectorOut])
async def list_connectors(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> list[ConnectorCredential]:
    result = await session.execute(
        select(ConnectorCredential).where(ConnectorCredential.user_id == current_user.id)
    )
    return result.scalars().all()


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    credential_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> None:
    cred = await session.get(ConnectorCredential, credential_id)
    if not cred or cred.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    await session.delete(cred)
