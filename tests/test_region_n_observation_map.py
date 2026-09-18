"""Release checks for the Region N map that is rendered by the Data page."""
import pandas as pd

from basin_core.region_n_map import build_observation_map, load_catalog


def test_bundled_catalog_and_satellite_inventory_are_present():
    catalog = load_catalog()
    assert len(catalog["counties"]["features"]) == 11
    assert len(catalog["rain_stations"]) == 191
    assert len(catalog["water_stations"]) == 228
    assert len(catalog["streams"]["features"]) == catalog["sources"]["streams"]["feature_count"]
    assert len(catalog["lakes"]["features"]) == catalog["sources"]["lakes"]["feature_count"]
    assert len(catalog["basins"]["features"]) == catalog["sources"]["basins"]["feature_count"]


def test_default_map_is_satellite_and_distinguishes_loaded_sources():
    loaded = pd.DataFrame([
        {"station_id": "USW00012924", "name": "Corpus Christi", "latitude": 27.7839,
         "longitude": -97.5114, "is_custom": False},
    ])
    fig = build_observation_map(loaded)
    assert fig.layout.map.style == "white-bg"
    assert "/app/static/tiles/World_Imagery/" in fig.layout.map.layers[0].source[0]
    traces = {trace.name: trace for trace in fig.data}
    assert len(traces["NOAA rainfall stations"].lat) == len(load_catalog()["rain_stations"]) - 1
    assert len(traces["USGS water sites"].lat) == len(load_catalog()["water_stations"])
    assert len(traces["Loaded rainfall source"].lat) == 1


def test_observation_map_legend_font_and_emoji_mode():
    loaded = pd.DataFrame([
        {"station_id": "USW00012924", "name": "Corpus Christi", "latitude": 27.7839,
         "longitude": -97.5114, "is_custom": False},
    ])
    # Check default dots mode legend font
    fig_dots = build_observation_map(loaded)
    assert fig_dots.layout.legend.font.size >= 14
    assert fig_dots.layout.legend.itemsizing == "constant"
    traces_dots = {trace.name: trace for trace in fig_dots.data}

    # Check emoji mode
    fig_emoji = build_observation_map(loaded, marker_style="emoji")
    traces_emoji = {trace.name: trace for trace in fig_emoji.data}
    assert "🌧️ NOAA rainfall stations" in traces_emoji
    assert "💧 USGS water sites" in traces_emoji
    assert "🎯 Loaded rainfall source" in traces_emoji
    trace_pairs = (
        (traces_dots["NOAA rainfall stations"], traces_emoji["🌧️ NOAA rainfall stations"], "water"),
        (traces_dots["USGS water sites"], traces_emoji["💧 USGS water sites"], "drinking-water"),
        (traces_dots["Loaded rainfall source"], traces_emoji["🎯 Loaded rainfall source"], "star"),
    )
    for dot_trace, emoji_trace, symbol in trace_pairs:
        assert emoji_trace.mode == "markers"
        assert emoji_trace.marker.symbol == symbol
        assert emoji_trace.marker.allowoverlap is True
        assert list(emoji_trace.lon) == list(dot_trace.lon)
        assert list(emoji_trace.lat) == list(dot_trace.lat)
        assert list(emoji_trace.text) == list(dot_trace.text)


def test_emoji_mode_does_not_mutate_colored_marker_data():
    loaded = pd.DataFrame([
        {"station_id": "USW00012924", "name": "Corpus Christi", "latitude": 27.7839,
         "longitude": -97.5114, "is_custom": False},
    ])
    custom = {"rain_stations": "#00ff00", "water_stations": "#ff00ff", "loaded_source": "#123456"}
    dots_before = build_observation_map(loaded, marker_style="dots", custom_colors=custom)
    colors_before = {trace.name: trace.marker.color for trace in dots_before.data}

    emojis = build_observation_map(loaded, marker_style="emoji", custom_colors=custom)
    dots_after = build_observation_map(loaded, marker_style="dots", custom_colors=custom)

    assert emojis is not dots_before
    assert {trace.name: trace.marker.color for trace in dots_after.data} == colors_before


def test_observation_map_custom_colors():
    loaded = pd.DataFrame([
        {"station_id": "USW00012924", "name": "Corpus Christi", "latitude": 27.7839,
         "longitude": -97.5114, "is_custom": False},
    ])
    custom = {"rain_stations": "#00ff00", "water_stations": "#ff00ff"}
    fig = build_observation_map(loaded, custom_colors=custom)
    traces = {trace.name: trace for trace in fig.data}
    assert traces["NOAA rainfall stations"].marker.color == "#00ff00"
    assert traces["USGS water sites"].marker.color == "#ff00ff"
