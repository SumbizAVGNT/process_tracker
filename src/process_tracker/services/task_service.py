from __future__ import annotations

from typing import Any, Optional

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
        await events.publish({"type": "task_created", "id": task.id, "title": getattr(task, "title", f"Task #{task.id}")})
        return task

    async def set_status(self, task_id: int, status: str) -> int:
        """
        Унифицированная смена статуса.
        Совместимость:
          - если в repo есть set_status(...) — используем его
          - иначе транслируем в set_done(...) (старый флаг)
        """
        changed_id: int = 0
        if hasattr(self.repo, "set_status"):
            changed_id = await getattr(self.repo, "set_status")(task_id, status)
        else:
            # Fallback к старому полю done
            normalized = (status or "").strip().lower()
            done = normalized in {"done", "closed", "resolved", "complete"}
            changed_id = await getattr(self.repo, "set_done")(task_id, done)  # type: ignore[misc]

        await self.session.commit()
        if changed_id:
            await events.publish({"type": "task_updated", "id": task_id, "status": status})
        return changed_id

    async def set_done(self, task_id: int, done: bool) -> int:
        """
        Обратная совместимость со старым API сервисов/репо.
        """
        return await self.set_status(task_id, "done" if done else "open")

    async def remove(self, task_id: int):
        removed = await self.repo.remove(task_id)
        await self.session.commit()
        if removed:
            await events.publish({"type": "task_deleted", "id": task_id})
        return removed
