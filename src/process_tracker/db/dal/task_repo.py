# src/process_tracker/db/dal/task_repo.py
from __future__ import annotations

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import Task

class TaskRepo(BaseRepo):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list(self) -> list[Task]:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(select(Task).order_by(Task.id.desc()))
            )
            return list(res.scalars().all())

    async def create(self, title: str) -> Task:
        async with self._guard():
            task = Task(title=title)
            self.session.add(task)
            await self._await_timeout(self.session.flush())
            return task

    async def set_done(self, task_id: int, done: bool) -> int:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(
                    update(Task).where(Task.id == task_id).values(done=done).returning(Task.id)
                )
            )
            row = res.first()
            return row[0] if row else 0

    async def remove(self, task_id: int) -> int:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(
                    delete(Task).where(Task.id == task_id).returning(Task.id)
                )
            )
            row = res.first()
            return row[0] if row else 0
