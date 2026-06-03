from __future__ import annotations

from typing import Any


class OCRClient:
    async def extract(self, file_uri: str, file_type: str) -> dict[str, Any]:
        raise NotImplementedError


class DefaultOCRClient(OCRClient):
    async def extract(self, file_uri: str, file_type: str) -> dict[str, Any]:
        lower_uri = file_uri.lower()
        lower_type = file_type.lower()
        if "invoice" in lower_uri or "发票" in lower_uri:
            doc_type = "invoice"
        elif "payment" in lower_uri or "水单" in lower_uri or "支付" in lower_uri:
            doc_type = "payment"
        elif "approval" in lower_uri or "审批" in lower_uri:
            doc_type = "approval"
        else:
            doc_type = "other"

        return {
            "document_type": doc_type,
            "confidence": 0.65,
            "fields": {
                "invoice_title": "默认公司",
                "invoice_amount": None,
                "invoice_date": None,
                "source_file_type": lower_type,
            },
            "raw_text": "OCR provider is not configured. Default OCR returned placeholder fields.",
            "raw": {},
        }


def build_ocr_client() -> OCRClient:
    return DefaultOCRClient()
