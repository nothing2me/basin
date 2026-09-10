"""Test the baked-in offline vector GIS map and optional satellite mode."""
import socket
import pandas as pd
import pytest

from basin_core.geo_map import build_basin_map, load_texas_vector_data


@pytest.fixture
def sample_stations():
    return pd.DataFrame([
        {
            "station_id": "USW00012924",
            "name": "Corpus Christi",
            "latitude": 27.7839,
            "longitude": -97.5114,
            "is_custom": False,
        },
        {
            "station_id": "USW00012912",
            "name": "Victoria Rgnl Ap",
            "latitude": 28.8625,
            "longitude": -96.9300,
            "is_custom": False,
        },
        {
            "station_id": "USW00012921",
            "name": "San Antonio Intl Ap",
            "latitude": 29.5442,
            "longitude": -98.4839,
            "is_custom": False,
        },
    ])


def test_baked_in_vector_map_loads_100pct_offline(sample_stations, monkeypatch):
    """Ensure that map generation strictly makes zero network connections."""
    def no_network(*args, **kwargs):
        raise AssertionError("Map attempted a network connection during offline generation")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)

    fig = build_basin_map(sample_stations, use_satellite=False)
    assert fig is not None
    assert len(fig.data) >= 8  # state, counties, 4 rivers, 3 reservoirs, halo, stations

    # Verify key layer names are present
    trace_names = [t.name for t in fig.data if getattr(t, "name", None)]
    assert "Texas Coast & Border" in trace_names
    assert "County Boundaries" in trace_names
    assert "Nueces River" in trace_names
    assert "Lake Corpus Christi" in trace_names
    assert "Choke Canyon Reservoir" in trace_names

    # Verify annotations for cartography
    texts = [a.text for a in fig.layout.annotations if getattr(a, "text", None)]
    assert any("Gulf of Mexico" in t for t in texts)
    assert any("▲ N" in t for t in texts)
    assert any("50 mi" in t for t in texts)


def test_custom_stations_rendered_with_distinct_symbols(sample_stations):
    custom_row = pd.DataFrame([{
        "station_id": "CUST_ROBSTOWN",
        "name": "Robstown Municipal Farm Gauge",
        "latitude": 27.8000,
        "longitude": -97.6500,
        "is_custom": True,
    }])
    df = pd.concat([sample_stations, custom_row], ignore_index=True)

    fig = build_basin_map(df, use_satellite=False)
    trace_names = [t.name for t in fig.data if getattr(t, "name", None)]
    assert "NOAA Benchmark Stations" in trace_names
    assert "Custom Uploaded Gauges" in trace_names

    custom_trace = next(t for t in fig.data if t.name == "Custom Uploaded Gauges")
    assert custom_trace.marker.symbol == "diamond"
    assert custom_trace.marker.color == "#F59E0B"


def test_satellite_mode_configuration(sample_stations):
    fig = build_basin_map(sample_stations, use_satellite=True)
    assert hasattr(fig.layout, "map")
    assert fig.layout.map.layers is not None
    assert "arcgisonline.com" in fig.layout.map.layers[0]["source"][0]


def test_vector_data_caching():
    data1 = load_texas_vector_data()
    data2 = load_texas_vector_data()
    assert data1 is data2  # LRU cache returns identical object reference
    assert len(data1["state_x"]) > 100
    assert len(data1["county_x"]) > 1000