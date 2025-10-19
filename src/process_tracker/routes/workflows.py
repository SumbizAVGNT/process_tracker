from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..core.blueprints import (
    BlueprintDefinition,
    MemoryBlueprintStore,
    create_default_store,
    compile_to_workflow,
)
from ..core.workflow import WorkflowEngine, InMemoryWorkflowStore

router = APIRouter(prefix="/workflows", tags=["workflows"])

# in-memory store (можно заменить на БД-сервис)
_store: MemoryBlueprintStore = create_default_store()


class BlueprintIn(BaseModel):
    key: str = Field(..., max_length=128)
    title: str
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    version: int = 1


class BlueprintOut(BlueprintIn):
    pass


@router.get("/blueprints", response_model=List[BlueprintOut])
async def list_blueprints():
    items = await _store.list_as_list()
    return [BlueprintOut(**bp.to_dict()) for bp in items]


@router.get("/blueprints/{key}", response_model=BlueprintOut)
async def get_blueprint(key: str):
    bp = await _store.get_definition(key)
    if not bp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="blueprint not found")
    return BlueprintOut(**bp.to_dict())


@router.post("/blueprints", response_model=BlueprintOut, status_code=status.HTTP_201_CREATED)
async def upsert_blueprint(body: BlueprintIn):
    bp = await _store.upsert_definition(
        key=body.key,
        title=body.title,
        nodes=body.nodes,
        edges=body.edges,
        version=body.version,
    )
    return BlueprintOut(**bp.to_dict())


class CompileOut(BaseModel):
    workflow: Dict[str, Any]


@router.post("/blueprints/{key}/compile", response_model=CompileOut)
async def compile_blueprint(key: str):
    bp = await _store.get_definition(key)
    if not bp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="blueprint not found")

    wf = compile_to_workflow(bp)
    engine = WorkflowEngine(InMemoryWorkflowStore([wf]))
    await engine.validate(wf)
    # pydantic-модель engine.wf сериализуем через model_dump()
    return CompileOut(workflow=wf.model_dump())
