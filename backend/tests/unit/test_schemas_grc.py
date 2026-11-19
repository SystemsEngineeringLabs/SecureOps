import uuid
from datetime import UTC, date, datetime

import pytest

from app.models.enums import (
    EvidenceCollectionMethod,
    EvidenceStatus,
    PolicyStatus,
    RiskCategory,
    RiskImpact,
    RiskLikelihood,
    RiskStatus,
    RiskTreatment,
    VendorRiskLevel,
    VendorStatus,
)
from app.schemas.evidence import EvidenceResponse
from app.schemas.policy import PolicyResponse
from app.schemas.risk import (
    RiskHeatmapCell,
    RiskHeatmapResponse,
    RiskListResponse,
    RiskResponse,
)
from app.schemas.vendor import VendorResponse

pytestmark = pytest.mark.unit


class TestRiskResponseSerialization:
    def test_full_response(self):
        rid = uuid.uuid4()
        oid = uuid.uuid4()
        now = datetime.now(UTC)
        resp = RiskResponse(
            id=rid,
            title="Data breach risk",
            description="PII exposure through API",
            category=RiskCategory.TECHNICAL,
            source="manual",
            likelihood=RiskLikelihood.HIGH,
            impact=RiskImpact.VERY_HIGH,
            inherent_score=20.0,
            treatment=RiskTreatment.MITIGATE,
            treatment_plan="Implement input validation",
            residual_likelihood=RiskLikelihood.LOW,
            residual_impact=RiskImpact.MEDIUM,
            residual_score=6.0,
            status=RiskStatus.MITIGATING,
            owner_id=oid,
            due_date=date(2025, 6, 1),
            related_control_ids=[uuid.uuid4()],
            last_reviewed_at=now,
            next_review_at=now,
            created_at=now,
            updated_at=now,
        )
        data = resp.model_dump()
        assert data["title"] == "Data breach risk"
        assert data["inherent_score"] == 20.0
        assert data["status"] == RiskStatus.MITIGATING

    def test_minimal_response(self):
        now = datetime.now(UTC)
        resp = RiskResponse(
            id=uuid.uuid4(),
            title="Simple risk",
            description=None,
            category=RiskCategory.OPERATIONAL,
            source=None,
            likelihood=RiskLikelihood.LOW,
            impact=RiskImpact.LOW,
            inherent_score=4.0,
            treatment=None,
            treatment_plan=None,
            residual_likelihood=None,
            residual_impact=None,
            residual_score=None,
            status=RiskStatus.OPEN,
            owner_id=None,
            due_date=None,
            related_control_ids=None,
            last_reviewed_at=None,
            next_review_at=None,
            created_at=now,
            updated_at=now,
        )
        data = resp.model_dump()
        assert data["residual_score"] is None
        assert data["owner_id"] is None

    def test_heatmap_cell(self):
        cell = RiskHeatmapCell(
            likelihood="high",
            impact="very_high",
            count=3,
            risk_ids=[uuid.uuid4(), uuid.uuid4(), uuid.uuid4()],
        )
        assert cell.count == 3
        assert len(cell.risk_ids) == 3

    def test_heatmap_response(self):
        resp = RiskHeatmapResponse(cells=[])
        assert resp.cells == []

    def test_list_response(self):
        resp = RiskListResponse(items=[], total=0, limit=50, offset=0)
        assert resp.total == 0


class TestEvidenceResponseSerialization:
    def test_full_response(self):
        now = datetime.now(UTC)
        resp = EvidenceResponse(
            id=uuid.uuid4(),
            title="SOC 2 Report",
            description="Annual audit evidence",
            file_name="soc2_report.pdf",
            file_size=2048576,
            content_type="application/pdf",
            sha256_hash="a" * 64,
            version=1,
            status=EvidenceStatus.APPROVED,
            uploaded_by=uuid.uuid4(),
            approved_by=uuid.uuid4(),
            approved_at=now,
            expires_at=None,
            collection_method=EvidenceCollectionMethod.MANUAL,
            source="manual_upload",
            tags=["soc2", "annual"],
            created_at=now,
            updated_at=now,
        )
        data = resp.model_dump()
        assert data["status"] == EvidenceStatus.APPROVED
        assert data["version"] == 1

    def test_pending_response(self):
        now = datetime.now(UTC)
        resp = EvidenceResponse(
            id=uuid.uuid4(),
            title="Pending doc",
            description=None,
            file_name="doc.pdf",
            file_size=1024,
            content_type="application/pdf",
            sha256_hash="b" * 64,
            version=1,
            status=EvidenceStatus.PENDING,
            uploaded_by=uuid.uuid4(),
            approved_by=None,
            approved_at=None,
            expires_at=None,
            collection_method=EvidenceCollectionMethod.MANUAL,
            source=None,
            tags=None,
            created_at=now,
            updated_at=None,
        )
        data = resp.model_dump()
        assert data["approved_by"] is None
        assert data["approved_at"] is None


