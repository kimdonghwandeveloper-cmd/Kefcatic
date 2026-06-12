"""Auth endpoints — Google OAuth2 platform login."""
import secrets
import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decrypt_data,
    encrypt_data,
)
from app.models.user import OAuthAccount, User
from app.schemas.auth import TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory state store for CSRF protection (replace with Redis in production)
_pending_states: set[str] = set()


@router.get("/google")
async def google_login() -> RedirectResponse:
    from app.connectors.youtube import build_auth_url

    state = secrets.token_urlsafe(16)
    _pending_states.add(state)
    return RedirectResponse(build_auth_url(state))


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
) -> TokenOut:
    if state not in _pending_states:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")
    _pending_states.discard(state)

    # Exchange code for tokens
    from app.connectors.youtube import exchange_code

    token_data = await exchange_code(code)
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token", "")

    # Fetch user info from Google
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        google_user = resp.json()

    google_id = google_user["id"]
    email = google_user["email"]
    name = google_user.get("name")
    avatar_url = google_user.get("picture")

    # Upsert user
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email, name=name, avatar_url=avatar_url)
        session.add(user)
        await session.flush()

    # Upsert oauth_account (SR-03: tokens are encrypted)
    result = await session.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == user.id,
            OAuthAccount.provider == "google",
            OAuthAccount.provider_account_id == google_id,
        )
    )
    oauth_acct = result.scalar_one_or_none()
    if oauth_acct is None:
        oauth_acct = OAuthAccount(
            user_id=user.id,
            provider="google",
            provider_account_id=google_id,
            access_token=encrypt_data(access_token),
            refresh_token=encrypt_data(refresh_token) if refresh_token else None,
        )
        session.add(oauth_acct)
    else:
        oauth_acct.access_token = encrypt_data(access_token)
        if refresh_token:
            oauth_acct.refresh_token = encrypt_data(refresh_token)

    return TokenOut(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    # JWT is stateless; client drops the token.
    # Add a token denylist here in Phase 5 if needed.
    pass
