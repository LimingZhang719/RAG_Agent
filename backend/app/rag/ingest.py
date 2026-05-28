from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from llama_index.core import Document as LlamaDocument
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import Document, DocumentBlock, Chunk
from app.db.models.enums import BlockType, DocumentStatus
from app.db.models.knowledge_base import KnowledgeBase
from app.rag.embedding_client import build_embedding_client
from app.storage.minio_client import MinioStorage, parse_minio_uri


@dataclass
class IngestResult:
    blocks: int
    chunks: int


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def ingest_document_sync(session: Session, document_id: UUID) -> IngestResult:
    document = session.get(Document, document_id)
    if document is None:
        raise ValueError("Document not found")

    kb = session.get(KnowledgeBase, document.kb_id)
    if kb is None:
        raise ValueError("Knowledge base not found")

    document.status = DocumentStatus.parsing
    document.error_message = None
    session.commit()

    storage = MinioStorage()
    _, object_name = parse_minio_uri(document.file_uri)

    with tempfile.TemporaryDirectory() as temp_dir:
        local_path = os.path.join(temp_dir, document.file_name)
        storage.download_to_file(object_name, local_path)

        reader = SimpleDirectoryReader(input_files=[local_path])
        documents: list[LlamaDocument] = reader.load_data()

        document.status = DocumentStatus.chunking
        session.commit()

        splitter = SentenceSplitter(
            chunk_size=settings.ingest_chunk_size,
            chunk_overlap=settings.ingest_chunk_overlap,
        )
        nodes = splitter.get_nodes_from_documents(documents)

        document.status = DocumentStatus.embedding
        session.commit()

        embed_model = build_embedding_client()
        texts = [node.get_content(metadata_mode="none") for node in nodes]
        batch_size = min(settings.ingest_batch_size, 10)
        embeddings = embed_model.get_text_embedding_batch(
            texts, batch_size=batch_size
        )

        session.query(DocumentBlock).filter(
            DocumentBlock.document_id == document.id
        ).delete()
        session.query(Chunk).filter(Chunk.document_id == document.id).delete()

        blocks_count = 0
        chunks_count = 0

        for idx, (node, embedding) in enumerate(zip(nodes, embeddings), start=1):
            content = texts[idx - 1]
            metadata = node.metadata or {}
            page_no = _safe_int(metadata.get("page_label") or metadata.get("page_number"))
            section_path = metadata.get("section") or metadata.get("heading")

            block = DocumentBlock(
                document_id=document.id,
                block_type=BlockType.text,
                content=content,
                page_no=page_no,
                block_order=idx,
                metadata_=metadata,
            )
            session.add(block)
            blocks_count += 1

            chunk = Chunk(
                kb_id=kb.id,
                document_id=document.id,
                content=content,
                content_hash=_hash_content(content),
                embedding=embedding,
                page_no=page_no,
                block_order=idx,
                section_path=section_path,
                visibility_scope=kb.visibility_scope,
                org_id=kb.org_id,
                owner_id=kb.owner_id,
            )
            session.add(chunk)
            chunks_count += 1

        document.status = DocumentStatus.ready
        session.commit()

    return IngestResult(blocks=blocks_count, chunks=chunks_count)
