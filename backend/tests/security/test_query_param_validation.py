"""List endpoints must validate filter/sort params at the API boundary (422, not 500)."""

import pytest
from pydantic import ValidationError

from app.main import app
from app.schemas.risk import RiskQueryParams

pytestmark = pytest.mark.security


class TestRiskSortAllowlist:
    @pytest.mark.parametrize(
        "col", ["inherent_score", "residual_score", "title", "due_date", "status"]
    )
    def test_allowed_sort_columns(self, col):
        assert RiskQueryParams(sort_by=col).sort_by == col

    @pytest.mark.parametrize(
        "col", ["__init__", "__class__", "tenant_id", "metadata", "registry", "nope"]
    )
    def test_disallowed_sort_columns_rejected(self, col):
        with pytest.raises(ValidationError):
            RiskQueryParams(sort_by=col)

    def test_sort_order_restricted(self):
        with pytest.raises(ValidationError):
            RiskQueryParams(sort_order="sideways")


def _query_params(path: str) -> dict[str, dict]:
    op = app.openapi()["paths"][path]["get"]
    return {p["name"]: p["schema"] for p in op.get("parameters", []) if p["in"] == "query"}


def _has_enum(schema: dict) -> bool:
    if "enum" in schema or "$ref" in schema:
        return True
    return any(_has_enum(s) for s in schema.get("anyOf", []))


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/api/v1/risks", ["category", "status", "likelihood", "impact", "sort_by", "sort_order"]),
        ("/api/v1/vendors", ["status", "risk_level"]),
        ("/api/v1/policies", ["status"]),
    ],
)
def test_list_filters_declared_as_enums(path, params):
    declared = _query_params(path)
    for name in params:
        assert _has_enum(declared[name]), f"{path}?{name} is not enum-validated"


def test_every_risk_sort_field_is_a_real_column():
    import typing

    from app.models.risk import Risk
    from app.schemas.risk import RiskSortField

    for col in typing.get_args(RiskSortField):
        assert col in Risk.__table__.columns, f"sort field {col!r} is not a Risk column"
