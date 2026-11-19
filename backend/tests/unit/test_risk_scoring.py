"""Tests for risk scoring and risk service utilities."""

import pytest

from app.models.enums import RiskImpact, RiskLikelihood
from app.models.risk import IMPACT_SCORES, LIKELIHOOD_SCORES, compute_risk_score
from app.services.risk_service import RiskService


class TestComputeRiskScore:
    def test_returns_none_when_likelihood_is_none(self):
        assert compute_risk_score(None, RiskImpact.HIGH) is None

    def test_returns_none_when_impact_is_none(self):
        assert compute_risk_score(RiskLikelihood.HIGH, None) is None

    def test_returns_none_when_both_none(self):
        assert compute_risk_score(None, None) is None

    def test_minimum_score(self):
        score = compute_risk_score(RiskLikelihood.VERY_LOW, RiskImpact.VERY_LOW)
        assert score == 1.0

    def test_maximum_score(self):
        score = compute_risk_score(RiskLikelihood.VERY_HIGH, RiskImpact.VERY_HIGH)
        assert score == 25.0

    def test_medium_medium(self):
        score = compute_risk_score(RiskLikelihood.MEDIUM, RiskImpact.MEDIUM)
        assert score == 9.0

    def test_high_low(self):
        score = compute_risk_score(RiskLikelihood.HIGH, RiskImpact.LOW)
        assert score == 8.0

    def test_returns_float(self):
        result = compute_risk_score(RiskLikelihood.LOW, RiskImpact.MEDIUM)
        assert isinstance(result, float)

    @pytest.mark.parametrize("likelihood", list(RiskLikelihood))
    @pytest.mark.parametrize("impact", list(RiskImpact))
    def test_all_combinations_produce_positive_scores(self, likelihood, impact):
        score = compute_risk_score(likelihood, impact)
        assert score is not None
        assert score > 0

    def test_score_increases_with_likelihood(self):
        scores = [
            compute_risk_score(lk, RiskImpact.HIGH)
            for lk in [
                RiskLikelihood.VERY_LOW,
                RiskLikelihood.LOW,
                RiskLikelihood.MEDIUM,
                RiskLikelihood.HIGH,
                RiskLikelihood.VERY_HIGH,
            ]
        ]
        assert scores == sorted(scores)
        assert len(set(scores)) == 5

    def test_score_increases_with_impact(self):
        scores = [
            compute_risk_score(RiskLikelihood.HIGH, imp)
            for imp in [
                RiskImpact.VERY_LOW,
                RiskImpact.LOW,
                RiskImpact.MEDIUM,
                RiskImpact.HIGH,
                RiskImpact.VERY_HIGH,
            ]
        ]
        assert scores == sorted(scores)
        assert len(set(scores)) == 5


class TestScoreMaps:
    def test_likelihood_scores_cover_all_values(self):
        assert set(LIKELIHOOD_SCORES.keys()) == set(RiskLikelihood)

    def test_impact_scores_cover_all_values(self):
        assert set(IMPACT_SCORES.keys()) == set(RiskImpact)

    def test_likelihood_scores_are_1_through_5(self):
        assert sorted(LIKELIHOOD_SCORES.values()) == [1, 2, 3, 4, 5]

    def test_impact_scores_are_1_through_5(self):
        assert sorted(IMPACT_SCORES.values()) == [1, 2, 3, 4, 5]


class TestScoreToLevel:
    def test_critical_threshold(self):
        assert RiskService.score_to_level(15.0) == "critical"
        assert RiskService.score_to_level(25.0) == "critical"

    def test_high_threshold(self):
        assert RiskService.score_to_level(10.0) == "high"
        assert RiskService.score_to_level(14.9) == "high"

    def test_medium_threshold(self):
        assert RiskService.score_to_level(5.0) == "medium"
        assert RiskService.score_to_level(9.9) == "medium"

    def test_low_threshold(self):
        assert RiskService.score_to_level(4.9) == "low"
        assert RiskService.score_to_level(1.0) == "low"
        assert RiskService.score_to_level(0.0) == "low"
