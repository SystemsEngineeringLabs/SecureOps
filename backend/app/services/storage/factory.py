from app.core.config import settings
from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorage


def get_storage_backend() -> StorageBackend:
    backend = settings.EVIDENCE_STORAGE_BACKEND
    if backend == "local":
        return LocalStorage(settings.EVIDENCE_STORAGE_PATH)
    if backend == "azure_blob":
        raise NotImplementedError("Azure Blob storage adapter not yet configured")
    if backend == "s3":
        raise NotImplementedError("S3 storage adapter not yet configured")
    raise ValueError(f"Unknown storage backend: {backend}")
