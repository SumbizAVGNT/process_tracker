from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import Task


class TaskRepo(BaseRepo):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        async with self._guard():
            res = await self._await_timeout(self.session.execute(select(Task).where(Task.id == task_id)))
            return res.scalars().first()

    async def list(self) -> list[Task]:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(select(Task).order_by(Task.id.desc()))
            )
            return list(res.scalars().all())

    async def create(
        self,
        title: str,
        description: str | None = None,
        *,
        status: str = "open",
        process_id: int | None = None,
        type_id: int | None = None,
        assignee_id: int | None = None,
        fields: dict | None = None,
    ) -> Task:
        async with self._guard():
            item = Task(
                title=title,
                description=description,
                status=status,
                process_id=process_id,
                type_id=type_id,
                assignee_id=assignee_id,
                fields=fields or {},
            )
            self.session.add(item)
            await self._await_timeout(self.session.flush())
            return item

    async def update_status(self, task_id: int, status: str) -> int:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(
                    update(Task).where(Task.id == task_id).values(status=status).returning(Task.id)
                )
            )
            row = res.first()
            return int(row[0]) if row else 0

    async def update_assignee(self, task_id: int, assignee_id: int | None) -> int:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(
                    update(Task).where(Task.id == task_id).values(assignee_id=assignee_id).returning(Task.id)
                )
            )
            row = res.first()
            return int(row[0]) if row else 0

    async def update_fields(self, task_id: int, fields: dict, *, replace: bool = False) -> int:
        """
        Обновление произвольных полей задачи.
        replace=False → merge (поверх существующих), True → полная замена.
        """
        async with self._guard():
            if replace:
                values = {"fields": fields}
            else:
                # merge на стороне Python (без JSONB ops для кросс-диалектности)
                task = await self.get_by_id(task_id)
                if not task:
                    return 0
                merged = dict(task.fields or {})
                merged.update(fields or {})
                values = {"fields": merged}

            res = await self._await_timeout(
                self.session.execute(
                    update(Task).where(Task.id == task_id).values(**values).returning(Task.id)
                )
            )
            row = res.first()
            return int(row[0]) if row else 0

    async def remove(self, task_id: int) -> int:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(delete(Task).where(Task.id == task_id).returning(Task.id))
            )
            row = res.first()
            return int(row[0]) if row else 0
