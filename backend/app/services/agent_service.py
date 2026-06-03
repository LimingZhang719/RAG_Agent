from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models.agent import AgentRun, AgentStep
from app.db.models.enums import AgentRunStatus, AgentStepStatus
from app.db.models.user import User
from app.services.expense_service import get_claim, submit_claim


def _now():
    return datetime.now(timezone.utc)


async def create_run(
    session: AsyncSession,
    user: User,
    agent_type: str,
    input_payload: dict[str, Any],
) -> AgentRun:
    run = AgentRun(
        user_id=user.id,
        agent_type=agent_type,
        status=AgentRunStatus.pending,
        input=input_payload,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def get_run(session: AsyncSession, run_id: UUID, user: User) -> AgentRun:
    result = await session.execute(select(AgentRun).where(AgentRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise AppError("Agent run not found", status_code=404)
    if run.user_id != user.id:
        raise AppError("Forbidden", status_code=403)
    return run


async def list_runs(session: AsyncSession, user: User) -> list[AgentRun]:
    result = await session.execute(
        select(AgentRun)
        .where(AgentRun.user_id == user.id)
        .order_by(AgentRun.created_at.desc())
    )
    return list(result.scalars().all())


async def list_steps(session: AsyncSession, run_id: UUID, user: User) -> list[AgentStep]:
    await get_run(session, run_id, user)
    result = await session.execute(
        select(AgentStep)
        .where(AgentStep.run_id == run_id)
        .order_by(AgentStep.created_at.asc())
    )
    return list(result.scalars().all())


async def cancel_run(session: AsyncSession, run_id: UUID, user: User) -> AgentRun:
    run = await get_run(session, run_id, user)
    run.status = AgentRunStatus.cancelled
    run.completed_at = _now()
    await session.commit()
    await session.refresh(run)
    return run


async def _record_step(
    session: AsyncSession,
    run: AgentRun,
    name: str,
    input_payload: dict[str, Any] | None,
    handler,
) -> AgentStep:
    step = AgentStep(
        run_id=run.id,
        step_name=name,
        status=AgentStepStatus.running,
        input=input_payload,
        started_at=_now(),
    )
    session.add(step)
    await session.flush()
    try:
        output = await handler()
        step.output = output
        step.status = AgentStepStatus.succeeded
    except Exception as exc:
        step.status = AgentStepStatus.failed
        step.error_message = str(exc)
        run.status = AgentRunStatus.failed
        run.error_message = str(exc)
        raise
    finally:
        step.completed_at = _now()
        await session.commit()
    return step


async def execute_run(session: AsyncSession, run_id: UUID, user: User) -> AgentRun:
    run = await get_run(session, run_id, user)
    if run.agent_type != "expense":
        raise AppError("Unsupported agent type", status_code=400)
    claim_id = (run.input or {}).get("claim_id")
    if not claim_id:
        raise AppError("claim_id is required", status_code=400)

    run.status = AgentRunStatus.running
    run.started_at = run.started_at or _now()
    await session.commit()

    try:
        await _record_step(
            session,
            run,
            "collect_materials",
            {"claim_id": claim_id},
            lambda: _collect_materials(session, UUID(claim_id), user),
        )
        await _record_step(
            session,
            run,
            "validate_and_submit",
            {"claim_id": claim_id},
            lambda: _validate_and_submit(session, UUID(claim_id), user),
        )
        refreshed = await get_claim(session, UUID(claim_id), user)
        run.output = {
            "claim_id": claim_id,
            "status": refreshed.status.value,
            "human_required": refreshed.status.value in {"need_supplement", "finance_review"},
            "next_action": refreshed.status.value,
            "audit_summary": refreshed.audit_summary,
        }
        run.status = AgentRunStatus.succeeded
        run.completed_at = _now()
        await session.commit()
        await session.refresh(run)
        return run
    except Exception:
        await session.refresh(run)
        return run


async def _collect_materials(
    session: AsyncSession,
    claim_id: UUID,
    user: User,
) -> dict[str, Any]:
    claim = await get_claim(session, claim_id, user)
    return {
        "attachments": [
            {"id": str(item.id), "type": item.attachment_type.value}
            for item in claim.attachments
        ]
    }


async def _validate_and_submit(
    session: AsyncSession,
    claim_id: UUID,
    user: User,
) -> dict[str, Any]:
    claim = await submit_claim(session, claim_id, user)
    return {
        "status": claim.status.value,
        "audit_summary": claim.audit_summary,
    }


def serialize_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"


async def run_events(
    session: AsyncSession,
    run_id: UUID,
    user: User,
) -> AsyncGenerator[str, None]:
    run = await get_run(session, run_id, user)
    yield serialize_event({"type": "run_started", "run_id": str(run.id)})
    steps = await list_steps(session, run_id, user)
    for step in steps:
        yield serialize_event(
            {
                "type": "step_completed",
                "run_id": str(run.id),
                "step_name": step.step_name,
                "payload": step.output,
            }
        )
    if run.output and run.output.get("human_required"):
        yield serialize_event(
            {
                "type": "human_required",
                "run_id": str(run.id),
                "payload": run.output,
            }
        )
    yield serialize_event({"type": "run_completed", "run_id": str(run.id), "payload": run.output})
