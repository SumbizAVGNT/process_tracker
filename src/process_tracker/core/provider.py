"""
Простой DI/Service Provider для асинхронных сервисов.
— Единая точка выдачи AsyncSession
— Контекстные провайдеры для сервисов (TaskService, ProcessService)
— Универсальный провайдер `provide(factory)` для любых сервисов,
  где factory: (AsyncSession) -> Service
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import AsyncSessionLocal

S = TypeVar("S")  # тип сервиса


# ---------- Базовый провайдер сессии ----------

@asynccontextmanager
async def provide_session() -> AsyncIterator[AsyncSession]:
    """
    Выдаёт AsyncSession в контексте.
    Коммит/rollback — на уровне сервисов (явно).
    """
    async with AsyncSessionLocal() as session:
        yield session


# ---------- Универсальный провайдер сервиса ----------

@asynccontextmanager
async def provide(factory: Callable[[AsyncSession], S]) -> AsyncIterator[S]:
    """
    Универсальный DI-провайдер:
    ```
    async with provide(lambda s: MyService(s)) as svc:
        await svc.do()
    ```
    """
    async with provide_session() as session:
        yield factory(session)


# ---------- Конкретные провайдеры сервисов (ленивые импорты) ----------

@asynccontextmanager
async def provide_task_service():
    from ..services.task_service import TaskService  # lazy import
    async with provide(lambda s: TaskService(s)) as svc:
        yield svc


@asynccontextmanager
async def provide_process_service():
    from ..services.process_service import ProcessService  # lazy import
    async with provide(lambda s: ProcessService(s)) as svc:
        yield svc


# ---------- FastAPI dependency (для роутов) ----------

async def session_dependency() -> AsyncIterator[AsyncSession]:
    """
    Зависимость для FastAPI:
    ```
    @router.get("/items")
    async def handler(session: AsyncSession = Depends(session_dependency)):
        ...
    ```
    """
    async with AsyncSessionLocal() as session:
        yield session
