import pandas as pd
from basin_core.summary import scenario_summary, reservoir_summary


def test_scenario_summary_severe():
    features = {
        "duration_days": 180,
        "deficit_mm": 240.5,
        "historical_percentile": 0.96,
        "concurrence": 0.45,
        "benchmark_n": 25,
        "beyond_rainfall_reference": True,
        "max_dry_days": 42,
    }
    text = scenario_summary(features)
    assert "180-day scenario" in text
    assert "240.5 mm" in text
    assert "96%" in text
    assert "sample comparison, not a drought probability" in text
    assert "does not establish basin-wide water-supply conditions" in text
    assert "42 days" in text


def test_scenario_summary_moderate():
    features = {
        "duration_days": 90,
        "deficit_mm": 60.0,
        "historical_percentile": 0.50,
        "concurrence": 0.10,
        "benchmark_n": 30,
        "beyond_rainfall_reference": False,
        "max_dry_days": 12,
    }
    text = scenario_summary(features)
    assert "90-day scenario" in text
    assert "50%" in text
    assert "historical comparison windows" in text


def test_scenario_summary_small_sample_does_not_claim_rarity():
    text = scenario_summary({
        "duration_days": 30,
        "deficit_mm": 20.0,
        "historical_percentile": 1.0,
        "concurrence": 0.0,
        "benchmark_n": 2,
        "eligible_concurrence_days": 0,
    })
    assert "small sample does not support a rarity claim" in text
    assert "No eligible 30-day windows" in text


def test_reservoir_summary_breached():
    df = pd.DataFrame({
        "day": [1, 2, 3],
        "combined_pct": [35.0, 25.0, 18.0],
    })
    text = reservoir_summary(df, "Test Lake", critical_pct=20.0)
    assert "Test Lake" in text
    assert "Day 3" in text
    assert "illustrative" in text
    assert "no operational action" in text.lower()


def test_reservoir_summary_safe():
    df = pd.DataFrame({
        "day": [1, 2, 3],
        "combined_pct": [80.0, 78.0, 76.0],
    })
    text = reservoir_summary(df, "Farm Pond")
    assert "above all illustrative bands" in text


def test_reservoir_summary_reports_day_zero():
    df = pd.DataFrame({"day": [1], "combined_pct": [18.0]})
    text = reservoir_summary(df, initial_pct=.20)
    assert "Day 0" in text
