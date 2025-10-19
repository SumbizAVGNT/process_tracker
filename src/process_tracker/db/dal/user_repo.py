from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepo
from ..models import User


class UserRepo(BaseRepo):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        async with self._guard():
            res = await self._await_timeout(self.session.execute(select(User).where(User.id == user_id)))
            return res.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        async with self._guard():
            res = await self._await_timeout(self.session.execute(select(User).where(User.email == email)))
            return res.scalars().first()

    async def create(self, email: str, display_name: str | None = None, is_active: bool = True) -> User:
        """
        В нашей модели User НЕТ password_hash — авторизацию добавим отдельным модулем позже.
        """
        async with self._guard():
            user = User(email=email, display_name=display_name, is_active=is_active)
            self.session.add(user)
            await self._await_timeout(self.session.flush())
            return user
