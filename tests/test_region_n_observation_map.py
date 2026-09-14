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
