from __future__ import annotations

from uuid import UUID

from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.models.enums import AttachmentType, ExpenseApprovalAction
from app.db.session import get_session
from app.schemas.expense import (
    ExpenseApprovalLogResponse,
    ExpenseAttachmentResponse,
    ExpenseClaimCreate,
    ExpenseClaimResponse,
    ExpenseClaimUpdate,
    ExpenseReviewAction,
    TravelExpenseStandardCreate,
    TravelExpenseStandardResponse,
)
from app.services.expense_service import (
    add_attachment,
    create_claim,
    create_travel_standard,
    delete_attachment,
    get_attachment_source,
    get_claim,
    list_approval_logs,
    list_claims,
    list_finance_tasks,
    list_travel_standards,
    review_claim,
    submit_claim,
    update_claim,
)
from app.storage.minio_client import MinioStorage, parse_minio_uri

router = APIRouter(prefix="/expense", tags=["expense"])


@router.post("/claims", response_model=ExpenseClaimResponse)
async def create_expense_claim(
    payload: ExpenseClaimCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseClaimResponse:
    claim = await create_claim(session, current_user, payload)
    return ExpenseClaimResponse.model_validate(claim)


@router.get("/claims", response_model=list[ExpenseClaimResponse])
async def list_expense_claims(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[ExpenseClaimResponse]:
    claims = await list_claims(session, current_user)
    return [ExpenseClaimResponse.model_validate(item) for item in claims]


@router.get("/claims/{claim_id}", response_model=ExpenseClaimResponse)
async def get_expense_claim(
    claim_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseClaimResponse:
    claim = await get_claim(session, claim_id, current_user)
    return ExpenseClaimResponse.model_validate(claim)


@router.patch("/claims/{claim_id}", response_model=ExpenseClaimResponse)
async def update_expense_claim(
    claim_id: UUID,
    payload: ExpenseClaimUpdate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseClaimResponse:
    claim = await update_claim(session, claim_id, current_user, payload)
    return ExpenseClaimResponse.model_validate(claim)


@router.post("/claims/{claim_id}/attachments", response_model=ExpenseAttachmentResponse)
async def upload_expense_attachment(
    claim_id: UUID,
    attachment_type: AttachmentType = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseAttachmentResponse:
    attachment = await add_attachment(session, claim_id, current_user, file, attachment_type)
    return ExpenseAttachmentResponse.model_validate(attachment)


@router.delete("/claims/{claim_id}/attachments/{attachment_id}")
async def delete_expense_attachment(
    claim_id: UUID,
    attachment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    await delete_attachment(session, claim_id, attachment_id, current_user)
    return {"status": "ok"}


@router.get("/claims/{claim_id}/attachments/{attachment_id}/source")
async def get_expense_attachment_source(
    claim_id: UUID,
    attachment_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> Response:
    attachment = await get_attachment_source(
        session,
        claim_id,
        attachment_id,
        current_user,
    )
    _bucket, object_name = parse_minio_uri(attachment.file_uri)
    content = MinioStorage().download_to_bytes(object_name)
    filename = quote(attachment.file_name)
    return Response(
        content=content,
        media_type=attachment.file_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{filename}",
            "Cache-Control": "private, max-age=300",
        },
    )


@router.post("/claims/{claim_id}/submit", response_model=ExpenseClaimResponse)
async def submit_expense_claim(
    claim_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseClaimResponse:
    claim = await submit_claim(session, claim_id, current_user)
    return ExpenseClaimResponse.model_validate(claim)


@router.post("/claims/{claim_id}/run-agent", response_model=ExpenseClaimResponse)
async def run_expense_agent(
    claim_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseClaimResponse:
    claim = await submit_claim(session, claim_id, current_user)
    return ExpenseClaimResponse.model_validate(claim)


@router.get("/claims/{claim_id}/approval-logs", response_model=list[ExpenseApprovalLogResponse])
async def get_expense_approval_logs(
    claim_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[ExpenseApprovalLogResponse]:
    logs = await list_approval_logs(session, claim_id, current_user)
    return [ExpenseApprovalLogResponse.model_validate(item) for item in logs]


@router.get("/finance/tasks", response_model=list[ExpenseClaimResponse])
async def get_finance_tasks(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[ExpenseClaimResponse]:
    claims = await list_finance_tasks(session, current_user)
    return [ExpenseClaimResponse.model_validate(item) for item in claims]


@router.get("/finance/tasks/{claim_id}", response_model=ExpenseClaimResponse)
async def get_finance_task(
    claim_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseClaimResponse:
    claim = await get_claim(session, claim_id, current_user)
    return ExpenseClaimResponse.model_validate(claim)


@router.post("/finance/tasks/{claim_id}/approve", response_model=ExpenseClaimResponse)
async def approve_finance_task(
    claim_id: UUID,
    payload: ExpenseReviewAction,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseClaimResponse:
    claim = await review_claim(
        session, claim_id, current_user, ExpenseApprovalAction.approve, payload.comment
    )
    return ExpenseClaimResponse.model_validate(claim)


@router.post("/finance/tasks/{claim_id}/reject", response_model=ExpenseClaimResponse)
async def reject_finance_task(
    claim_id: UUID,
    payload: ExpenseReviewAction,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseClaimResponse:
    claim = await review_claim(
        session, claim_id, current_user, ExpenseApprovalAction.reject, payload.comment
    )
    return ExpenseClaimResponse.model_validate(claim)


@router.post("/finance/tasks/{claim_id}/request-supplement", response_model=ExpenseClaimResponse)
async def request_supplement_finance_task(
    claim_id: UUID,
    payload: ExpenseReviewAction,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> ExpenseClaimResponse:
    claim = await review_claim(
        session,
        claim_id,
        current_user,
        ExpenseApprovalAction.request_supplement,
        payload.comment,
    )
    return ExpenseClaimResponse.model_validate(claim)


@router.get("/travel-standards", response_model=list[TravelExpenseStandardResponse])
async def get_travel_standards(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> list[TravelExpenseStandardResponse]:
    _ = current_user
    standards = await list_travel_standards(session)
    return [TravelExpenseStandardResponse.model_validate(item) for item in standards]


@router.post("/travel-standards", response_model=TravelExpenseStandardResponse)
async def create_expense_travel_standard(
    payload: TravelExpenseStandardCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
) -> TravelExpenseStandardResponse:
    standard = await create_travel_standard(session, payload, current_user)
    return TravelExpenseStandardResponse.model_validate(standard)
