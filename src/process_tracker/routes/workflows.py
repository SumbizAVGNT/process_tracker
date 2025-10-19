from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..services.workflow_service import WorkflowService
from ..core.workflow.models import WorkflowDefinition, Step

router = APIRouter(tags=["workflows"])


def _svc_dep() -> WorkflowService:
    # Пока — in-memory store по умолчанию; позже переведём на DI/DB
    return WorkflowService()


@router.get("/workflows", response_model=List[WorkflowDefinition])
async def list_workflows(svc: WorkflowService = Depends(_svc_dep)):
    return await svc.list_definitions()


@router.get("/workflows/{wf_id}", response_model=WorkflowDefinition)
async def get_workflow(wf_id: str, version: Optional[int] = None, svc: WorkflowService = Depends(_svc_dep)):
    try:
        return await svc.get_definition(wf_id, version)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workflow not found")


@router.post("/workflows/validate")
async def validate_workflow(body: WorkflowDefinition, svc: WorkflowService = Depends(_svc_dep)):
    await svc.engine.validate(body)
    return {"ok": True}


class NextStepsIn(BaseModel):
    wf_id: str = Field(..., description="ID процесса")
    current_step_id: str = Field(..., description="Текущий шаг")
    context: Dict[str, Any] = Field(default_factory=dict)
    roles: List[str] = Field(default_factory=list)
    perms: List[str] = Field(default_factory=list)


class NextStepsOut(BaseModel):
    steps: List[Step]


@router.post("/workflows/next-steps", response_model=NextStepsOut)
async def calc_next_steps(body: NextStepsIn, svc: WorkflowService = Depends(_svc_dep)):
    try:
        steps = await svc.next_steps(
            wf_id=body.wf_id,
            current_step_id=body.current_step_id,
            context=body.context,
            user_roles=body.roles,
            user_perms=body.perms,
        )
        return NextStepsOut(steps=steps)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workflow not found")
