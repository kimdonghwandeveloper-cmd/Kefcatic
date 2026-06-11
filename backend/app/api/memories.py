"""Assistant memory CRUD endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.assistant import Assistant
from app.models.memory import AssistantMemory
from app.models.user import User
from app.schemas.memory import MemoryCreate, MemoryOut, MemoryUpdate

router = APIRouter(prefix="/assistants/{assistant_id}/memories", tags=["memories"])


async def _get_owned_assistant(
    assistant_id: uuid.UUID,
    current_user: User,
    session: AsyncSession,
) -> Assistant:
    assistant = await session.get(Assistant, assistant_id)
    if not assistant or assistant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found")
    return assistant


@router.get("", response_model=list[MemoryOut])
async def list_memories(
    assistant_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> list[AssistantMemory]:
    await _get_owned_assistant(assistant_id, current_user, session)
    result = await session.execute(
        select(AssistantMemory)
        .where(AssistantMemory.assistant_id == assistant_id)
        .order_by(AssistantMemory.memory_type, AssistantMemory.key)
    )
    return result.scalars().all()


@router.post("", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
async def create_memory(
    assistant_id: uuid.UUID,
    body: MemoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> AssistantMemory:
    await _get_owned_assistant(assistant_id, current_user, session)

    # Prevent duplicate keys within same assistant
    existing = await session.execute(
        select(AssistantMemory).where(
            AssistantMemory.assistant_id == assistant_id,
            AssistantMemory.key == body.key,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Memory key '{body.key}' already exists",
        )

    memory = AssistantMemory(
        assistant_id=assistant_id,
        memory_type=body.memory_type,
        key=body.key,
        value=body.value,
    )
    session.add(memory)
    await session.flush()
    return memory


@router.get("/{key}", response_model=MemoryOut)
async def get_memory(
    assistant_id: uuid.UUID,
    key: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> AssistantMemory:
    await _get_owned_assistant(assistant_id, current_user, session)
    result = await session.execute(
        select(AssistantMemory).where(
            AssistantMemory.assistant_id == assistant_id,
            AssistantMemory.key == key,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return memory


@router.put("/{key}", response_model=MemoryOut)
async def update_memory(
    assistant_id: uuid.UUID,
    key: str,
    body: MemoryUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> AssistantMemory:
    await _get_owned_assistant(assistant_id, current_user, session)
    result = await session.execute(
        select(AssistantMemory).where(
            AssistantMemory.assistant_id == assistant_id,
            AssistantMemory.key == key,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    memory.value = body.value
    return memory


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    assistant_id: uuid.UUID,
    key: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> None:
    await _get_owned_assistant(assistant_id, current_user, session)
    result = await session.execute(
        select(AssistantMemory).where(
            AssistantMemory.assistant_id == assistant_id,
            AssistantMemory.key == key,
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    await session.delete(memory)
