from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter, TokenTextSplitter
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import Chunk, Document, DocumentBlock
from app.db.models.enums import BlockType, ChunkMethod, DocumentStatus
from app.db.models.knowledge_base import KnowledgeBase
from app.rag.document_readers import load_documents
from app.rag.embedding_client import build_embedding_client
from app.rag.text_cleaning import normalize_extracted_text_with_stats
from app.storage.minio_client import MinioStorage, parse_minio_uri

logger = logging.getLogger(__name__)


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


def _clean_documents(documents: list[LlamaDocument]) -> list[LlamaDocument]:
    cleaned_documents: list[LlamaDocument] = []
    for document in documents:
        text = document.get_content(metadata_mode="none")
        cleaned_text, stats = normalize_extracted_text_with_stats(text)
        if stats.removed_control_chars or stats.repaired_spacing:
            logger.info(
                "Cleaned extracted document text: removed_control_chars=%s, "
                "repaired_spacing=%s, original_length=%s, cleaned_length=%s",
                stats.removed_control_chars,
                stats.repaired_spacing,
                stats.original_length,
                stats.cleaned_length,
            )
        if not cleaned_text:
            continue
        cleaned_documents.append(
            LlamaDocument(text=cleaned_text, metadata=document.metadata or {})
        )
    return cleaned_documents


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

        documents = _clean_documents(load_documents(local_path, document.file_type))
        if not documents:
            raise ValueError("No extractable text found in document")

        document.status = DocumentStatus.chunking
        session.commit()

        chunk_method = document.chunk_method or kb.chunk_method
        chunk_size = document.chunk_size or kb.chunk_size
        chunk_overlap = document.chunk_overlap or kb.chunk_overlap

        if chunk_method == ChunkMethod.sentence:
            splitter = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        elif chunk_method == ChunkMethod.token:
            splitter = TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        else:
            raise ValueError("Unsupported chunk method")
        nodes = splitter.get_nodes_from_documents(documents)

        document.status = DocumentStatus.embedding
        session.commit()

        embed_model = build_embedding_client()
        cleaned_nodes = []
        texts = []
        for node in nodes:
            content, stats = normalize_extracted_text_with_stats(
                node.get_content(metadata_mode="none")
            )
            if stats.removed_control_chars or stats.repaired_spacing:
                logger.info(
                    "Cleaned chunk text: removed_control_chars=%s, "
                    "repaired_spacing=%s, original_length=%s, cleaned_length=%s",
                    stats.removed_control_chars,
                    stats.repaired_spacing,
                    stats.original_length,
                    stats.cleaned_length,
                )
            if not content:
                continue
            cleaned_nodes.append(node)
            texts.append(content)
        if not texts:
            raise ValueError("No valid chunks found after text cleaning")

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

        for idx, (node, embedding) in enumerate(
            zip(cleaned_nodes, embeddings, strict=True), start=1
        ):
            content = texts[idx - 1]
            metadata = node.metadata or {}
            page_no = _safe_int(
                metadata.get("page_label") or metadata.get("page_number")
            )
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
