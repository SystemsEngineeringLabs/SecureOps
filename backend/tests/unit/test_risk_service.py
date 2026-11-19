import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import (
    RiskCategory,
    RiskImpact,
    RiskLikelihood,
    RiskStatus,
    RiskTreatment,
)
from app.models.risk import IMPACT_SCORES, LIKELIHOOD_SCORES, compute_risk_score
from app.schemas.risk import (
    RiskCreateRequest,
    RiskHeatmapCell,
    RiskQueryParams,
    RiskSummary,
    RiskUpdateRequest,
)
from app.services.risk_service import RiskService

pytestmark = pytest.mark.unit


class TestComputeRiskScore:
    def test_very_low_very_low(self):
        assert compute_risk_score(RiskLikelihood.VERY_LOW, RiskImpact.VERY_LOW) == 1.0

    def test_very_high_very_high(self):
        assert compute_risk_score(RiskLikelihood.VERY_HIGH, RiskImpact.VERY_HIGH) == 25.0

    def test_medium_medium(self):
        assert compute_risk_score(RiskLikelihood.MEDIUM, RiskImpact.MEDIUM) == 9.0

    def test_high_low(self):
        assert compute_risk_score(RiskLikelihood.HIGH, RiskImpact.LOW) == 8.0

    def test_none_likelihood(self):
        assert compute_risk_score(None, RiskImpact.HIGH) is None

    def test_none_impact(self):
        assert compute_risk_score(RiskLikelihood.HIGH, None) is None

    def test_both_none(self):
        assert compute_risk_score(None, None) is None

    def test_all_combinations_are_positive(self):
        for lk in RiskLikelihood:
            for imp in RiskImpact:
                score = compute_risk_score(lk, imp)
                assert score is not None
                assert score > 0

    def test_score_increases_with_likelihood(self):
        prev = 0.0
        for lk in [
            RiskLikelihood.VERY_LOW,
            RiskLikelihood.LOW,
            RiskLikelihood.MEDIUM,
            RiskLikelihood.HIGH,
            RiskLikelihood.VERY_HIGH,
        ]:
            score = compute_risk_score(lk, RiskImpact.MEDIUM)
            assert score > prev
            prev = score

    def test_score_increases_with_impact(self):
        prev = 0.0
        for imp in [
            RiskImpact.VERY_LOW,
            RiskImpact.LOW,
            RiskImpact.MEDIUM,
            RiskImpact.HIGH,
            RiskImpact.VERY_HIGH,
        ]:
            score = compute_risk_score(RiskLikelihood.MEDIUM, imp)
            assert score > prev
            prev = score


class TestScoreToLevel:
    def test_critical_at_25(self):
        assert RiskService.score_to_level(25.0) == "critical"

    def test_critical_at_15(self):
        assert RiskService.score_to_level(15.0) == "critical"

    def test_high_at_14(self):
        assert RiskService.score_to_level(14.0) == "high"

    def test_high_at_10(self):
        assert RiskService.score_to_level(10.0) == "high"

    def test_medium_at_9(self):
        assert RiskService.score_to_level(9.0) == "medium"

    def test_medium_at_5(self):
        assert RiskService.score_to_level(5.0) == "medium"

    def test_low_at_4(self):
        assert RiskService.score_to_level(4.0) == "low"

    def test_low_at_1(self):
        assert RiskService.score_to_level(1.0) == "low"

    def test_low_at_zero(self):
        assert RiskService.score_to_level(0.0) == "low"

    def test_boundaries_are_consistent(self):
        levels = [RiskService.score_to_level(float(i)) for i in range(1, 26)]
        assert levels[0] == "low"
        assert levels[4] == "medium"
        assert levels[9] == "high"
        assert levels[14] == "critical"


class TestLikelihoodAndImpactScores:
    def test_likelihood_scores_cover_all_values(self):
        for lk in RiskLikelihood:
            assert lk in LIKELIHOOD_SCORES

    def test_impact_scores_cover_all_values(self):
        for imp in RiskImpact:
            assert imp in IMPACT_SCORES

    def test_likelihood_scores_range_1_to_5(self):
        values = sorted(LIKELIHOOD_SCORES.values())
        assert values == [1, 2, 3, 4, 5]

    def test_impact_scores_range_1_to_5(self):
        values = sorted(IMPACT_SCORES.values())
        assert values == [1, 2, 3, 4, 5]


class TestRiskSchemaValidation:
    def test_create_request_valid(self):
        req = RiskCreateRequest(
            title="Test Risk",
            category=RiskCategory.TECHNICAL,
            likelihood=RiskLikelihood.HIGH,
            impact=RiskImpact.MEDIUM,
        )
        assert req.title == "Test Risk"
        assert req.treatment is None

    def test_create_request_empty_title_rejected(self):
        with pytest.raises(Exception):
            RiskCreateRequest(
                title="",
                category=RiskCategory.TECHNICAL,
                likelihood=RiskLikelihood.HIGH,
                impact=RiskImpact.MEDIUM,
            )

    def test_create_request_all_fields(self):
        owner = uuid.uuid4()
        control = uuid.uuid4()
        req = RiskCreateRequest(
            title="Full Risk",
            description="A detailed description",
            category=RiskCategory.COMPLIANCE,
            likelihood=RiskLikelihood.VERY_HIGH,
            impact=RiskImpact.VERY_HIGH,
            treatment=RiskTreatment.MITIGATE,
            treatment_plan="Apply patches",
            owner_id=owner,
            due_date=date(2025, 6, 1),
            related_control_ids=[control],
        )
        assert req.owner_id == owner
        assert req.related_control_ids == [control]

    def test_update_request_partial(self):
        req = RiskUpdateRequest(title="Updated Title")
        dumped = req.model_dump(exclude_unset=True)
        assert "title" in dumped
        assert "category" not in dumped

    def test_query_params_defaults(self):
        params = RiskQueryParams()
        assert params.limit == 50
        assert params.offset == 0
        assert params.sort_by == "inherent_score"
        assert params.sort_order == "desc"

    def test_query_params_limit_bounds(self):
        with pytest.raises(Exception):
            RiskQueryParams(limit=0)
        with pytest.raises(Exception):
            RiskQueryParams(limit=201)

    def test_risk_summary_schema(self):
        summary = RiskSummary(
            total=10,
            by_status={"open": 5, "closed": 5},
            by_category={"technical": 10},
            by_risk_level={"critical": 2, "high": 3, "medium": 3, "low": 2},
            average_inherent_score=12.5,
            average_residual_score=None,
        )
        assert summary.total == 10
        assert summary.average_residual_score is None
