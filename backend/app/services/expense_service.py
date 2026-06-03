from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.db.models.enums import (
    AttachmentType,
    AuditResult,
    ExpenseApprovalAction,
    ExpenseStatus,
    RoleName,
)
from app.db.models.expense import (
    ExpenseApprovalLog,
    ExpenseAttachment,
    ExpenseAuditItem,
    ExpenseClaim,
    TravelExpenseStandard,
)
from app.db.models.user import User
from app.models_gateway.ocr_client import build_ocr_client
from app.schemas.expense import ExpenseClaimCreate, ExpenseClaimUpdate, TravelExpenseStandardCreate
from app.services.settings_service import (
    get_invoice_title,
    get_reimbursement_days,
    has_role,
    require_admin,
    require_finance,
)
from app.storage.minio_client import MinioStorage


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _can_view_claim(user: User, claim: ExpenseClaim) -> bool:
    return (
        claim.user_id == user.id
        or has_role(user, RoleName.admin)
        or has_role(user, RoleName.finance)
    )


def _claim_options():
    return (
        selectinload(ExpenseClaim.attachments),
        selectinload(ExpenseClaim.audit_items),
    )


async def get_claim(session: AsyncSession, claim_id: UUID, user: User) -> ExpenseClaim:
    result = await session.execute(
        select(ExpenseClaim).options(*_claim_options()).where(ExpenseClaim.id == claim_id)
    )
    claim = result.scalar_one_or_none()
    if claim is None:
        raise AppError("Expense claim not found", status_code=404)
    if not _can_view_claim(user, claim):
        raise AppError("Forbidden", status_code=403)
    return claim


async def list_claims(session: AsyncSession, user: User) -> list[ExpenseClaim]:
    stmt = select(ExpenseClaim).options(*_claim_options()).order_by(ExpenseClaim.created_at.desc())
    if not (has_role(user, RoleName.admin) or has_role(user, RoleName.finance)):
        stmt = stmt.where(ExpenseClaim.user_id == user.id)
    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def list_finance_tasks(session: AsyncSession, user: User) -> list[ExpenseClaim]:
    require_finance(user)
    result = await session.execute(
        select(ExpenseClaim)
        .options(*_claim_options())
        .where(ExpenseClaim.status != ExpenseStatus.draft)
        .order_by(ExpenseClaim.submitted_at.desc().nullslast())
    )
    return list(result.scalars().unique().all())


async def get_attachment_source(
    session: AsyncSession,
    claim_id: UUID,
    attachment_id: UUID,
    user: User,
) -> ExpenseAttachment:
    claim = await get_claim(session, claim_id, user)
    for attachment in claim.attachments:
        if attachment.id == attachment_id:
            return attachment
    raise AppError("Expense attachment not found", status_code=404)


async def create_claim(
    session: AsyncSession, user: User, payload: ExpenseClaimCreate
) -> ExpenseClaim:
    claim = ExpenseClaim(
        user_id=user.id,
        status=ExpenseStatus.draft,
        claim_no=f"EX-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
        expense_type="travel",
        title=payload.title,
        description=payload.description,
        total_amount=payload.total_amount,
        currency=payload.currency,
    )
    metadata = {"city_tier": payload.city_tier} if payload.city_tier else None
    claim.audit_summary = {"metadata": metadata} if metadata else None
    session.add(claim)
    await session.commit()
    return await get_claim(session, claim.id, user)


async def update_claim(
    session: AsyncSession,
    claim_id: UUID,
    user: User,
    payload: ExpenseClaimUpdate,
) -> ExpenseClaim:
    claim = await get_claim(session, claim_id, user)
    if claim.user_id != user.id and not has_role(user, RoleName.admin):
        raise AppError("Forbidden", status_code=403)
    if claim.status not in {ExpenseStatus.draft, ExpenseStatus.need_supplement}:
        raise AppError("Only draft or supplement claims can be edited", status_code=400)

    for field in ("title", "description", "total_amount", "currency"):
        value = getattr(payload, field)
        if value is not None:
            setattr(claim, field, value)
    if payload.city_tier is not None:
        summary = dict(claim.audit_summary or {})
        metadata = dict(summary.get("metadata") or {})
        metadata["city_tier"] = payload.city_tier
        summary["metadata"] = metadata
        claim.audit_summary = summary
    await session.commit()
    return await get_claim(session, claim_id, user)


def _attachment_type_from_ocr(value: str | None, fallback: AttachmentType) -> AttachmentType:
    try:
        return AttachmentType(value) if value else fallback
    except ValueError:
        return fallback


