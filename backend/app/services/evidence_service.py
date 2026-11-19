import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import EvidenceCollectionMethod, EvidenceStatus
from app.models.evidence import ControlEvidence, Evidence
from app.schemas.evidence import (
    EvidenceApproveRequest,
    EvidenceQueryParams,
    EvidenceSummary,
    EvidenceUpdateRequest,
    EvidenceUploadRequest,
)
from app.services.storage.base import StorageBackend

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/gif",
    "text/plain",
    "text/csv",
    "text/markdown",
    "application/json",
    "application/xml",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-excel",
    "application/zip",
}

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".ps1", ".dll", ".so",
    ".msi", ".com", ".scr", ".vbs", ".js", ".wsf", ".pif",
}


class EvidenceService:
    def __init__(self, db: AsyncSession, storage: StorageBackend) -> None:
        self.db = db
        self.storage = storage

    async def upload_evidence(
        self,
        tenant_id: UUID,
        file: UploadFile,
        metadata: EvidenceUploadRequest,
        uploaded_by: UUID,
    ) -> Evidence:
        file_name = file.filename or "unnamed"
        content_type = file.content_type or "application/octet-stream"

        content = await file.read()
        file_size = len(content)

        self._validate_file(file_name, content_type, file_size)

        sha256_hash = hashlib.sha256(content).hexdigest()

        storage_path = await self.storage.upload(
            tenant_id=str(tenant_id),
            file_name=file_name,
            content=content,
            content_type=content_type,
        )

        evidence = Evidence(
            tenant_id=tenant_id,
            title=metadata.title,
            description=metadata.description,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            storage_path=storage_path,
            storage_backend=settings.EVIDENCE_STORAGE_BACKEND,
            sha256_hash=sha256_hash,
            version=1,
            status=EvidenceStatus.PENDING,
            uploaded_by=uploaded_by,
            collection_method=EvidenceCollectionMethod.MANUAL,
            source="manual_upload",
            tags=metadata.tags,
        )
        self.db.add(evidence)
        await self.db.flush()

        if metadata.control_ids:
            for control_id in metadata.control_ids:
                link = ControlEvidence(
                    tenant_id=tenant_id,
                    control_id=control_id,
                    evidence_id=evidence.id,
                )
                self.db.add(link)
            await self.db.flush()

        return evidence

    async def get_evidence(self, tenant_id: UUID, evidence_id: UUID) -> Evidence:
        result = await self.db.execute(
            select(Evidence).where(
                Evidence.id == evidence_id,
                Evidence.tenant_id == tenant_id,
            )
        )
        evidence = result.scalar_one_or_none()
        if evidence is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found",
            )
        return evidence

    async def list_evidence(
        self, tenant_id: UUID, params: EvidenceQueryParams
    ) -> tuple[list[Evidence], int]:
        base = select(Evidence).where(Evidence.tenant_id == tenant_id)

        if params.status is not None:
            base = base.where(Evidence.status == params.status)
        if params.search is not None:
            pattern = f"%{params.search}%"
            base = base.where(
                Evidence.title.ilike(pattern) | Evidence.file_name.ilike(pattern)
            )
        if params.uploaded_by is not None:
            base = base.where(Evidence.uploaded_by == params.uploaded_by)
        if params.since is not None:
            base = base.where(Evidence.created_at >= params.since)
        if params.until is not None:
            base = base.where(Evidence.created_at <= params.until)
        if params.control_id is not None:
            sub = (
                select(ControlEvidence.evidence_id)
                .where(
                    ControlEvidence.control_id == params.control_id,
                    ControlEvidence.tenant_id == tenant_id,
                )
            )
            base = base.where(Evidence.id.in_(sub))

        count_result = await self.db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        rows = await self.db.execute(
            base.order_by(Evidence.created_at.desc())
            .limit(params.limit)
            .offset(params.offset)
        )
        items = list(rows.scalars().all())
        return items, total

    async def update_evidence(
        self, tenant_id: UUID, evidence_id: UUID, data: EvidenceUpdateRequest
    ) -> Evidence:
        evidence = await self.get_evidence(tenant_id, evidence_id)
        if data.title is not None:
            evidence.title = data.title
        if data.description is not None:
            evidence.description = data.description
        if data.tags is not None:
            evidence.tags = data.tags
        await self.db.flush()
        return evidence

    async def approve_evidence(
        self,
        tenant_id: UUID,
        evidence_id: UUID,
        data: EvidenceApproveRequest,
        approved_by: UUID,
    ) -> Evidence:
        evidence = await self.get_evidence(tenant_id, evidence_id)

        if data.approved:
            evidence.status = EvidenceStatus.APPROVED
        else:
            evidence.status = EvidenceStatus.REJECTED

        evidence.approved_by = approved_by
        evidence.approved_at = datetime.now(timezone.utc)
        await self.db.flush()
        return evidence

    async def download_evidence(
        self, tenant_id: UUID, evidence_id: UUID
    ) -> tuple[bytes, Evidence]:
        evidence = await self.get_evidence(tenant_id, evidence_id)
        content = await self.storage.download(evidence.storage_path)
        return content, evidence

    async def delete_evidence(self, tenant_id: UUID, evidence_id: UUID) -> None:
        evidence = await self.get_evidence(tenant_id, evidence_id)
        await self.storage.delete(evidence.storage_path)
        await self.db.delete(evidence)
        await self.db.flush()

    async def get_evidence_summary(self, tenant_id: UUID) -> EvidenceSummary:
        base = select(Evidence).where(Evidence.tenant_id == tenant_id)

        count_result = await self.db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()

        status_q = await self.db.execute(
            select(Evidence.status, func.count())
            .where(Evidence.tenant_id == tenant_id)
            .group_by(Evidence.status)
        )
        by_status = {row[0].value: row[1] for row in status_q.all()}

        pending_q = await self.db.execute(
            select(func.count()).where(
                Evidence.tenant_id == tenant_id,
                Evidence.status == EvidenceStatus.PENDING,
            )
        )
        pending_approval = pending_q.scalar_one()

        threshold = datetime.now(timezone.utc) + timedelta(days=30)
        expiring_q = await self.db.execute(
            select(func.count()).where(
                Evidence.tenant_id == tenant_id,
                Evidence.expires_at.is_not(None),
                Evidence.expires_at <= threshold,
                Evidence.status != EvidenceStatus.EXPIRED,
            )
        )
        expiring_soon = expiring_q.scalar_one()

        size_q = await self.db.execute(
            select(func.coalesce(func.sum(Evidence.file_size), 0)).where(
                Evidence.tenant_id == tenant_id,
            )
        )
        total_size_bytes = size_q.scalar_one()

        return EvidenceSummary(
            total=total,
            by_status=by_status,
            pending_approval=pending_approval,
            expiring_soon=expiring_soon,
            total_size_bytes=total_size_bytes,
        )

    async def get_control_evidence(
        self, tenant_id: UUID, control_id: UUID
    ) -> list[Evidence]:
        result = await self.db.execute(
            select(Evidence)
            .join(ControlEvidence, ControlEvidence.evidence_id == Evidence.id)
            .where(
                ControlEvidence.control_id == control_id,
                ControlEvidence.tenant_id == tenant_id,
            )
            .order_by(Evidence.created_at.desc())
        )
        return list(result.scalars().all())

    def _validate_file(self, filename: str, content_type: str, size: int) -> None:
        max_bytes = settings.EVIDENCE_MAX_UPLOAD_MB * 1024 * 1024
        if size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum size of {settings.EVIDENCE_MAX_UPLOAD_MB} MB",
            )

        ext = PurePosixPath(filename).suffix.lower()
        if ext in BLOCKED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not allowed",
            )

        if content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content type '{content_type}' is not allowed",
            )
