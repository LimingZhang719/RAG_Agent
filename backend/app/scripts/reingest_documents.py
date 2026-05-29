from __future__ import annotations

import argparse
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models.document import Document
from app.db.models.enums import DocumentStatus
from app.rag.ingest import ingest_document_sync


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid UUID: {value}") from exc


def _select_documents(
    session: Session,
    document_id: uuid.UUID | None,
    kb_id: uuid.UUID | None,
    limit: int | None,
) -> list[Document]:
    query = select(Document).order_by(Document.created_at.asc())
    if document_id is not None:
        query = query.where(Document.id == document_id)
    if kb_id is not None:
        query = query.where(Document.kb_id == kb_id)
    if limit is not None:
        query = query.limit(limit)
    return list(session.scalars(query).all())


def reingest_documents(
    document_id: uuid.UUID | None,
    kb_id: uuid.UUID | None,
    limit: int | None,
) -> int:
    engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
    session_maker = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    completed = 0

    with session_maker() as session:
        documents = _select_documents(session, document_id, kb_id, limit)
        for document in documents:
            try:
                result = ingest_document_sync(session, document.id)
                completed += 1
                print(
                    f"reingested document={document.id} "
                    f"blocks={result.blocks} chunks={result.chunks}"
                )
            except Exception as exc:
                refreshed = session.get(Document, document.id)
                if refreshed is not None:
                    refreshed.status = DocumentStatus.failed
                    refreshed.error_message = str(exc)
                    session.commit()
                print(f"failed document={document.id} error={exc}")

    engine.dispose()
    return completed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-parse, clean, chunk, and embed existing documents."
    )
    parser.add_argument("--doc-id", type=_parse_uuid, default=None)
    parser.add_argument("--kb-id", type=_parse_uuid, default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if args.doc_id is None and args.kb_id is None:
        parser.error("At least one of --doc-id or --kb-id is required.")

    completed = reingest_documents(args.doc_id, args.kb_id, args.limit)
    print(f"completed={completed}")


if __name__ == "__main__":
    main()
