"""Tests for GRC Pydantic schema validation."""

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.models.enums import (
    ControlEffectiveness,
    ControlStatus,
    PolicyStatus,
    RiskCategory,
    RiskImpact,
    RiskLikelihood,
    RiskStatus,
    RiskTreatment,
    VendorRiskLevel,
    VendorStatus,
)
from app.schemas.evidence import (
    EvidenceApproveRequest,
    EvidenceQueryParams,
    EvidenceUploadRequest,
)
from app.schemas.framework import (
    ControlStatusSummary,
    TenantControlStatusUpdateRequest,
)
from app.schemas.policy import PolicyCreateRequest, PolicyQueryParams, PolicyUpdateRequest
from app.schemas.risk import RiskCreateRequest, RiskQueryParams, RiskUpdateRequest
from app.schemas.vendor import VendorCreateRequest, VendorQueryParams, VendorUpdateRequest


class TestRiskCreateRequest:
    def test_valid_minimal(self):
        req = RiskCreateRequest(
            title="Data breach risk",
            category=RiskCategory.TECHNICAL,
            likelihood=RiskLikelihood.HIGH,
            impact=RiskImpact.VERY_HIGH,
        )
        assert req.title == "Data breach risk"
        assert req.treatment is None
        assert req.related_control_ids is None

    def test_valid_full(self):
        uid = uuid.uuid4()
        req = RiskCreateRequest(
            title="Vendor outage",
            description="Critical vendor SLA breach",
            category=RiskCategory.OPERATIONAL,
            likelihood=RiskLikelihood.MEDIUM,
            impact=RiskImpact.HIGH,
            treatment=RiskTreatment.MITIGATE,
            treatment_plan="Implement failover",
            owner_id=uid,
            due_date=date(2025, 6, 1),
            related_control_ids=[uuid.uuid4()],
        )
        assert req.owner_id == uid

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            RiskCreateRequest(
                title="",
                category=RiskCategory.TECHNICAL,
                likelihood=RiskLikelihood.LOW,
                impact=RiskImpact.LOW,
            )

    def test_title_too_long_rejected(self):
        with pytest.raises(ValidationError):
            RiskCreateRequest(
                title="x" * 501,
                category=RiskCategory.TECHNICAL,
                likelihood=RiskLikelihood.LOW,
                impact=RiskImpact.LOW,
            )

    def test_invalid_category_rejected(self):
        with pytest.raises(ValidationError):
            RiskCreateRequest(
                title="Test",
                category="invalid",
                likelihood=RiskLikelihood.LOW,
                impact=RiskImpact.LOW,
            )


class TestRiskUpdateRequest:
    def test_partial_update(self):
        req = RiskUpdateRequest(status=RiskStatus.MITIGATING)
        dumped = req.model_dump(exclude_unset=True)
        assert "status" in dumped
        assert "title" not in dumped

    def test_residual_fields(self):
        req = RiskUpdateRequest(
            residual_likelihood=RiskLikelihood.LOW,
            residual_impact=RiskImpact.VERY_LOW,
        )
        assert req.residual_likelihood == RiskLikelihood.LOW


class TestRiskQueryParams:
    def test_defaults(self):
        params = RiskQueryParams()
        assert params.limit == 50
        assert params.offset == 0
        assert params.sort_by == "inherent_score"
        assert params.sort_order == "desc"

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            RiskQueryParams(limit=0)
        with pytest.raises(ValidationError):
            RiskQueryParams(limit=201)

    def test_all_filters(self):
        params = RiskQueryParams(
            category=RiskCategory.COMPLIANCE,
            status=RiskStatus.OPEN,
            likelihood=RiskLikelihood.HIGH,
            impact=RiskImpact.VERY_HIGH,
            min_score=10.0,
            search="breach",
        )
        assert params.category == RiskCategory.COMPLIANCE


