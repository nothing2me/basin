from datetime import date
import pytest
from basin_core.uploads import preview_rainfall
from basin_core.rainfall_comparison import compare_rainfall


def sample():
    return preview_rainfall(b"date,precipitation\n2024-01-01,1\n2024-01-02,\n2024-01-04,3", "Local", "Town", "inches")


def test_only_paired_days_contribute_to_both_totals():
    result = compare_rainfall(sample(), {date(2024,1,1): 10, date(2024,1,2): 900, date(2024,1,3): 800, date(2024,1,4): 20}, relationship="regional_proxy", daily_basis_confirmed=True)
    assert len(result.rows) == 4
    assert result.paired_days == 2
    assert result.upload_total_mm == pytest.approx(101.6)
    assert result.reference_total_mm == 30
    assert result.difference_mm == pytest.approx(71.6)
    assert result.relative_difference_pct == pytest.approx(100*71.6/30)


def test_zero_reference_has_no_relative_difference():
    r = compare_rainfall(sample(), {date(2024,1,1): 0}, relationship="same_station", daily_basis_confirmed=True)
    assert r.relative_difference_pct is None
    assert r.paired_days == 1


@pytest.mark.parametrize("relation,confirmed", [("unknown", True), ("regional_proxy", False)])
def test_requires_review(relation, confirmed):
    with pytest.raises(ValueError):
        compare_rainfall(sample(), {}, relationship=relation, daily_basis_confirmed=confirmed)


def test_no_overlap_is_blocked():
    with pytest.raises(ValueError, match="No dates"):
        compare_rainfall(sample(), {date(2025,1,1): 5}, relationship="regional_proxy", daily_basis_confirmed=True)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_bad_reference_is_rejected(value):
    with pytest.raises(ValueError, match="invalid rainfall"):
        compare_rainfall(sample(), {date(2024,1,1): value}, relationship="regional_proxy", daily_basis_confirmed=True)
