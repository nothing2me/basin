"""Satellite observation map with a bundled, sourced Region N catalog.

Map metadata is separate from the analysis source. Building a figure never
downloads observations; only the browser requests the satellite imagery tiles.
"""
from __future__ import annotations

from functools import lru_cache
import gzip
from html import escape
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

CATALOG_FILE = Path(__file__).resolve().parents[1] / "assets/region_n_map.json.gz"
OFFLINE_TILES_DIR = Path(__file__).resolve().parents[1] / "static/tiles/World_Imagery"
OFFLINE_IMAGERY_URL = "/app/static/tiles/World_Imagery/{z}/{y}/{x}.jpg"
IMAGERY_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
LAYER_LABELS = {
    "rain_stations": "NOAA rainfall stations",
    "water_stations": "USGS water sites",
    "basins": "HUC8 subbasin boundaries",
    "counties": "County boundaries",
    "streams": "Streams and channels (detailed hydrography)",
    "lakes": "Lakes, ponds and reservoirs (detailed hydrography)",
}
DEFAULT_FAST_LAYERS = ["counties", "basins", "rain_stations", "water_stations"]
COLORS = {"rain_stations": "#f9e44b", "water_stations": "#fc83d0",
          "streams": "#53d9ff", "lakes": "#47aaff", "basins": "#e3abff", "counties": "#ffffff"}


@lru_cache(maxsize=1)
def load_catalog():
    with gzip.open(CATALOG_FILE, "rt", encoding="utf-8") as handle:
        catalog = json.load(handle)
    if catalog.get("schema_version") != "1.0":
        raise ValueError("Unsupported Region N map catalog")
    return catalog


def _properties(feature):
    return {key.lower(): value for key, value in feature["properties"].items()}


def _points(geometry):
    def flatten(coords):
        if coords and isinstance(coords[0], (float, int)):
            yield coords
        else:
            for child in coords:
                yield from flatten(child)
    return list(flatten(geometry["coordinates"]))


def _location(feature):
    points = _points(feature["geometry"])
    # A location for zooming, not an asserted hydrologic centroid.
    return points[len(points) // 2][:2]


@lru_cache(maxsize=1)
def search_catalog():
    catalog = load_catalog()
    entries = []
    for key in ("rain_stations", "water_stations"):
        for station in catalog[key]:
            entries.append({"label": f"{station['name']} · {station['station_id']} · {station['network']}",
                            "lon": station["longitude"], "lat": station["latitude"], "layer": key,
                            "details": station["variable"], "source_url": station["source_url"]})
    for key in ("streams", "lakes", "basins", "counties"):
        seen = set()
        for feature in catalog[key]["features"]:
            props = _properties(feature)
            name = props.get("gnis_name") or props.get("name")
            if not name or name in seen:
                continue
            seen.add(name)
            lon, lat = _location(feature)
            identity = props.get("huc8") or props.get("permanent_identifier") or ""
            entries.append({"label": f"{name} · {LAYER_LABELS[key]}", "lon": lon, "lat": lat,
                            "layer": key, "details": f"{name} · {identity}",
                            "source_url": catalog["sources"][key]["url"]})
    return sorted(entries, key=lambda entry: entry["label"].casefold())


@lru_cache(maxsize=6)
def _geometry_layer(key):
    # Retain complete attributes in the catalog, but send only geometry to the
    # renderer. No features are dropped, even if unnamed or historical.
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": f["geometry"], "properties": {}}
        for f in load_catalog()[key]["features"]]}


def _station_trace(rows, name, color, size):
    hover = []
    for row in rows:
        period = (f"PRCP inventory: {row['first_year']}–{row['last_year']}<br>"
                  if "first_year" in row else "")
        hover.append(f"<b>{escape(str(row['name']))}</b><br>{escape(str(row['station_id']))}<br>"
                     f"{escape(row.get('variable', 'Rainfall'))}<br>{period}"
                     f"{escape(row.get('map_role', 'Map catalog only; observations not loaded'))}")
    return go.Scattermap(lon=[r["longitude"] for r in rows], lat=[r["latitude"] for r in rows],
                         text=hover, mode="markers", name=name, marker=dict(color=color, size=size),
                         hovertemplate="%{text}<br>%{lat:.4f}, %{lon:.4f}<extra></extra>")


