from __future__ import annotations

import os
from collections.abc import Callable

import fitz
from llama_index.core import Document as LlamaDocument
from llama_index.core import SimpleDirectoryReader


def _load_with_simple_reader(local_path: str) -> list[LlamaDocument]:
    reader = SimpleDirectoryReader(input_files=[local_path])
    return list(reader.load_data())


def _is_pdf(local_path: str, file_type: str | None) -> bool:
    suffix = os.path.splitext(local_path)[1].lower()
    return suffix == ".pdf" or file_type == "application/pdf"


def _load_pdf_with_pymupdf(local_path: str) -> list[LlamaDocument]:
    pages: list[LlamaDocument] = []
    with fitz.open(local_path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            if not text.strip():
                continue
            pages.append(
                LlamaDocument(
                    text=text,
                    metadata={
                        "page_label": str(page_index),
                        "page_number": page_index,
                        "source": local_path,
                        "reader": "pymupdf",
                    },
                )
            )
    return pages


def load_documents(local_path: str, file_type: str | None) -> list[LlamaDocument]:
    reader: Callable[[str], list[LlamaDocument]]
    if _is_pdf(local_path, file_type):
        reader = _load_pdf_with_pymupdf
    else:
        reader = _load_with_simple_reader

    try:
        documents = reader(local_path)
    except Exception:
        if reader is _load_with_simple_reader:
            raise
        documents = _load_with_simple_reader(local_path)

    if not documents and reader is not _load_with_simple_reader:
        documents = _load_with_simple_reader(local_path)
    return documents
