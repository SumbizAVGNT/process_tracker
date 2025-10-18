# src/process_tracker/db/dal/user_repo.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import User

class UserRepo(BaseRepo):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        async with self._guard():
            res = await self._await_timeout(
                self.session.execute(select(User).where(User.email == email))
            )
            return res.scalars().first()

    async def create(self, email: str, password_hash: str) -> User:
        async with self._guard():
            user = User(email=email, password_hash=password_hash)
            self.session.add(user)
            await self._await_timeout(self.session.flush())
            return user
