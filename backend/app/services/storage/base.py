from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    async def upload(
        self, tenant_id: str, file_name: str, content: bytes, content_type: str
    ) -> str:
        """Upload file and return the storage path."""

    @abstractmethod
    async def download(self, storage_path: str) -> bytes:
        """Download file bytes by storage path."""

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Delete file from storage."""

    @abstractmethod
    async def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Return a temporary URL for downloading the file."""
