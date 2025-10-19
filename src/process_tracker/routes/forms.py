from __future__ import annotations

from typing import Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import AsyncSessionLocal
from ..db.models import FormDef  # <-- напрямую из models, не из models_meta

router = APIRouter(prefix="/forms", tags=["forms"])


# --- DI session --------------------------------------------------------------
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as s:
        yield s


# --- Schemas ----------------------------------------------------------------
class FormDefIn(BaseModel):
    """
    Входная модель. Поле 'schema' конфликтует с зарезервированным именем в pydantic,
    поэтому используем form_schema + алиасы для JSON.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        # Разрешаем имя 'schema' через алиасы
    )
    slug: str = Field(..., description="Уникальный код формы")
    title: str = Field(..., description="Название формы")
    form_schema: dict[str, Any] = Field(
        ...,
        alias="schema",
        description="JSON-схема формы",
    )


class FormDefOut(BaseModel):
    slug: str
    title: str
    schema: dict[str, Any]

    @classmethod
    def from_orm_row(cls, row: FormDef) -> "FormDefOut":
        return cls(slug=row.slug, title=row.title, schema=row.schema or {})


# --- Routes -----------------------------------------------------------------
@router.get("/defs", response_model=List[FormDefOut])
async def list_defs(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(FormDef).order_by(FormDef.id.desc()))
    items = list(res.scalars().all())
    return [FormDefOut.from_orm_row(x) for x in items]


@router.get("/defs/{slug}", response_model=FormDefOut)
async def get_def(slug: str, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(FormDef).where(FormDef.slug == slug))
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return FormDefOut.from_orm_row(item)


@router.post("/defs", response_model=FormDefOut, status_code=status.HTTP_201_CREATED)
async def create_def(payload: FormDefIn, session: AsyncSession = Depends(get_session)):
    # upsert по slug
    res = await session.execute(select(FormDef).where(FormDef.slug == payload.slug))
    item = res.scalars().first()
    if item:
        # обновим
        item.title = payload.title
        item.schema = payload.form_schema
        await session.flush()
        return FormDefOut.from_orm_row(item)

    item = FormDef(slug=payload.slug, title=payload.title, schema=payload.form_schema)
    session.add(item)
    await session.flush()
    return FormDefOut.from_orm_row(item)


@router.put("/defs/{slug}", response_model=FormDefOut)
async def update_def(slug: str, payload: FormDefIn, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(FormDef).where(FormDef.slug == slug))
    item = res.scalars().first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    item.slug = payload.slug  # разрешим переименовать
    item.title = payload.title
    item.schema = payload.form_schema
    await session.flush()
    return FormDefOut.from_orm_row(item)


@router.delete("/defs/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_def(slug: str, session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(FormDef).where(FormDef.slug == slug))
    item = res.scalars().first()
    if not item:
        # идемпотентно: 204 даже если уже нет
        return
    await session.delete(item)
    await session.flush()
