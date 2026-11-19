import hashlib
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.models.enums import EvidenceCollectionMethod, EvidenceStatus
from app.schemas.evidence import (
    EvidenceApproveRequest,
    EvidenceQueryParams,
    EvidenceSummary,
    EvidenceUpdateRequest,
    EvidenceUploadRequest,
)
from app.services.evidence_service import (
    ALLOWED_CONTENT_TYPES,
    BLOCKED_EXTENSIONS,
    EvidenceService,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.upload = AsyncMock(return_value="tenant/2024/01/abc_report.pdf")
    storage.download = AsyncMock(return_value=b"file-content")
    storage.delete = AsyncMock()
    return storage


class TestFileValidation:
    @pytest.fixture
    def service(self, mock_db, mock_storage):
        return EvidenceService(mock_db, mock_storage)

    def test_blocked_extension_exe(self, service):
        with pytest.raises(HTTPException) as exc:
            service._validate_file("malware.exe", "application/octet-stream", 1000)
        assert exc.value.status_code == 400
        assert ".exe" in exc.value.detail

    def test_blocked_extension_bat(self, service):
        with pytest.raises(HTTPException):
            service._validate_file("script.bat", "application/octet-stream", 1000)

    def test_blocked_extension_ps1(self, service):
        with pytest.raises(HTTPException):
            service._validate_file("script.ps1", "application/octet-stream", 1000)

    def test_blocked_extension_dll(self, service):
        with pytest.raises(HTTPException):
            service._validate_file("lib.dll", "application/octet-stream", 1000)

    def test_blocked_extension_sh(self, service):
        with pytest.raises(HTTPException):
            service._validate_file("run.sh", "application/octet-stream", 1000)

    def test_blocked_extension_js(self, service):
        with pytest.raises(HTTPException):
            service._validate_file("payload.js", "application/octet-stream", 1000)

    def test_allowed_pdf(self, service):
        service._validate_file("report.pdf", "application/pdf", 1000)

    def test_allowed_png(self, service):
        service._validate_file("screenshot.png", "image/png", 1000)

    def test_allowed_csv(self, service):
        service._validate_file("data.csv", "text/csv", 1000)

    def test_allowed_xlsx(self, service):
        ct = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        service._validate_file("sheet.xlsx", ct, 1000)

    def test_disallowed_content_type(self, service):
        with pytest.raises(HTTPException) as exc:
            service._validate_file("data.bin", "application/octet-stream", 1000)
        assert exc.value.status_code == 400

    @patch("app.services.evidence_service.settings")
    def test_file_too_large(self, mock_settings, service):
        mock_settings.EVIDENCE_MAX_UPLOAD_MB = 50
        max_bytes = 50 * 1024 * 1024
        with pytest.raises(HTTPException) as exc:
            service._validate_file("big.pdf", "application/pdf", max_bytes + 1)
        assert exc.value.status_code == 400
        assert "50 MB" in exc.value.detail

    @patch("app.services.evidence_service.settings")
    def test_file_exactly_at_limit(self, mock_settings, service):
        mock_settings.EVIDENCE_MAX_UPLOAD_MB = 50
        max_bytes = 50 * 1024 * 1024
        service._validate_file("exact.pdf", "application/pdf", max_bytes)

    def test_case_insensitive_extension(self, service):
        with pytest.raises(HTTPException):
            service._validate_file("MALWARE.EXE", "application/octet-stream", 1000)

    def test_all_blocked_extensions_are_lowercase(self):
        for ext in BLOCKED_EXTENSIONS:
            assert ext == ext.lower()
            assert ext.startswith(".")


class TestAllowedContentTypes:
    def test_pdf_is_allowed(self):
        assert "application/pdf" in ALLOWED_CONTENT_TYPES

    def test_images_are_allowed(self):
        assert "image/png" in ALLOWED_CONTENT_TYPES
        assert "image/jpeg" in ALLOWED_CONTENT_TYPES

    def test_csv_is_allowed(self):
        assert "text/csv" in ALLOWED_CONTENT_TYPES

    def test_json_is_allowed(self):
        assert "application/json" in ALLOWED_CONTENT_TYPES

    def test_octet_stream_not_allowed(self):
        assert "application/octet-stream" not in ALLOWED_CONTENT_TYPES


class TestSha256Integrity:
    def test_sha256_deterministic(self):
        content = b"SOC 2 audit evidence document"
        hash1 = hashlib.sha256(content).hexdigest()
        hash2 = hashlib.sha256(content).hexdigest()
        assert hash1 == hash2

    def test_sha256_different_content(self):
        h1 = hashlib.sha256(b"document v1").hexdigest()
        h2 = hashlib.sha256(b"document v2").hexdigest()
        assert h1 != h2

    def test_sha256_format(self):
        h = hashlib.sha256(b"test").hexdigest()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestEvidenceSchemas:
    def test_upload_request_valid(self):
        req = EvidenceUploadRequest(
            title="Q4 SOC Report",
            description="Quarterly compliance evidence",
            control_ids=[uuid.uuid4()],
            tags=["soc2", "q4"],
        )
        assert req.title == "Q4 SOC Report"
        assert len(req.tags) == 2

    def test_upload_request_empty_title(self):
        with pytest.raises(Exception):
            EvidenceUploadRequest(title="")

    def test_upload_request_minimal(self):
        req = EvidenceUploadRequest(title="Minimal")
        assert req.control_ids is None
        assert req.tags is None

    def test_update_request_partial(self):
        req = EvidenceUpdateRequest(title="New Title")
        dumped = req.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "tags" not in dumped

    def test_approve_request(self):
        req = EvidenceApproveRequest(approved=True, notes="Looks good")
        assert req.approved is True

    def test_reject_request(self):
        req = EvidenceApproveRequest(approved=False, notes="Missing signatures")
        assert req.approved is False

    def test_query_params_defaults(self):
        params = EvidenceQueryParams()
        assert params.limit == 50
        assert params.offset == 0
        assert params.status is None

    def test_query_params_with_filters(self):
        cid = uuid.uuid4()
        params = EvidenceQueryParams(
            status=EvidenceStatus.PENDING,
            control_id=cid,
            limit=10,
        )
        assert params.status == EvidenceStatus.PENDING
        assert params.control_id == cid

    def test_evidence_summary_schema(self):
        summary = EvidenceSummary(
            total=100,
            by_status={"pending": 20, "approved": 70, "rejected": 10},
            pending_approval=20,
            expiring_soon=5,
            total_size_bytes=1024 * 1024 * 500,
        )
        assert summary.total == 100
        assert summary.pending_approval == 20


class TestEvidenceStatusEnum:
    def test_all_statuses(self):
        expected = {"pending", "approved", "rejected", "expired"}
        assert {s.value for s in EvidenceStatus} == expected

    def test_collection_methods(self):
        expected = {"manual", "automated"}
        assert {m.value for m in EvidenceCollectionMethod} == expected
