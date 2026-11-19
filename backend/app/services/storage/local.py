import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

import aiofiles
import aiofiles.os

from app.services.storage.base import StorageBackend

_UNSAFE_CHARS = re.compile(r"[\x00-\x1f\x7f\"<>:|?*]")
_MAX_NAME_LENGTH = 200


def safe_filename(file_name: str) -> str:
    """Reduce a client-supplied filename to a single safe path component.

    Strips any directory parts (POSIX or Windows separators), control and
    reserved characters, and leading dots, so the result can never traverse.
    """
    base = re.split(r"[\\/]", file_name)[-1]
    base = _UNSAFE_CHARS.sub("_", base).lstrip(". ").strip()
    return base[:_MAX_NAME_LENGTH] or "unnamed"


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)

    def _contained(self, relative: str | Path) -> Path:
        """Resolve a storage path and refuse anything outside the store root."""
        root = self.base_path.resolve()
        full = (root / relative).resolve()
        if not full.is_relative_to(root) or full == root:
            raise ValueError("Storage path escapes the evidence store")
        return full

    async def upload(
        self,
        tenant_id: str,
        file_name: str,
        content: bytes,
        content_type: str,  # noqa: ARG002 - part of StorageBackend interface
    ) -> str:
        now = datetime.now(UTC)
        stored_name = f"{uuid.uuid4().hex}_{safe_filename(file_name)}"
        relative = Path(safe_filename(tenant_id)) / str(now.year) / f"{now.month:02d}" / stored_name
        full_path = self._contained(relative)

        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        return str(relative)

    async def download(self, storage_path: str) -> bytes:
        full_path = self._contained(storage_path)
        if not full_path.is_file():
            raise FileNotFoundError(f"Evidence file not found: {storage_path}")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, storage_path: str) -> None:
        full_path = self._contained(storage_path)
        if full_path.is_file():
            await aiofiles.os.remove(full_path)

    async def get_signed_url(
        self,
        storage_path: str,
        expires_in: int = 3600,  # noqa: ARG002 - local backend has no signing
    ) -> str:
        self._contained(storage_path)
        return f"/evidence-store/{storage_path}"
