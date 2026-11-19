import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import (
    ControlEffectiveness,
    ControlMappingType,
    ControlStatus,
)
from app.schemas.framework import (
    ControlDetailResponse,
    ControlMappingResponse,
    ControlResponse,
    ControlStatusSummary,
    FrameworkDetailResponse,
    FrameworkResponse,
    FrameworkVersionResponse,
    GapAssessmentResponse,
    TenantControlStatusResponse,
    TenantControlStatusUpdateRequest,
)

pytestmark = pytest.mark.unit


class TestControlStatusSummary:
    def test_defaults_to_zero(self):
        summary = ControlStatusSummary()
        assert summary.total == 0
        assert summary.compliance_percentage == 0.0

    def test_compliance_percentage_calculation(self):
        summary = ControlStatusSummary(
            total=100,
            implemented=40,
            in_progress=20,
            not_started=30,
            not_applicable=10,
            failed=0,
            compliance_percentage=44.4,
        )
        assessable = summary.total - summary.not_applicable
        expected = round(summary.implemented / assessable * 100, 1)
        assert summary.compliance_percentage == expected

    def test_full_compliance(self):
        summary = ControlStatusSummary(
            total=50,
            implemented=50,
            compliance_percentage=100.0,
        )
        assert summary.compliance_percentage == 100.0

    def test_zero_total(self):
        summary = ControlStatusSummary(total=0, compliance_percentage=0.0)
        assert summary.compliance_percentage == 0.0


class TestFrameworkSchemas:
    def test_framework_response_fields(self):
        fid = uuid.uuid4()
        resp = FrameworkResponse(
            id=fid,
            key="soc2",
            name="SOC 2 Type II",
            description="Trust services criteria",
            organization="AICPA",
            is_active=True,
        )
        assert resp.key == "soc2"
        assert resp.is_active is True

    def test_framework_version_response(self):
        fid = uuid.uuid4()
        vid = uuid.uuid4()
        resp = FrameworkVersionResponse(
            id=vid,
            framework_id=fid,
            version="2024.1",
            effective_date=date(2024, 1, 1),
            is_current=True,
        )
        assert resp.is_current is True
        assert resp.version == "2024.1"

    def test_framework_detail_includes_versions(self):
        fid = uuid.uuid4()
        vid = uuid.uuid4()
        detail = FrameworkDetailResponse(
            id=fid,
            key="iso27001",
            name="ISO 27001",
            is_active=True,
            versions=[
                FrameworkVersionResponse(
                    id=vid,
                    framework_id=fid,
                    version="2022",
                    is_current=True,
                )
            ],
            control_count=114,
        )
        assert detail.control_count == 114
        assert len(detail.versions) == 1


class TestControlSchemas:
    def test_control_response(self):
        cid = uuid.uuid4()
        vid = uuid.uuid4()
        resp = ControlResponse(
            id=cid,
            framework_version_id=vid,
            code="CC6.1",
            title="Logical Access Controls",
            description="Entity restricts logical access",
            category="Common Criteria",
            sort_order=1,
        )
        assert resp.code == "CC6.1"

    def test_control_mapping_response(self):
        mid = uuid.uuid4()
        src = uuid.uuid4()
        tgt = uuid.uuid4()
        resp = ControlMappingResponse(
            id=mid,
            source_control_id=src,
            target_control_id=tgt,
            mapping_type=ControlMappingType.EQUIVALENT,
            notes="Direct equivalent",
        )
        assert resp.mapping_type == ControlMappingType.EQUIVALENT

    def test_control_detail_with_mappings(self):
        cid = uuid.uuid4()
        vid = uuid.uuid4()
        mid = uuid.uuid4()
        detail = ControlDetailResponse(
            id=cid,
            framework_version_id=vid,
            code="A.5.1",
            title="Information security policies",
            sort_order=1,
            mappings=[
                ControlMappingResponse(
                    id=mid,
                    source_control_id=cid,
                    target_control_id=uuid.uuid4(),
                    mapping_type=ControlMappingType.PARTIAL,
                )
            ],
        )
        assert len(detail.mappings) == 1

    def test_control_detail_no_tenant_status(self):
        detail = ControlDetailResponse(
            id=uuid.uuid4(),
            framework_version_id=uuid.uuid4(),
            code="CC1.1",
            title="Control Environment",
            sort_order=0,
        )
        assert detail.tenant_status is None
        assert detail.mappings == []


class TestTenantControlStatus:
    def test_update_request_required_status(self):
        req = TenantControlStatusUpdateRequest(status=ControlStatus.IN_PROGRESS)
        assert req.status == ControlStatus.IN_PROGRESS
        assert req.effectiveness is None

    def test_update_request_all_fields(self):
        owner = uuid.uuid4()
        req = TenantControlStatusUpdateRequest(
            status=ControlStatus.IMPLEMENTED,
            effectiveness=ControlEffectiveness.FULL,
            owner_id=owner,
            notes="Verified by audit team",
        )
        assert req.effectiveness == ControlEffectiveness.FULL
        assert req.owner_id == owner

    def test_status_response(self):
        sid = uuid.uuid4()
        cid = uuid.uuid4()
        resp = TenantControlStatusResponse(
            id=sid,
            control_id=cid,
            status=ControlStatus.IMPLEMENTED,
            effectiveness=ControlEffectiveness.FULL,
            evidence_count=3,
        )
        assert resp.evidence_count == 3
        assert resp.last_assessed_at is None


class TestGapAssessment:
    def test_gap_assessment_response(self):
        vid = uuid.uuid4()
        gap = GapAssessmentResponse(
            framework_version_id=vid,
            summary=ControlStatusSummary(
                total=100,
                not_started=60,
                in_progress=20,
                implemented=20,
                compliance_percentage=20.0,
            ),
            gaps=[
                ControlDetailResponse(
                    id=uuid.uuid4(),
                    framework_version_id=vid,
                    code="CC7.1",
                    title="System Operations",
                    sort_order=1,
                )
            ],
        )
        assert len(gap.gaps) == 1
        assert gap.summary.compliance_percentage == 20.0

    def test_gap_assessment_empty_gaps(self):
        vid = uuid.uuid4()
        gap = GapAssessmentResponse(
            framework_version_id=vid,
            summary=ControlStatusSummary(
                total=10,
                implemented=10,
                compliance_percentage=100.0,
            ),
            gaps=[],
        )
        assert len(gap.gaps) == 0


class TestControlStatusEnum:
    def test_all_statuses_have_values(self):
        expected = {"not_started", "in_progress", "implemented", "not_applicable", "failed"}
        assert {s.value for s in ControlStatus} == expected

    def test_effectiveness_levels(self):
        expected = {"none", "partial", "full"}
        assert {e.value for e in ControlEffectiveness} == expected

    def test_mapping_types(self):
        expected = {"equivalent", "partial", "related"}
        assert {m.value for m in ControlMappingType} == expected