class TestEvidenceUploadRequest:
    def test_valid(self):
        req = EvidenceUploadRequest(title="SOC 2 audit report")
        assert req.control_ids is None
        assert req.tags is None

    def test_with_control_ids(self):
        cid = uuid.uuid4()
        req = EvidenceUploadRequest(
            title="Pen test results",
            control_ids=[cid],
            tags=["pentest", "annual"],
        )
        assert len(req.control_ids) == 1

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            EvidenceUploadRequest(title="")


class TestEvidenceApproveRequest:
    def test_approve(self):
        req = EvidenceApproveRequest(approved=True, notes="Looks good")
        assert req.approved is True

    def test_reject(self):
        req = EvidenceApproveRequest(approved=False)
        assert req.notes is None


class TestEvidenceQueryParams:
    def test_defaults(self):
        params = EvidenceQueryParams()
        assert params.limit == 50
        assert params.status is None


class TestPolicyCreateRequest:
    def test_valid(self):
        req = PolicyCreateRequest(
            title="Acceptable Use Policy",
            content="# Policy\n\nAll users must...",
        )
        assert req.title == "Acceptable Use Policy"
        assert req.category is None

    def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            PolicyCreateRequest(title="Test", content="")

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            PolicyCreateRequest(title="", content="Content here")


class TestPolicyUpdateRequest:
    def test_partial_update(self):
        req = PolicyUpdateRequest(title="Updated Title")
        dumped = req.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "content" not in dumped


class TestPolicyQueryParams:
    def test_filter_by_status(self):
        params = PolicyQueryParams(status=PolicyStatus.PUBLISHED)
        assert params.status == PolicyStatus.PUBLISHED


class TestVendorCreateRequest:
    def test_valid_minimal(self):
        req = VendorCreateRequest(name="Acme Cloud")
        assert req.status == VendorStatus.ACTIVE
        assert req.risk_level is None

    def test_valid_full(self):
        req = VendorCreateRequest(
            name="CloudCo",
            description="Cloud hosting provider",
            category="Infrastructure",
            contact_name="John Doe",
            contact_email="john@cloudco.com",
            risk_level=VendorRiskLevel.HIGH,
            status=VendorStatus.UNDER_REVIEW,
            contract_start=date(2024, 1, 1),
            contract_end=date(2025, 12, 31),
        )
        assert req.contact_email == "john@cloudco.com"

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            VendorCreateRequest(name="")

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            VendorCreateRequest(name="Test", contact_email="not-an-email")


class TestVendorUpdateRequest:
    def test_partial_update(self):
        req = VendorUpdateRequest(risk_level=VendorRiskLevel.CRITICAL)
        dumped = req.model_dump(exclude_unset=True)
        assert dumped["risk_level"] == VendorRiskLevel.CRITICAL


class TestVendorQueryParams:
    def test_defaults(self):
        params = VendorQueryParams()
        assert params.limit == 50
        assert params.offset == 0

    def test_filter_by_risk_level(self):
        params = VendorQueryParams(risk_level=VendorRiskLevel.HIGH)
        assert params.risk_level == VendorRiskLevel.HIGH


class TestControlStatusUpdate:
    def test_valid(self):
        req = TenantControlStatusUpdateRequest(
            status=ControlStatus.IMPLEMENTED,
            effectiveness=ControlEffectiveness.FULL,
        )
        assert req.status == ControlStatus.IMPLEMENTED

    def test_status_only(self):
        req = TenantControlStatusUpdateRequest(status=ControlStatus.IN_PROGRESS)
        assert req.effectiveness is None

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            TenantControlStatusUpdateRequest(status="invalid")


class TestControlStatusSummary:
    def test_defaults(self):
        summary = ControlStatusSummary()
        assert summary.total == 0
        assert summary.compliance_percentage == 0.0

    def test_with_data(self):
        summary = ControlStatusSummary(
            total=100,
            implemented=60,
            in_progress=20,
            not_started=15,
            not_applicable=5,
            compliance_percentage=63.2,
        )
        assert summary.total == 100
