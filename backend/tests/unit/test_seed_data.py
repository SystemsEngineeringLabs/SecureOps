"""Tests for seed data integrity — SOC 2, ISO 27001, and cross-framework mappings."""

import pytest

from app.db.seed import CROSS_MAPPINGS, ISO27001_CONTROLS, SOC2_CONTROLS
from app.models.enums import ControlMappingType


class TestSOC2Controls:
    def test_has_controls(self):
        assert len(SOC2_CONTROLS) == 33

    def test_all_have_required_fields(self):
        for ctrl in SOC2_CONTROLS:
            assert "code" in ctrl
            assert "title" in ctrl
            assert "category" in ctrl
            assert "sort_order" in ctrl

    def test_no_duplicate_codes(self):
        codes = [c["code"] for c in SOC2_CONTROLS]
        assert len(codes) == len(set(codes))

    def test_no_duplicate_sort_orders(self):
        orders = [c["sort_order"] for c in SOC2_CONTROLS]
        assert len(orders) == len(set(orders))

    def test_sort_orders_sequential(self):
        orders = sorted(c["sort_order"] for c in SOC2_CONTROLS)
        assert orders == list(range(1, 34))

    def test_all_cc_categories_present(self):
        categories = {c["category"] for c in SOC2_CONTROLS}
        for i in range(1, 10):
            assert any(f"CC{i}" in cat for cat in categories), f"CC{i} missing"

    def test_codes_follow_naming_convention(self):
        for ctrl in SOC2_CONTROLS:
            assert ctrl["code"].startswith("CC"), f"{ctrl['code']} doesn't start with CC"

    def test_titles_not_empty(self):
        for ctrl in SOC2_CONTROLS:
            assert len(ctrl["title"]) > 5, f"Title too short: {ctrl['title']}"


class TestISO27001Controls:
    def test_has_controls(self):
        assert len(ISO27001_CONTROLS) == 93

    def test_all_have_required_fields(self):
        for ctrl in ISO27001_CONTROLS:
            assert "code" in ctrl
            assert "title" in ctrl
            assert "category" in ctrl
            assert "sort_order" in ctrl

    def test_no_duplicate_codes(self):
        codes = [c["code"] for c in ISO27001_CONTROLS]
        assert len(codes) == len(set(codes))

    def test_no_duplicate_sort_orders(self):
        orders = [c["sort_order"] for c in ISO27001_CONTROLS]
        assert len(orders) == len(set(orders))

    def test_sort_orders_sequential(self):
        orders = sorted(c["sort_order"] for c in ISO27001_CONTROLS)
        assert orders == list(range(1, 94))

    def test_annex_a_categories_present(self):
        categories = {c["category"] for c in ISO27001_CONTROLS}
        for section in ["A.5", "A.6", "A.7", "A.8"]:
            assert any(section in cat for cat in categories), f"{section} missing"

    def test_codes_follow_naming_convention(self):
        for ctrl in ISO27001_CONTROLS:
            assert ctrl["code"].startswith("A."), f"{ctrl['code']} doesn't start with A."

    def test_category_distribution(self):
        by_cat = {}
        for ctrl in ISO27001_CONTROLS:
            cat = ctrl["category"].split(" — ")[0]
            by_cat[cat] = by_cat.get(cat, 0) + 1
        assert by_cat["A.5"] == 37
        assert by_cat["A.6"] == 8
        assert by_cat["A.7"] == 14
        assert by_cat["A.8"] == 34


class TestCrossFrameworkMappings:
    def test_has_mappings(self):
        assert len(CROSS_MAPPINGS) >= 15

    def test_all_have_required_fields(self):
        for mapping in CROSS_MAPPINGS:
            assert "soc2" in mapping
            assert "iso" in mapping
            assert "type" in mapping
            assert "notes" in mapping

    def test_soc2_codes_exist_in_controls(self):
        soc2_codes = {c["code"] for c in SOC2_CONTROLS}
        for mapping in CROSS_MAPPINGS:
            assert mapping["soc2"] in soc2_codes, f"SOC 2 code {mapping['soc2']} not in controls"

    def test_iso_codes_exist_in_controls(self):
        iso_codes = {c["code"] for c in ISO27001_CONTROLS}
        for mapping in CROSS_MAPPINGS:
            assert mapping["iso"] in iso_codes, f"ISO code {mapping['iso']} not in controls"

    def test_mapping_types_are_valid(self):
        for mapping in CROSS_MAPPINGS:
            assert isinstance(mapping["type"], ControlMappingType)

    def test_all_mapping_types_used(self):
        types_used = {m["type"] for m in CROSS_MAPPINGS}
        assert ControlMappingType.EQUIVALENT in types_used
        assert ControlMappingType.PARTIAL in types_used
        assert ControlMappingType.RELATED in types_used

    def test_notes_not_empty(self):
        for mapping in CROSS_MAPPINGS:
            assert len(mapping["notes"]) > 10, f"Notes too short for {mapping['soc2']}->{mapping['iso']}"

    def test_no_exact_duplicate_mappings(self):
        pairs = [(m["soc2"], m["iso"]) for m in CROSS_MAPPINGS]
        assert len(pairs) == len(set(pairs)), "Duplicate SOC2->ISO mapping pair found"
