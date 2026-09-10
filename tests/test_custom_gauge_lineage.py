import numpy as np
import pandas as pd
import pytest

from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams, ScenarioGenerator
from basin_core.workspace import Workspace


@pytest.fixture
def base_source():
    return CachedSource()


def test_station_id_collision(base_source):
    """Custom gauge should not silently overwrite an authoritative NOAA station ID."""
    dates = pd.date_range("2021-01-01", "2021-12-31")
    custom_series = pd.Series(2.0, index=dates)
    noaa_id = base_source.manifest["stations"][0]["id"]
    
    # Passing an existing NOAA ID must raise a ValueError rather than corrupting reference data
    with pytest.raises(ValueError, match="already exists|collision|reference station"):
        base_source.with_custom_station(noaa_id, "Duplicate Station", custom_series)


def test_malformed_and_invalid_data(base_source):
    """Invalid types, empty IDs, negative values, and non-finite values must be rejected."""
    dates = pd.date_range("2021-01-01", "2021-01-10")
    
    # Empty or whitespace ID
    with pytest.raises(ValueError):
        base_source.with_custom_station("", "Valid Name", pd.Series(1.0, index=dates))
    with pytest.raises(ValueError):
        base_source.with_custom_station("   ", "Valid Name", pd.Series(1.0, index=dates))
        
    # Non-Series data
    with pytest.raises(ValueError):
        base_source.with_custom_station("CUST1", "Valid Name", [1.0, 2.0])
        
    # Negative precipitation
    neg_series = pd.Series([1.0, -0.5, 2.0], index=dates[:3])
    with pytest.raises(ValueError, match="negative|nonnegative|Invalid precipitation"):
        base_source.with_custom_station("CUST1", "Valid Name", neg_series)
        
    # Non-finite precipitation (inf / -inf)
    inf_series = pd.Series([1.0, np.inf, 2.0], index=dates[:3])
    with pytest.raises(ValueError, match="finite|Invalid precipitation"):
        base_source.with_custom_station("CUST1", "Valid Name", inf_series)


def test_dates_completely_out_of_public_period(base_source):
    """Data entirely outside the 1991-2025 public period cannot supply observations."""
    out_dates = pd.date_range("1980-01-01", "1980-12-31")
    custom_series = pd.Series(5.0, index=out_dates)
    
    with pytest.raises(ValueError, match="No overlapping dates|outside the declared period|overlap"):
        base_source.with_custom_station("PAST_GAUGE", "Past Gauge", custom_series)


def test_duplicate_dates_validation(base_source):
    """Duplicate dates in custom series must be handled explicitly or rejected if conflicting."""
    dup_dates = pd.to_datetime(["2021-01-01", "2021-01-01", "2021-01-02"])
    
    # Identical duplicates
    same_val = pd.Series([1.0, 1.0, 2.0], index=dup_dates)
    aug1 = base_source.with_custom_station("DUP1", "Dup 1", same_val)
    assert aug1.daily.loc["2021-01-01", "DUP1"] == 1.0
    
    # Conflicting duplicates for the same timestamp should be rejected
    conflicting_val = pd.Series([1.0, 10.0, 2.0], index=dup_dates)
    with pytest.raises(ValueError, match="Duplicate|conflicting"):
        base_source.with_custom_station("DUP2", "Dup 2", conflicting_val)


def test_short_record_scenario_rejection(base_source):
    """Custom gauge with record shorter than requested duration must raise ValueError."""
    short_dates = pd.date_range("2021-01-01", "2021-02-01") # 32 days
    short_series = pd.Series(1.0, index=short_dates)
    aug_source = base_source.with_custom_station("SHORT_GAUGE", "Short Gauge", short_series)
    
    # Requesting 90-day scenarios when only 32 days exist must fail cleanly
    params = ScenarioParams(stations=("SHORT_GAUGE",), durations=(90,), candidates=10)
    gen = ScenarioGenerator(aug_source, params)
    with pytest.raises(ValueError, match="No complete, season-matched windows"):
        gen.generate()


def test_custom_gauge_session_save_and_reload(base_source, tmp_path):
    """Verify that a workspace generated with an activated custom gauge saves and reloads."""
    dates = pd.date_range("2020-01-01", "2022-12-31")
    custom_series = pd.Series(1.5, index=dates)
    aug_source = base_source.with_custom_station("FARM_GAUGE", "Farm Rain Gauge", custom_series)
    
    params = ScenarioParams(stations=("FARM_GAUGE",), durations=(90,), months=(1, 4), candidates=10, seed=42)
    workspace = Workspace(aug_source, params, size=3)
    assert len(workspace.scenarios) == 10
    assert workspace.reference.stations == ["FARM_GAUGE"]
    
    # Save the session
    session_file = workspace.save(tmp_path)
    assert session_file.exists()
    
    # Attempt reload with the aug_source
    reloaded = Workspace.load(aug_source, session_file)
    assert reloaded.id == workspace.id
    assert reloaded.reference.stations == ["FARM_GAUGE"]
    assert len(reloaded.scenarios) == len(workspace.scenarios)

    # Attempt reload with the unaugmented base_source must fail with clear message
    with pytest.raises(ValueError, match="absent from source snapshot: FARM_GAUGE"):
        Workspace.load(base_source, session_file)


def test_custom_gauge_scenario_edit_invalidates_approval(base_source):
    """Proves that changing rainfall on a custom-gauge scenario marks approvals stale."""
    dates = pd.date_range("2020-01-01", "2022-12-31")
    custom_series = pd.Series(1.5, index=dates)
    aug_source = base_source.with_custom_station("IRRIGATION_GAUGE", "Irrigation Gauge", custom_series)
    
    params = ScenarioParams(stations=("IRRIGATION_GAUGE",), durations=(90,), months=(1, 4), candidates=10, seed=42)
    workspace = Workspace(aug_source, params, size=3)
    target_id = workspace.selected[0]
    scenario = workspace.get(target_id)
    
    # Review and accept scenario
    scenario.review(True, "Custom gauge rainfall reviewed and accepted")
    assert scenario.status == "accepted"
    assert scenario.approved_revision == 1
    
    # Edit rainfall factor
    workspace.edit(target_id, "Scale down custom rainfall", factor=0.75)
    updated_scenario = workspace.get(target_id)
    
    # Approval must be invalidated
    assert updated_scenario.revision == 2
    assert updated_scenario.status == "unreviewed"
    assert updated_scenario.approved_revision is None
