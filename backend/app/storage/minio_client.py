from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


@dataclass
class MinioObject:
    object_name: str
    file_uri: str
    size: int
    content_type: str | None


class MinioStorage:
    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        object_name: str,
        content_type: str | None,
    ) -> MinioObject:
        fileobj.seek(0, os.SEEK_END)
        size = fileobj.tell()
        fileobj.seek(0)
        self.client.put_object(
            self.bucket,
            object_name,
            fileobj,
            length=size,
            content_type=content_type,
        )
        file_uri = f"minio://{self.bucket}/{object_name}"
        return MinioObject(
            object_name=object_name,
            file_uri=file_uri,
            size=size,
            content_type=content_type,
        )

    def download_to_file(self, object_name: str, target_path: str) -> None:
        response = self.client.get_object(self.bucket, object_name)
        try:
            with open(target_path, "wb") as handle:
                for chunk in response.stream(1024 * 1024):
                    handle.write(chunk)
        finally:
            response.close()
            response.release_conn()

    def download_to_bytes(self, object_name: str) -> bytes:
        response = self.client.get_object(self.bucket, object_name)
        try:
            buffer = io.BytesIO()
            for chunk in response.stream(1024 * 1024):
                buffer.write(chunk)
            return buffer.getvalue()
        finally:
            response.close()
            response.release_conn()

    def remove_object(self, object_name: str) -> None:
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                return
            raise


def parse_minio_uri(file_uri: str) -> tuple[str, str]:
    if not file_uri.startswith("minio://"):
        raise ValueError("Invalid MinIO uri")
    bucket, object_name = file_uri.replace("minio://", "", 1).split("/", 1)
    return bucket, object_name
