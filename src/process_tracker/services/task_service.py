# src/process_tracker/services/task_service.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from ..db.dal.task_repo import TaskRepo
from ..core.events import events

class TaskService:
    def __init__(self, session: AsyncSession):
        self.repo = TaskRepo(session)
        self.session = session

    async def list(self):
        return await self.repo.list()

    async def create(self, title: str):
        task = await self.repo.create(title)
        await self.session.commit()
        await events.publish({"type": "task_created", "id": task.id, "title": task.title})
        return task

    async def set_done(self, task_id: int, done: bool):
        changed = await self.repo.set_done(task_id, done)
        await self.session.commit()
        if changed:
            await events.publish({"type": "task_updated", "id": task_id, "done": done})
        return changed

    async def remove(self, task_id: int):
        removed = await self.repo.remove(task_id)
        await self.session.commit()
        if removed:
            await events.publish({"type": "task_deleted", "id": task_id})
        return removed
