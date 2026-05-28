from __future__ import annotations

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models.document import Document
from app.db.models.enums import DocumentStatus
from app.rag.ingest import ingest_document_sync
from app.workers.celery_app import celery_app

engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


@celery_app.task(name="ingest_document")
def ingest_document_task(document_id: str) -> dict[str, int]:
    doc_uuid = uuid.UUID(document_id)
    with SessionLocal() as session:
        document = session.get(Document, doc_uuid)
        if document is None:
            raise ValueError("Document not found")

        try:
            result = ingest_document_sync(session, doc_uuid)
            return {"blocks": result.blocks, "chunks": result.chunks}
        except Exception as exc:
            document.status = DocumentStatus.failed
            document.error_message = str(exc)
            session.commit()
            raise