async def add_attachment(
    session: AsyncSession,
    claim_id: UUID,
    user: User,
    file: UploadFile,
    attachment_type: AttachmentType,
) -> ExpenseAttachment:
    claim = await get_claim(session, claim_id, user)
    if claim.user_id != user.id and not has_role(user, RoleName.admin):
        raise AppError("Forbidden", status_code=403)
    if file.filename is None:
        raise AppError("File name missing", status_code=400)

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    object_name = f"expense/{claim_id}/{uuid.uuid4().hex}_{file.filename}"
    uploaded = MinioStorage().upload_fileobj(file.file, object_name, file.content_type)
    ocr_result = await build_ocr_client().extract(uploaded.file_uri, file.content_type or "")
    fields = ocr_result.get("fields") or {}
    resolved_type = _attachment_type_from_ocr(
        ocr_result.get("document_type"),
        attachment_type,
    )
    attachment = ExpenseAttachment(
        claim_id=claim.id,
        file_uri=uploaded.file_uri,
        file_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        size=size,
        attachment_type=resolved_type,
        ocr_result=ocr_result,
        extracted_fields=fields,
        ocr_confidence=Decimal(str(ocr_result.get("confidence") or "0")),
        classification_source="auto",
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    return attachment


async def delete_attachment(
    session: AsyncSession, claim_id: UUID, attachment_id: UUID, user: User
) -> None:
    claim = await get_claim(session, claim_id, user)
    if claim.user_id != user.id and not has_role(user, RoleName.admin):
        raise AppError("Forbidden", status_code=403)
    await session.execute(
        delete(ExpenseAttachment).where(
            ExpenseAttachment.id == attachment_id,
            ExpenseAttachment.claim_id == claim.id,
        )
    )
    await session.commit()


async def _match_travel_standard(
    session: AsyncSession,
    claim: ExpenseClaim,
    user: User,
) -> TravelExpenseStandard | None:
    city_tier = ((claim.audit_summary or {}).get("metadata") or {}).get("city_tier")
    stmt = (
        select(TravelExpenseStandard)
        .where(TravelExpenseStandard.is_active.is_(True))
        .order_by(TravelExpenseStandard.org_id.desc().nullslast())
    )
    result = await session.execute(stmt)
    standards = list(result.scalars().all())
    for standard in standards:
        if standard.org_id and standard.org_id != user.org_id:
            continue
        if standard.city_tier and city_tier and standard.city_tier != city_tier:
            continue
        if standard.currency != claim.currency:
            continue
        return standard
    return None


async def run_audit(session: AsyncSession, claim: ExpenseClaim, user: User) -> dict:
    await session.execute(delete(ExpenseAuditItem).where(ExpenseAuditItem.claim_id == claim.id))
    attachment_types = {item.attachment_type for item in claim.attachments}
    audit_items: list[ExpenseAuditItem] = []

    required = {
        AttachmentType.invoice: "发票",
        AttachmentType.payment: "水单或支付凭证",
        AttachmentType.approval: "审批单",
    }
    missing = [label for type_, label in required.items() if type_ not in attachment_types]
    audit_items.append(
        ExpenseAuditItem(
            claim_id=claim.id,
            name="材料完整性校验",
            result=AuditResult.risk if missing else AuditResult.pass_,
            evidence="缺少：" + "、".join(missing) if missing else "发票、支付凭证和审批单均已上传",
        )
    )

    invoice_title = await get_invoice_title(session)
    invoice_fields = [
        item.extracted_fields or {}
        for item in claim.attachments
        if item.attachment_type == AttachmentType.invoice
    ]
    title_ok = any(fields.get("invoice_title") == invoice_title for fields in invoice_fields)
    audit_items.append(
        ExpenseAuditItem(
            claim_id=claim.id,
            name="发票抬头校验",
            result=AuditResult.pass_ if title_ok or not invoice_fields else AuditResult.attention,
            evidence=f"标准抬头：{invoice_title}",
        )
    )

    invoice_amounts = [
        Decimal(str(fields.get("invoice_amount")))
        for fields in invoice_fields
        if fields.get("invoice_amount") not in (None, "")
    ]
    amount_result = AuditResult.attention
    amount_evidence = "OCR 未识别到发票金额，需人工复核"
    if invoice_amounts and claim.total_amount is not None:
        total = sum(invoice_amounts, Decimal("0"))
        amount_result = AuditResult.pass_ if total == claim.total_amount else AuditResult.risk
        amount_evidence = f"发票合计 {total}，申报金额 {claim.total_amount}"
    audit_items.append(
        ExpenseAuditItem(
            claim_id=claim.id,
            name="发票金额校验",
            result=amount_result,
            evidence=amount_evidence,
        )
    )

    days = await get_reimbursement_days(session)
    audit_items.append(
        ExpenseAuditItem(
            claim_id=claim.id,
            name="日期范围校验",
            result=AuditResult.attention,
            evidence=f"当前配置为 {days} 天内可报销；OCR 未识别日期时需人工复核",
        )
    )

    standard = await _match_travel_standard(session, claim, user)
    limit_result = AuditResult.attention
    limit_evidence = "未配置差旅金额标准，需人工复核"
    if standard and standard.single_trip_limit is not None and claim.total_amount is not None:
        limit_result = (
            AuditResult.pass_
            if claim.total_amount <= standard.single_trip_limit
            else AuditResult.risk
        )
        limit_evidence = f"申报金额 {claim.total_amount}，单次限额 {standard.single_trip_limit}"
    audit_items.append(
        ExpenseAuditItem(
            claim_id=claim.id,
            name="差旅金额标准校验",
            result=limit_result,
            evidence=limit_evidence,
        )
    )

    session.add_all(audit_items)
    await session.flush()

    result_values = [item.result for item in audit_items]
    if AuditResult.risk in result_values:
        level = "risk"
        next_action = "supplement" if missing else "submit_to_finance"
    elif AuditResult.attention in result_values:
        level = "attention"
        next_action = "submit_to_finance"
    else:
        level = "pass"
        next_action = "submit_to_finance"

    summary = {
        "level": level,
        "summary": "存在需关注或复核项目" if level != "pass" else "材料和规则校验通过，可提交财务复核",
        "missing_materials": missing,
        "audit_items": [
            {"name": item.name, "result": item.result.value, "evidence": item.evidence}
            for item in audit_items
        ],
        "next_action": next_action,
        "metadata": (claim.audit_summary or {}).get("metadata") or {},
    }
    claim.audit_summary = summary
    await session.commit()
    return summary


def _snapshot_claim(claim: ExpenseClaim) -> dict:
    return {
        "id": str(claim.id),
        "claim_no": claim.claim_no,
        "status": claim.status.value,
        "total_amount": str(claim.total_amount) if claim.total_amount is not None else None,
        "audit_summary": claim.audit_summary,
    }


async def add_approval_log(
    session: AsyncSession,
    claim: ExpenseClaim,
    actor: User,
    action: ExpenseApprovalAction,
    from_status: ExpenseStatus | str | None,
    to_status: ExpenseStatus | str | None,
    comment: str | None = None,
) -> None:
    session.add(
        ExpenseApprovalLog(
            claim_id=claim.id,
            actor_id=actor.id,
            action=action,
            from_status=from_status.value if isinstance(from_status, ExpenseStatus) else from_status,
            to_status=to_status.value if isinstance(to_status, ExpenseStatus) else to_status,
            comment=comment,
            snapshot=_snapshot_claim(claim),
        )
    )


async def submit_claim(session: AsyncSession, claim_id: UUID, user: User) -> ExpenseClaim:
    claim = await get_claim(session, claim_id, user)
    if claim.user_id != user.id:
        raise AppError("Forbidden", status_code=403)
    if claim.status not in {ExpenseStatus.draft, ExpenseStatus.need_supplement}:
        raise AppError("Claim cannot be submitted in current status", status_code=400)
    action = (
        ExpenseApprovalAction.resubmit
        if claim.status == ExpenseStatus.need_supplement
        else ExpenseApprovalAction.submit
    )
    old_status = claim.status
    summary = await run_audit(session, claim, user)
    claim = await get_claim(session, claim_id, user)
    claim.status = (
        ExpenseStatus.need_supplement
        if summary["missing_materials"]
        else ExpenseStatus.finance_review
    )
    claim.submitted_at = _now()
    await add_approval_log(session, claim, user, action, old_status, claim.status)
    await session.commit()
    return await get_claim(session, claim_id, user)


async def review_claim(
    session: AsyncSession,
    claim_id: UUID,
    user: User,
    action: ExpenseApprovalAction,
    comment: str | None,
) -> ExpenseClaim:
    require_finance(user)
    claim = await get_claim(session, claim_id, user)
    if claim.status != ExpenseStatus.finance_review:
        raise AppError("Claim is not in finance review", status_code=400)
    old_status = claim.status
    if action == ExpenseApprovalAction.approve:
        claim.status = ExpenseStatus.approved
        claim.approved_at = _now()
    elif action == ExpenseApprovalAction.reject:
        claim.status = ExpenseStatus.rejected
    elif action == ExpenseApprovalAction.request_supplement:
        claim.status = ExpenseStatus.need_supplement
    else:
        raise AppError("Unsupported review action", status_code=400)
    claim.reviewer_id = user.id
    claim.reviewed_at = _now()
    claim.review_comment = comment
    await add_approval_log(session, claim, user, action, old_status, claim.status, comment)
    await session.commit()
    return await get_claim(session, claim_id, user)


async def list_approval_logs(
    session: AsyncSession, claim_id: UUID, user: User
) -> list[ExpenseApprovalLog]:
    await get_claim(session, claim_id, user)
    result = await session.execute(
        select(ExpenseApprovalLog)
        .where(ExpenseApprovalLog.claim_id == claim_id)
        .order_by(ExpenseApprovalLog.created_at.asc())
    )
    return list(result.scalars().all())


async def create_travel_standard(
    session: AsyncSession,
    payload: TravelExpenseStandardCreate,
    user: User,
) -> TravelExpenseStandard:
    require_admin(user)
    standard = TravelExpenseStandard(
        name=payload.name,
        org_id=payload.org_id,
        city_tier=payload.city_tier,
        daily_limit=payload.daily_limit,
        single_trip_limit=payload.single_trip_limit,
        currency=payload.currency,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        is_active=payload.is_active,
        metadata_=payload.metadata,
    )
    session.add(standard)
    await session.commit()
    await session.refresh(standard)
    return standard


async def list_travel_standards(session: AsyncSession) -> list[TravelExpenseStandard]:
    result = await session.execute(
        select(TravelExpenseStandard).order_by(TravelExpenseStandard.created_at.desc())
    )
    return list(result.scalars().all())
