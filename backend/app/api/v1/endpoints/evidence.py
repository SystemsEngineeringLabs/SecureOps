import uuid

from fastapi import APIRouter, Depends, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_permission
from app.core.permissions import Action, Resource
from app.db.tenant_session import get_tenant_db
from app.models.enums import EvidenceStatus
from app.models.membership import Membership
from app.models.user import User
from app.schemas.evidence import (
    EvidenceApproveRequest,
    EvidenceListResponse,
    EvidenceQueryParams,
    EvidenceResponse,
    EvidenceSummary,
    EvidenceUpdateRequest,
    EvidenceUploadRequest,
)
from app.services.evidence_service import EvidenceService
from app.services.storage.factory import get_storage_backend
from app.services.storage.local import content_disposition

router = APIRouter(prefix="/evidence", tags=["Evidence"])


def _get_evidence_service(
    db: AsyncSession = Depends(get_tenant_db),
) -> EvidenceService:
    return EvidenceService(db=db, storage=get_storage_backend())


@router.post("/upload", response_model=EvidenceResponse, status_code=201)
async def upload_evidence(
    file: UploadFile,
    title: str = Query(min_length=1, max_length=500),
    description: str | None = Query(default=None),
    control_ids: list[uuid.UUID] | None = Query(default=None),
    tags: list[str] | None = Query(default=None),
    auth: tuple[User, Membership] = Depends(require_permission(Resource.EVIDENCE, Action.WRITE)),
    service: EvidenceService = Depends(_get_evidence_service),
) -> EvidenceResponse:
    user, membership = auth
    metadata = EvidenceUploadRequest(
        title=title,
        description=description,
        control_ids=control_ids,
        tags=tags,
    )
    evidence = await service.upload_evidence(
        tenant_id=membership.tenant_id,
        file=file,
        metadata=metadata,
        uploaded_by=user.id,
    )
    return EvidenceResponse.model_validate(evidence)


@router.get("", response_model=EvidenceListResponse)
async def list_evidence(
    status_filter: EvidenceStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    control_id: uuid.UUID | None = Query(default=None),
    uploaded_by: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    auth: tuple[User, Membership] = Depends(require_permission(Resource.EVIDENCE, Action.READ)),
    service: EvidenceService = Depends(_get_evidence_service),
) -> EvidenceListResponse:
    _, membership = auth
    params = EvidenceQueryParams(
        status=status_filter,
        search=search,
        control_id=control_id,
        uploaded_by=uploaded_by,
        limit=limit,
        offset=offset,
    )
    items, total = await service.list_evidence(membership.tenant_id, params)
    return EvidenceListResponse(
        items=[EvidenceResponse.model_validate(e) for e in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=EvidenceSummary)
async def evidence_summary(
    auth: tuple[User, Membership] = Depends(require_permission(Resource.EVIDENCE, Action.READ)),
    service: EvidenceService = Depends(_get_evidence_service),
) -> EvidenceSummary:
    _, membership = auth
    return await service.get_evidence_summary(membership.tenant_id)


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: uuid.UUID,
    auth: tuple[User, Membership] = Depends(require_permission(Resource.EVIDENCE, Action.READ)),
    service: EvidenceService = Depends(_get_evidence_service),
) -> EvidenceResponse:
    _, membership = auth
    evidence = await service.get_evidence(membership.tenant_id, evidence_id)
    return EvidenceResponse.model_validate(evidence)


@router.put("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: uuid.UUID,
    data: EvidenceUpdateRequest,
    auth: tuple[User, Membership] = Depends(require_permission(Resource.EVIDENCE, Action.WRITE)),
    service: EvidenceService = Depends(_get_evidence_service),
) -> EvidenceResponse:
    _, membership = auth
    evidence = await service.update_evidence(membership.tenant_id, evidence_id, data)
    return EvidenceResponse.model_validate(evidence)


@router.post("/{evidence_id}/approve", response_model=EvidenceResponse)
async def approve_evidence(
    evidence_id: uuid.UUID,
    data: EvidenceApproveRequest,
    auth: tuple[User, Membership] = Depends(require_permission(Resource.EVIDENCE, Action.ADMIN)),
    service: EvidenceService = Depends(_get_evidence_service),
) -> EvidenceResponse:
    user, membership = auth
    evidence = await service.approve_evidence(
        membership.tenant_id, evidence_id, data, approved_by=user.id
    )
    return EvidenceResponse.model_validate(evidence)


@router.get("/{evidence_id}/download")
async def download_evidence(
    evidence_id: uuid.UUID,
    auth: tuple[User, Membership] = Depends(require_permission(Resource.EVIDENCE, Action.READ)),
    service: EvidenceService = Depends(_get_evidence_service),
) -> Response:
    _, membership = auth
    content, evidence = await service.download_evidence(membership.tenant_id, evidence_id)
    return Response(
        content=content,
        media_type=evidence.content_type,
        headers={
            "Content-Disposition": content_disposition(evidence.file_name),
        },
    )


@router.delete("/{evidence_id}", status_code=204)
async def delete_evidence(
    evidence_id: uuid.UUID,
    auth: tuple[User, Membership] = Depends(require_permission(Resource.EVIDENCE, Action.DELETE)),
    service: EvidenceService = Depends(_get_evidence_service),
) -> None:
    _, membership = auth
    await service.delete_evidence(membership.tenant_id, evidence_id)


@router.get("/by-control/{control_id}", response_model=list[EvidenceResponse])
async def get_evidence_by_control(
    control_id: uuid.UUID,
    auth: tuple[User, Membership] = Depends(require_permission(Resource.EVIDENCE, Action.READ)),
    service: EvidenceService = Depends(_get_evidence_service),
) -> list[EvidenceResponse]:
    _, membership = auth
    items = await service.get_control_evidence(membership.tenant_id, control_id)
    return [EvidenceResponse.model_validate(e) for e in items]
