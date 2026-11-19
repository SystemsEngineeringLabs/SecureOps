import uuid
from datetime import date

import pytest

from app.models.enums import (
    PolicyStatus,
    VendorRiskLevel,
    VendorStatus,
)
from app.schemas.policy import (
    PolicyCreateRequest,
    PolicyQueryParams,
    PolicyUpdateRequest,
)
from app.schemas.vendor import (
    VendorCreateRequest,
    VendorQueryParams,
    VendorSummary,
    VendorUpdateRequest,
)

pytestmark = pytest.mark.unit


class TestPolicySchemas:
    def test_create_request_valid(self):
        req = PolicyCreateRequest(
            title="Acceptable Use Policy",
            content="# Policy\nAll employees must...",
            category="security",
            tags=["security", "hr"],
        )
        assert req.title == "Acceptable Use Policy"
        assert req.category == "security"

    def test_create_request_empty_title(self):
        with pytest.raises(Exception):
            PolicyCreateRequest(title="", content="body")

    def test_create_request_empty_content(self):
        with pytest.raises(Exception):
            PolicyCreateRequest(title="Title", content="")

    def test_create_request_minimal(self):
        req = PolicyCreateRequest(title="Min", content="body")
        assert req.category is None
        assert req.tags is None
        assert req.owner_id is None

    def test_create_request_all_fields(self):
        owner = uuid.uuid4()
        req = PolicyCreateRequest(
            title="Data Retention Policy",
            content="Retain data for 7 years...",
            category="data",
            effective_date=date(2025, 1, 1),
            review_date=date(2026, 1, 1),
            owner_id=owner,
            tags=["retention", "data"],
        )
        assert req.owner_id == owner
        assert req.review_date == date(2026, 1, 1)

    def test_update_request_partial(self):
        req = PolicyUpdateRequest(title="Updated Title")
        dumped = req.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "content" not in dumped

    def test_update_request_status(self):
        req = PolicyUpdateRequest(status=PolicyStatus.PUBLISHED)
        assert req.status == PolicyStatus.PUBLISHED

    def test_query_params_defaults(self):
        params = PolicyQueryParams()
        assert params.limit == 50
        assert params.offset == 0
        assert params.category is None
        assert params.status is None

    def test_query_params_with_filters(self):
        params = PolicyQueryParams(
            category="security",
            status=PolicyStatus.DRAFT,
            search="access",
            limit=10,
        )
        assert params.status == PolicyStatus.DRAFT
        assert params.search == "access"


class TestPolicyStatusEnum:
    def test_all_statuses(self):
        expected = {"draft", "published", "archived"}
        assert {s.value for s in PolicyStatus} == expected

    def test_lifecycle_order(self):
        statuses = list(PolicyStatus)
        assert PolicyStatus.DRAFT in statuses
        assert PolicyStatus.PUBLISHED in statuses
        assert PolicyStatus.ARCHIVED in statuses


class TestVendorSchemas:
    def test_create_request_valid(self):
        req = VendorCreateRequest(
            name="CloudFlare Inc",
            description="CDN and security provider",
            category="infrastructure",
            contact_email="vendor@example.com",
            risk_level=VendorRiskLevel.LOW,
        )
        assert req.name == "CloudFlare Inc"
        assert req.risk_level == VendorRiskLevel.LOW

    def test_create_request_empty_name(self):
        with pytest.raises(Exception):
            VendorCreateRequest(name="")

    def test_create_request_minimal(self):
        req = VendorCreateRequest(name="Acme")
        assert req.status == VendorStatus.ACTIVE
        assert req.risk_level is None
        assert req.contact_email is None

    def test_create_request_invalid_email(self):
        with pytest.raises(Exception):
            VendorCreateRequest(name="Vendor", contact_email="not-an-email")

    def test_create_request_all_fields(self):
        owner = uuid.uuid4()
        req = VendorCreateRequest(
            name="AWS",
            description="Cloud provider",
            category="cloud",
            contact_name="John",
            contact_email="john@aws.example.com",
            website="https://aws.example.com",
            risk_level=VendorRiskLevel.HIGH,
            status=VendorStatus.ACTIVE,
            contract_start=date(2024, 1, 1),
            contract_end=date(2025, 12, 31),
            owner_id=owner,
            notes="Primary cloud provider",
        )
        assert req.owner_id == owner
        assert req.contract_end == date(2025, 12, 31)

    def test_update_request_partial(self):
        req = VendorUpdateRequest(risk_level=VendorRiskLevel.CRITICAL)
        dumped = req.model_dump(exclude_unset=True)
        assert "risk_level" in dumped
        assert "name" not in dumped

    def test_query_params_defaults(self):
        params = VendorQueryParams()
        assert params.limit == 50
        assert params.offset == 0

    def test_query_params_with_filters(self):
        params = VendorQueryParams(
            status=VendorStatus.UNDER_REVIEW,
            risk_level=VendorRiskLevel.HIGH,
            search="cloud",
        )
        assert params.risk_level == VendorRiskLevel.HIGH

    def test_vendor_summary_schema(self):
        summary = VendorSummary(
            total=25,
            by_status={"active": 20, "inactive": 5},
            by_risk_level={"low": 10, "medium": 8, "high": 5, "critical": 2},
            contracts_expiring_soon=3,
        )
        assert summary.total == 25
        assert summary.contracts_expiring_soon == 3


class TestVendorEnums:
    def test_risk_levels(self):
        expected = {"low", "medium", "high", "critical"}
        assert {r.value for r in VendorRiskLevel} == expected

    def test_vendor_statuses(self):
        expected = {"active", "under_review", "inactive", "terminated"}
        assert {s.value for s in VendorStatus} == expected

    def test_risk_level_severity_order(self):
        levels = [
            VendorRiskLevel.LOW,
            VendorRiskLevel.MEDIUM,
            VendorRiskLevel.HIGH,
            VendorRiskLevel.CRITICAL,
        ]
        assert len(levels) == len(VendorRiskLevel)
