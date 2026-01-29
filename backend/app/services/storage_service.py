"""Storage service for assets (local or S3-compatible)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from app.config import settings


class StorageError(Exception):
    pass


class StorageService:
    """Storage helper for asset uploads."""

    def __init__(self) -> None:
        self.backend = (settings.storage_backend or "local").lower()
        self.uploads_dir = Path(settings.uploads_dir or (Path(__file__).resolve().parents[2] / "uploads"))
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    async def save_bytes(
        self,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
    ) -> str:
        """Save bytes and return public URL."""
        if self.backend == "s3":
            return await self._save_s3(key, data, content_type)
        return self._save_local(key, data)

    async def delete(self, key: str) -> None:
        """Delete a stored object."""
        if self.backend == "s3":
            await self._delete_s3(key)
        else:
            self._delete_local(key)

    def public_url(self, key: str) -> str:
        """Get public URL for a key."""
        if self.backend == "s3":
            base = settings.storage_public_base_url
            if not base:
                raise StorageError("storage_public_base_url is required for S3 backend")
            return f"{base.rstrip('/')}/{key}"

        api_base = settings.api_url.rstrip("/")
        return f"{api_base}/uploads/{key}"

    def _save_local(self, key: str, data: bytes) -> str:
        target = self.uploads_dir / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return self.public_url(key)

    async def _save_s3(self, key: str, data: bytes, content_type: Optional[str]) -> str:
        try:
            import boto3
        except ImportError as exc:
            raise StorageError("boto3 is required for S3 backend") from exc

        client = boto3.client(
            "s3",
            region_name=settings.storage_region,
            endpoint_url=settings.storage_endpoint,
            aws_access_key_id=settings.storage_access_key_id,
            aws_secret_access_key=settings.storage_secret_access_key,
        )

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        bucket = settings.storage_bucket
        if not bucket:
            raise StorageError("storage_bucket is required for S3 backend")

        fileobj = io.BytesIO(data)
        client.upload_fileobj(fileobj, bucket, key, ExtraArgs=extra_args)
        return self.public_url(key)

    def _delete_local(self, key: str) -> None:
        target = self.uploads_dir / key
        if target.exists():
            target.unlink()

    async def _delete_s3(self, key: str) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise StorageError("boto3 is required for S3 backend") from exc

        bucket = settings.storage_bucket
        if not bucket:
            raise StorageError("storage_bucket is required for S3 backend")

        client = boto3.client(
            "s3",
            region_name=settings.storage_region,
            endpoint_url=settings.storage_endpoint,
            aws_access_key_id=settings.storage_access_key_id,
            aws_secret_access_key=settings.storage_secret_access_key,
        )
        client.delete_object(Bucket=bucket, Key=key)
