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
    assert "exceptionally rare" in text
    assert "multi-basin supply stress" in text
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
    assert "typical historical variation" in text


def test_reservoir_summary_breached():
    df = pd.DataFrame({
        "day": [1, 2, 3],
        "combined_pct": [35.0, 25.0, 18.0],
    })
    text = reservoir_summary(df, "Test Lake", critical_pct=20.0)
    assert "Test Lake" in text
    assert "Day 3" in text
    assert "emergency band" in text


def test_reservoir_summary_safe():
    df = pd.DataFrame({
        "day": [1, 2, 3],
        "combined_pct": [80.0, 78.0, 76.0],
    })
    text = reservoir_summary(df, "Farm Pond")
    assert "remains above Stage 1" in text
