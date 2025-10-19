from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import AsyncSessionLocal
from ..db.models import FormDef

router = APIRouter(prefix="/forms", tags=["forms"])


# --- DI session --------------------------------------------------------------
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as s:
        yield s


# --- Schemas ----------------------------------------------------------------
class FormDefIn(BaseModel):
    key: str = Field(..., description="Уникальный код формы")
    title: str = Field(..., description="Название формы")
    schema: dict[str, Any] = Field(..., description="JSON-схема формы")
    meta: dict[str, Any] = Field(default_factory=dict)


class FormDefOut(BaseModel):
    key: str
    title: str
    schema: dict[str, Any]
    meta: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_orm_row(cls, row: FormDef) -> "FormDefOut":
        return cls(key=row.key, title=row.title, schema=row.schema or {}, meta=row.meta or {})


# --- Routes -----------------------------------------------------------------
@router.get("/defs", response_model=List[FormDefOut])
async def list_defs(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(FormDef).order_by(FormDef.id.desc()))
    items = list(res.scalars().all())
    return [FormDefOut.from_orm_row(x) for x in items]


@router.get("/defs/{key}", response_model=FormDefOut)
async def get_def(key: str, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(FormDef).where(FormDef.key == key))
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return FormDefOut.from_orm_row(item)


@router.post("/defs", response_model=FormDefOut, status_code=status.HTTP_201_CREATED)
async def create_def(payload: FormDefIn, session: AsyncSession = Depends(get_session)):
    # upsert по key
    res = await session.execute(select(FormDef).where(FormDef.key == payload.key))
    item = res.scalars().first()
    if item:
        item.title = payload.title
        item.schema = payload.schema
        item.meta = payload.meta or {}
        await session.commit()
        await session.refresh(item)
        return FormDefOut.from_orm_row(item)

    item = FormDef(key=payload.key, title=payload.title, schema=payload.schema, meta=payload.meta or {})
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return FormDefOut.from_orm_row(item)


@router.put("/defs/{key}", response_model=FormDefOut)
async def update_def(key: str, payload: FormDefIn, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(FormDef).where(FormDef.key == key))
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    item.key = payload.key  # разрешим переименовать
    item.title = payload.title
    item.schema = payload.schema
    item.meta = payload.meta or {}
    await session.commit()
    await session.refresh(item)
    return FormDefOut.from_orm_row(item)


@router.delete("/defs/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_def(key: str, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(FormDef).where(FormDef.key == key))
    item = res.scalars().first()
    if not item:
        return
    await session.delete(item)
    await session.commit()
