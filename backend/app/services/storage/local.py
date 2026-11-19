import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
import aiofiles.os

from app.services.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)

    async def upload(
        self, tenant_id: str, file_name: str, content: bytes, content_type: str
    ) -> str:
        now = datetime.now(timezone.utc)
        safe_name = f"{uuid.uuid4().hex}_{file_name}"
        relative = Path(tenant_id) / str(now.year) / f"{now.month:02d}" / safe_name
        full_path = self.base_path / relative

        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        return str(relative)

    async def download(self, storage_path: str) -> bytes:
        full_path = self.base_path / storage_path
        if not full_path.exists():
            raise FileNotFoundError(f"Evidence file not found: {storage_path}")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, storage_path: str) -> None:
        full_path = self.base_path / storage_path
        if full_path.exists():
            await aiofiles.os.remove(full_path)

    async def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        return f"/evidence-store/{storage_path}"