class TestPolicyResponseSerialization:
    def test_draft_policy(self):
        now = datetime.now(UTC)
        resp = PolicyResponse(
            id=uuid.uuid4(),
            title="Password Policy",
            content="# Password Requirements\n...",
            category="security",
            version=1,
            status=PolicyStatus.DRAFT,
            approved_by=None,
            approved_at=None,
            effective_date=None,
            review_date=None,
            owner_id=uuid.uuid4(),
            tags=["password", "security"],
            created_at=now,
            updated_at=None,
        )
        data = resp.model_dump()
        assert data["status"] == PolicyStatus.DRAFT
        assert data["version"] == 1

    def test_published_policy(self):
        now = datetime.now(UTC)
        approver = uuid.uuid4()
        resp = PolicyResponse(
            id=uuid.uuid4(),
            title="Data Classification Policy",
            content="All data must be classified...",
            category="data",
            version=3,
            status=PolicyStatus.PUBLISHED,
            approved_by=approver,
            approved_at=now,
            effective_date=date(2025, 1, 1),
            review_date=date(2026, 1, 1),
            owner_id=uuid.uuid4(),
            tags=None,
            created_at=now,
            updated_at=now,
        )
        data = resp.model_dump()
        assert data["status"] == PolicyStatus.PUBLISHED
        assert data["approved_by"] == approver


class TestVendorResponseSerialization:
    def test_active_vendor(self):
        now = datetime.now(UTC)
        resp = VendorResponse(
            id=uuid.uuid4(),
            name="Datadog",
            description="Monitoring platform",
            category="observability",
            contact_name="Sales",
            contact_email="sales@example.com",
            website="https://example.com",
            risk_level=VendorRiskLevel.MEDIUM,
            status=VendorStatus.ACTIVE,
            contract_start=date(2024, 1, 1),
            contract_end=date(2025, 12, 31),
            last_assessment_at=now,
            next_assessment_at=now,
            owner_id=uuid.uuid4(),
            notes="Renewed annually",
            created_at=now,
            updated_at=now,
        )
        data = resp.model_dump()
        assert data["risk_level"] == VendorRiskLevel.MEDIUM
        assert data["status"] == VendorStatus.ACTIVE

    def test_minimal_vendor(self):
        now = datetime.now(UTC)
        resp = VendorResponse(
            id=uuid.uuid4(),
            name="Small Vendor",
            description=None,
            category=None,
            contact_name=None,
            contact_email=None,
            website=None,
            risk_level=None,
            status=VendorStatus.ACTIVE,
            contract_start=None,
            contract_end=None,
            last_assessment_at=None,
            next_assessment_at=None,
            owner_id=None,
            notes=None,
            created_at=now,
            updated_at=None,
        )
        data = resp.model_dump()
        assert data["risk_level"] is None
        assert data["contract_end"] is None


class TestAllGrcEnumsCovered:
    def test_risk_category_values(self):
        expected = {
            "operational",
            "technical",
            "compliance",
            "strategic",
            "financial",
            "reputational",
        }
        assert {c.value for c in RiskCategory} == expected

    def test_risk_treatment_values(self):
        expected = {"accept", "mitigate", "transfer", "avoid"}
        assert {t.value for t in RiskTreatment} == expected

    def test_risk_status_values(self):
        expected = {"open", "mitigating", "closed", "accepted"}
        assert {s.value for s in RiskStatus} == expected

    def test_risk_likelihood_values(self):
        expected = {"very_low", "low", "medium", "high", "very_high"}
        assert {lk.value for lk in RiskLikelihood} == expected

    def test_risk_impact_values(self):
        expected = {"very_low", "low", "medium", "high", "very_high"}
        assert {i.value for i in RiskImpact} == expected

    def test_evidence_status_values(self):
        expected = {"pending", "approved", "rejected", "expired"}
        assert {s.value for s in EvidenceStatus} == expected

    def test_policy_status_values(self):
        expected = {"draft", "published", "archived"}
        assert {s.value for s in PolicyStatus} == expected

    def test_vendor_risk_level_values(self):
        expected = {"low", "medium", "high", "critical"}
        assert {r.value for r in VendorRiskLevel} == expected

    def test_vendor_status_values(self):
        expected = {"active", "under_review", "inactive", "terminated"}
        assert {s.value for s in VendorStatus} == expected
