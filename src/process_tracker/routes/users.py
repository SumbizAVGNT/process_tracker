from __future__ import annotations
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# EmailStr → мягкая зависимость
try:
    from pydantic import EmailStr as _EmailStr  # type: ignore
    import email_validator as _ev  # noqa: F401
    EmailT = _EmailStr
except Exception:
    EmailT = str  # type: ignore[assignment]

router = APIRouter(tags=["users"])

# in-memory fallback (если нет БД-репозитория пользователей)
import itertools
_ids = itertools.count(1)
_STORE: dict[int, dict] = {}


class UserIn(BaseModel):
    email: EmailT
    name: Optional[str] = None
    is_active: bool = True
    roles: List[str] = Field(default_factory=list)
    perms: List[str] = Field(default_factory=list)


class UserPatch(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None
    perms: Optional[List[str]] = None


class UserOut(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    is_active: bool = True
    roles: List[str] = Field(default_factory=list)
    perms: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


@router.get("/users", response_model=List[UserOut])
async def list_users():
    return [UserOut.model_validate(v) for v in _STORE.values()]


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int):
    if user_id not in _STORE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return UserOut.model_validate(_STORE[user_id])


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserIn):
    uid = next(_ids)
    obj = body.model_dump()
    obj.update({"id": uid, "created_at": datetime.utcnow().isoformat()})
    _STORE[uid] = obj
    return UserOut.model_validate(obj)


@router.patch("/users/{user_id}", response_model=UserOut)
async def patch_user(user_id: int, body: UserPatch):
    if user_id not in _STORE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    for k, v in body.model_dump(exclude_none=True).items():
        _STORE[user_id][k] = v
    return UserOut.model_validate(_STORE[user_id])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    if _STORE.pop(user_id, None) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return
