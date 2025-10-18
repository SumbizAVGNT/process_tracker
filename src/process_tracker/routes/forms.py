from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..services.forms_service import FormsService
from ..core.forms.schemas import FormSchema

router = APIRouter(tags=["forms"])


def _svc_dep() -> FormsService:
    # пока используем in-memory сервис; дальше можно переключить на DI/BД
    return FormsService()


@router.get("/forms", response_model=List[FormSchema])
async def list_forms(svc: FormsService = Depends(_svc_dep)):
    return await svc.list_forms()


@router.get("/forms/{form_id}", response_model=FormSchema)
async def get_form(form_id: str, svc: FormsService = Depends(_svc_dep)):
    try:
        return await svc.get_form(form_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="form not found")


class ValidateIn(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)


class ValidateOut(BaseModel):
    ok: bool
    errors: Dict[str, List[str]] = Field(default_factory=dict)


@router.post("/forms/{form_id}/validate", response_model=ValidateOut)
async def validate_form(form_id: str, body: ValidateIn, svc: FormsService = Depends(_svc_dep)):
    try:
        ok, errors = await svc.validate(form_id, body.data or {})
        return ValidateOut(ok=ok, errors=errors)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="form not found")
