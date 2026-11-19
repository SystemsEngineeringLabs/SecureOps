"""Tests for evidence file validation rules."""

import pytest
from fastapi import HTTPException

from app.services.evidence_service import (
    ALLOWED_CONTENT_TYPES,
    BLOCKED_EXTENSIONS,
    EvidenceService,
)


class TestBlockedExtensions:
    def test_executable_blocked(self):
        assert ".exe" in BLOCKED_EXTENSIONS

    def test_bat_blocked(self):
        assert ".bat" in BLOCKED_EXTENSIONS

    def test_shell_script_blocked(self):
        assert ".sh" in BLOCKED_EXTENSIONS

    def test_powershell_blocked(self):
        assert ".ps1" in BLOCKED_EXTENSIONS

    def test_dll_blocked(self):
        assert ".dll" in BLOCKED_EXTENSIONS

    def test_vbs_blocked(self):
        assert ".vbs" in BLOCKED_EXTENSIONS

    def test_js_blocked(self):
        assert ".js" in BLOCKED_EXTENSIONS

    @pytest.mark.parametrize(
        "ext",
        [
            ".exe",
            ".bat",
            ".cmd",
            ".sh",
            ".ps1",
            ".dll",
            ".so",
            ".msi",
            ".com",
            ".scr",
            ".vbs",
            ".js",
            ".wsf",
            ".pif",
        ],
    )
    def test_all_dangerous_extensions_blocked(self, ext):
        assert ext in BLOCKED_EXTENSIONS


class TestAllowedContentTypes:
    def test_pdf_allowed(self):
        assert "application/pdf" in ALLOWED_CONTENT_TYPES

    def test_png_allowed(self):
        assert "image/png" in ALLOWED_CONTENT_TYPES

    def test_csv_allowed(self):
        assert "text/csv" in ALLOWED_CONTENT_TYPES

    def test_json_allowed(self):
        assert "application/json" in ALLOWED_CONTENT_TYPES

    def test_xlsx_allowed(self):
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in ALLOWED_CONTENT_TYPES
        )

    def test_docx_allowed(self):
        assert (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            in ALLOWED_CONTENT_TYPES
        )

    def test_html_not_allowed(self):
        assert "text/html" not in ALLOWED_CONTENT_TYPES

    def test_octet_stream_not_allowed(self):
        assert "application/octet-stream" not in ALLOWED_CONTENT_TYPES


class TestValidateFile:
    @pytest.fixture
    def svc(self):
        return EvidenceService.__new__(EvidenceService)

    def test_valid_pdf(self, svc):
        svc._validate_file("report.pdf", "application/pdf", 1024)

    def test_valid_png(self, svc):
        svc._validate_file("screenshot.png", "image/png", 5000)

    def test_blocked_extension_raises(self, svc):
        with pytest.raises(HTTPException) as exc_info:
            svc._validate_file("malware.exe", "application/pdf", 100)
        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail

    def test_blocked_content_type_raises(self, svc):
        with pytest.raises(HTTPException) as exc_info:
            svc._validate_file("data.bin", "application/octet-stream", 100)
        assert exc_info.value.status_code == 400

    def test_oversized_file_raises(self, svc):
        max_mb = 100
        from unittest.mock import patch

        with patch("app.services.evidence_service.settings") as mock_settings:
            mock_settings.EVIDENCE_MAX_UPLOAD_MB = max_mb
            oversized = max_mb * 1024 * 1024 + 1
            with pytest.raises(HTTPException) as exc_info:
                svc._validate_file("big.pdf", "application/pdf", oversized)
            assert exc_info.value.status_code == 400
            assert "maximum size" in exc_info.value.detail

    def test_case_insensitive_extension_check(self, svc):
        with pytest.raises(HTTPException):
            svc._validate_file("MALWARE.EXE", "application/pdf", 100)

    def test_double_extension_blocked(self, svc):
        with pytest.raises(HTTPException):
            svc._validate_file("report.pdf.exe", "application/pdf", 100)

    def test_no_extension_with_valid_content_type(self, svc):
        from unittest.mock import patch

        with patch("app.services.evidence_service.settings") as mock_settings:
            mock_settings.EVIDENCE_MAX_UPLOAD_MB = 100
            svc._validate_file("report", "application/pdf", 1024)
