from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_session
from app.schemas.agent import (
    AgentRunCreate,
    AgentRunResponse,
    AgentRunResume,
    AgentStepResponse,
)
from app.services.agent_service import (
    cancel_run,
    create_run,
    execute_run,
    get_run,
    list_runs,
    list_steps,
    run_events,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/runs", response_model=AgentRunResponse)
async def create_agent_run(
    payload: AgentRunCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> AgentRunResponse:
    run = await create_run(session, current_user, payload.agent_type, payload.input)
    run = await execute_run(session, run.id, current_user)
    return AgentRunResponse.model_validate(run)


@router.get("/runs", response_model=list[AgentRunResponse])
async def list_agent_runs(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[AgentRunResponse]:
    runs = await list_runs(session, current_user)
    return [AgentRunResponse.model_validate(item) for item in runs]


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> AgentRunResponse:
    run = await get_run(session, run_id, current_user)
    return AgentRunResponse.model_validate(run)


@router.get("/runs/{run_id}/steps", response_model=list[AgentStepResponse])
async def get_agent_steps(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[AgentStepResponse]:
    steps = await list_steps(session, run_id, current_user)
    return [AgentStepResponse.model_validate(item) for item in steps]


@router.post("/runs/{run_id}/resume", response_model=AgentRunResponse)
async def resume_agent_run(
    run_id: UUID,
    _payload: AgentRunResume,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> AgentRunResponse:
    run = await execute_run(session, run_id, current_user)
    return AgentRunResponse.model_validate(run)


@router.post("/runs/{run_id}/cancel", response_model=AgentRunResponse)
async def cancel_agent_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> AgentRunResponse:
    run = await cancel_run(session, run_id, current_user)
    return AgentRunResponse.model_validate(run)


@router.get("/runs/{run_id}/events")
async def get_agent_events(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    return StreamingResponse(
        run_events(session, run_id, current_user),
        media_type="text/event-stream",
    )
