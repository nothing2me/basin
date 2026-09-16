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


def test_classify_drought_typology():
    from basin_core.summary import classify_drought_typology

    # Compound Spring-Summer Drought
    t1 = classify_drought_typology({
        "duration_days": 180,
        "onset_month": 4,
        "concurrence": 0.75,
        "max_dry_days": 42,
        "historical_percentile": 0.95,
    })
    assert t1["archetype"] == "Compound Spring-Summer Drought"
    assert "Synchronous" in t1["spatial_pattern"]
    assert "Critical Inflow" in t1["vulnerability"]
    assert t1["onset_name"] == "April"

    # Acute Flash Drought & Dry Run
    t2 = classify_drought_typology({
        "duration_days": 60,
        "onset_month": 7,
        "concurrence": 0.20,
        "max_dry_days": 38,
        "historical_percentile": 0.60,
    })
    assert t2["archetype"] == "Acute Flash Drought & Dry Run"
    assert "Localized" in t2["spatial_pattern"]
    assert t2["onset_name"] == "July"

    # Chronic Multi-Year Drought
    t3 = classify_drought_typology({
        "duration_days": 365,
        "onset_month": 10,
        "concurrence": 0.45,
        "max_dry_days": 20,
        "historical_percentile": 0.80,
    })
    assert t3["archetype"] == "Chronic Multi-Year Drought"
    assert "Regional Tributary Stress" in t3["spatial_pattern"]


def test_generate_scenario_interpretation_and_draft_note():
    from types import SimpleNamespace
    from basin_core.summary import generate_scenario_interpretation, draft_engineering_review_note

    fake_scenario = SimpleNamespace(
        id="B-001",
        features={
            "duration_days": 180,
            "onset_month": 4,
            "deficit_mm": 304.8,  # 12.0 inches
            "historical_percentile": 0.92,
            "concurrence": 0.75,
            "max_dry_days": 45,
            "benchmark_n": 30,
        }
    )

    interp = generate_scenario_interpretation(fake_scenario, workspace=None, use_llm=False)
    assert interp["typology"] == "Compound Spring-Summer Drought"
    assert "12.00-inch" in interp["narrative"] or "12.0" in interp["narrative"]
    assert "synchronous basin-wide inflow failure" in interp["narrative"].lower()
    assert "45 consecutive days" in interp["narrative"]
    assert "Choke Canyon" in interp["narrative"]
    assert "[Engineering Assessment]" in interp["draft_note"]
    assert "180-day window" in interp["draft_note"]
    assert "April onset" in interp["draft_note"]
    assert "92%" in interp["draft_note"]
    assert "75%" in interp["draft_note"]

    draft = draft_engineering_review_note(fake_scenario)
    assert "[Engineering Assessment]" in draft
    assert "45-day dry spell" in draft


def test_attach_scenario_ai_interpretations():
    from types import SimpleNamespace
    from basin_core.summary import attach_scenario_ai_interpretations

    s1 = SimpleNamespace(
        id="B-002",
        features={
            "duration_days": 90,
            "onset_month": 5,
            "deficit_mm": 150.0,
            "historical_percentile": 0.75,
            "concurrence": 0.50,
            "max_dry_days": 25,
            "benchmark_n": 20,
        }
    )
    attach_scenario_ai_interpretations([s1], workspace=None, use_llm=False)
    assert hasattr(s1, "ai_narrative") and len(s1.ai_narrative) > 50
    assert hasattr(s1, "ai_draft_note") and "[Engineering Assessment]" in s1.ai_draft_note
    assert hasattr(s1, "ai_typology") and s1.ai_typology