_BASE_MAP_CACHE: dict[tuple, Any] = {}


def build_observation_map(stations_df, *, layers=None, focus=None, use_offline=True):
    source_rows = stations_df.to_dict("records") if not stations_df.empty else []
    has_custom = any(r.get("is_custom") for r in source_rows)
    layers_tuple = tuple(sorted(LAYER_LABELS if layers is None else layers))
    station_ids = tuple(sorted(r["station_id"] for r in source_rows if not r.get("is_custom", False)))

    if not has_custom and focus is None:
        cache_key = (station_ids, layers_tuple, use_offline)
        if cache_key in _BASE_MAP_CACHE:
            return _BASE_MAP_CACHE[cache_key]

    catalog = load_catalog()
    layers = set(LAYER_LABELS if layers is None else layers)
    imagery_source = OFFLINE_IMAGERY_URL if (use_offline and OFFLINE_TILES_DIR.exists()) else IMAGERY_URL
    attribution = (
        "Tiles © Esri (Bundled Region N Satellite Cache)"
        if imagery_source == OFFLINE_IMAGERY_URL
        else "Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community"
    )
    raster_layer = dict(
        below="traces",
        sourcetype="raster",
        source=[imagery_source],
        sourceattribution=attribution,
    )
    if imagery_source == OFFLINE_IMAGERY_URL:
        raster_layer["minzoom"] = 6
        raster_layer["maxzoom"] = 11
    map_layers = [raster_layer]
    for key in ("lakes", "streams", "basins", "counties"):
        if key not in layers:
            continue
        map_layers.append(dict(below="traces", sourcetype="geojson", source=_geometry_layer(key),
                               type="fill" if key == "lakes" else "line", color=COLORS[key],
                               opacity={"lakes": .38, "streams": .4, "basins": .7, "counties": .5}[key],
                               line=dict(width=1.5 if key == "basins" else .6)))
    map_layers.append(dict(below="traces", sourcetype="geojson", source=_geometry_layer("region"),
                           type="line", color="#ffac47", line=dict(width=3)))
    fig = go.Figure()
    source_rows = stations_df.to_dict("records") if not stations_df.empty else []
    source_ids = {r["station_id"] for r in source_rows if not r.get("is_custom", False)}
    for key in ("rain_stations", "water_stations"):
        if key in layers:
            rows = [r for r in catalog[key] if key != "rain_stations" or r["station_id"] not in source_ids]
            fig.add_trace(_station_trace(rows, LAYER_LABELS[key], COLORS[key], 7 if key == "rain_stations" else 9))
    for custom in (False, True):
        rows = [dict(r, map_role="User-entered analysis source" if custom else "Loaded rainfall analysis source")
                for r in source_rows if bool(r.get("is_custom", False)) == custom]
        if rows:
            fig.add_trace(_station_trace(rows, "User-entered source" if custom else "Loaded rainfall source",
                                         "#ffac47" if custom else "#ffffff", 16))
    if focus:
        fig.add_trace(go.Scattermap(lon=[focus["lon"]], lat=[focus["lat"]], mode="markers+text",
                                   marker=dict(size=22, color="#ff654f", opacity=.8),
                                   text=[escape(focus["label"])], textposition="top right",
                                   textfont=dict(color="white", size=13), name="Located feature",
                                   hovertemplate="%{text}<extra></extra>"))
    if not fig.data:
        fig.add_trace(go.Scattermap(lon=[None], lat=[None], showlegend=False))
    west, south, east, north = catalog["bounds"]
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=0, b=0),
                      map=dict(style="white-bg", layers=map_layers,
                               center=dict(lon=focus["lon"] if focus else (west + east) / 2,
                                           lat=focus["lat"] if focus else (south + north) / 2),
                               zoom=9 if focus else 7),
                      uirevision="region-n-" + (focus["label"] if focus else "overview"),
                      legend=dict(orientation="h", y=-.02, x=0, font=dict(size=12)),
                      paper_bgcolor="rgba(0,0,0,0)")
    if not has_custom and focus is None:
        cache_key = (station_ids, layers_tuple, use_offline)
        _BASE_MAP_CACHE[cache_key] = fig
    return fig


