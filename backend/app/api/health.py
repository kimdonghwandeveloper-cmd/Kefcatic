from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

router = APIRouter()


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_async_session)) -> dict:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}