def render_observation_map(stations_df, *, show_catalog=False):
    import streamlit as st
    st.markdown("**Region N observation map**")
    try:
        catalog = load_catalog()
    except (OSError, ValueError) as error:
        st.error(f"The bundled Region N map catalog could not be loaded: {error}")
        return
    st.caption("Offline satellite imagery · Orange outline: Region N's 11 counties. "
               "Geographic layers show mapped features, not current water levels or streamflow.")

    layers = st.multiselect(
        "Visible map layers",
        list(LAYER_LABELS),
        default=DEFAULT_FAST_LAYERS,
        format_func=LAYER_LABELS.get,
        key="observation_map_layers",
    )
    entries = search_catalog()
    selected = st.selectbox("Find a station, county, stream, lake or subbasin", range(len(entries)),
                            index=None, placeholder="Search by name or station ID…",
                            format_func=lambda i: entries[i]["label"], key="observation_map_search")
    focus = entries[selected] if selected is not None else None
    if focus and focus["layer"] not in layers:
        layers = [*layers, focus["layer"]]
        st.caption(f"Showing {LAYER_LABELS[focus['layer']]} for the selected search result.")
    st.plotly_chart(build_observation_map(stations_df, layers=layers, focus=focus, use_offline=True), width="stretch",
                    theme=None, config={"displayModeBar": True, "scrollZoom": True})
    st.caption("Cyan lines: streams/channels · Blue fill: lakes/ponds · Purple lines: HUC8 subbasins · "
               "White lines: counties · Orange outline: Region N")
    if focus:
        st.caption(f"{focus['details']} · [Open source]({focus['source_url']})")
    st.caption(f"{len(catalog['rain_stations']):,} NOAA rainfall stations · "
               f"{len(catalog['water_stations']):,} USGS water sites · "
               f"{len(catalog['streams']['features']):,} stream/channel segments · "
               f"{len(catalog['lakes']['features']):,} lakes/ponds/reservoirs · "
               f"{len(catalog['basins']['features'])} HUC8 subbasins.")

    if show_catalog:
        with st.expander("Map station catalog and sources"):
            st.caption(f"Catalog retrieved {catalog['retrieved_at'][:10]}. "
                       "Coverage: all NOAA GHCN-Daily precipitation inventory stations and USGS NWIS "
                       "stream, lake/reservoir and estuary sites inside the TWDB Region N boundary.")
            table = pd.DataFrame(catalog["rain_stations"] + catalog["water_stations"])
            st.dataframe(table, hide_index=True, width="stretch", column_config={
                "source_url": st.column_config.LinkColumn("Source"),
                "first_year": st.column_config.NumberColumn("First inventory year", format="%d"),
                "last_year": st.column_config.NumberColumn("Last inventory year", format="%d")})
            st.download_button("Download map station catalog (CSV)", table.to_csv(index=False),
                               file_name="region_n_map_stations.csv", mime="text/csv")
            for key, source in catalog["sources"].items():
                st.markdown(f"- [{LAYER_LABELS.get(key, 'Region N boundary')}]({source['url']})")
            provenance = {key: catalog[key] for key in ("schema_version", "retrieved_at", "scope", "county_names", "sources")}
            st.download_button("Download map provenance (JSON)", json.dumps(provenance, indent=2),
                               file_name="region_n_map_sources.json", mime="application/json")
