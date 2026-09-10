"""Baked-in offline vector GIS map and optional satellite overlay for BASIN.

Provides:
- 100% offline Texas vector basemap: Texas state boundary, Gulf Coast, all county boundaries.
- South Texas hydrological features: Nueces River, Frio River, San Antonio River,
  Lake Corpus Christi, Choke Canyon Reservoir, Corpus Christi Bay, and Nueces Bay.
- Station radar target markers with glowing halos, airport/gauge classifications, and rich metadata.
- Cartographic scale bar, North arrow, and geographically true aspect ratio.
- Optional high-resolution satellite imagery overlay for online sessions.
"""
from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from basin_theme import accessible_chart

ROOT_DIR = Path(__file__).resolve().parents[1]
GEO_FILE = ROOT_DIR / "assets" / "texas_geo.json"


@functools.lru_cache(maxsize=1)
def load_texas_vector_data() -> dict[str, Any]:
    """Load and parse the baked-in Texas vector geometries from assets."""
    if not GEO_FILE.exists():
        return {"state_x": [], "state_y": [], "county_x": [], "county_y": []}

    with open(GEO_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 1. Texas state boundary and coastline
    state_x: list[float | None] = []
    state_y: list[float | None] = []
    state_features = raw.get("state", {}).get("features", [])
    if state_features:
        for poly in state_features[0].get("geometry", {}).get("coordinates", []):
            for pt in poly:
                state_x.append(round(pt[0], 3))
                state_y.append(round(pt[1], 3))
            state_x.append(None)
            state_y.append(None)

    # 2. All Texas county boundary lines (single line trace with None delimiters)
    county_x: list[float | None] = []
    county_y: list[float | None] = []
    for f_c in raw.get("counties", []):
        geom = f_c.get("geometry", {})
        coords = geom.get("coordinates", [])
        if geom.get("type") == "Polygon":
            coords = [coords]
        for poly in coords:
            for ring in poly:
                for pt in ring:
                    county_x.append(round(pt[0], 3))
                    county_y.append(round(pt[1], 3))
                county_x.append(None)
                county_y.append(None)

    return {
        "state_x": state_x,
        "state_y": state_y,
        "county_x": county_x,
        "county_y": county_y,
    }


# ---------------------------------------------------------------------------
# South Texas / Region N Hydrological System Polygons & Centerlines
# ---------------------------------------------------------------------------

RESERVOIRS = [
    {
        "name": "Lake Corpus Christi",
        "details": "Wesley E. Seale Dam (Mathis, TX) · Capacity: 257,300 ac-ft · Primary Municipal Supply",
        "lon": [-97.94, -97.91, -97.87, -97.84, -97.86, -97.89, -97.93, -97.94],
        "lat": [28.08, 28.14, 28.17, 28.13, 28.04, 28.02, 28.05, 28.08],
    },
    {
        "name": "Choke Canyon Reservoir",
        "details": "Choke Canyon Dam (Three Rivers, TX) · Capacity: 662,600 ac-ft · Regional Long-term Storage",
        "lon": [-98.42, -98.34, -98.24, -98.17, -98.19, -98.27, -98.38, -98.42],
        "lat": [28.49, 28.53, 28.52, 28.47, 28.43, 28.42, 28.46, 28.49],
    },
    {
        "name": "Corpus Christi & Nueces Bay",
        "details": "Nueces Estuary & Coastal Outfall · Gulf of Mexico Maritime Exchange",
        "lon": [-97.55, -97.42, -97.33, -97.20, -97.26, -97.40, -97.49, -97.55],
        "lat": [27.86, 27.89, 27.87, 27.83, 27.71, 27.73, 27.79, 27.86],
    },
]

RIVERS = [
    {
        "name": "Nueces River",
        "coords": [
            (-99.95, 29.35), (-99.70, 29.10), (-99.40, 28.75), (-99.10, 28.45),
            (-98.60, 28.32), (-98.20, 28.46), (-97.90, 28.05), (-97.50, 27.86)
        ],
    },
    {
        "name": "Frio River",
        "coords": [
            (-99.75, 29.70), (-99.50, 29.25), (-99.15, 28.85), (-98.70, 28.55),
            (-98.25, 28.47)
        ],
    },
    {
        "name": "San Antonio River",
        "coords": [
            (-98.50, 29.45), (-98.25, 29.20), (-97.90, 28.90), (-97.45, 28.65),
            (-96.85, 28.35)
        ],
    },
    {
        "name": "Guadalupe River",
        "coords": [
            (-98.15, 29.75), (-97.95, 29.55), (-97.35, 29.05), (-96.95, 28.82),
            (-96.80, 28.40)
        ],
    },
]


def build_basin_map(stations_df: pd.DataFrame, use_satellite: bool = False) -> go.Figure:
    """Render station locations on an authentic baked-in GIS map or optional satellite layer."""
    if use_satellite:
        center_lat = float(stations_df["latitude"].mean()) if not stations_df.empty else 28.7
        center_lon = float(stations_df["longitude"].mean()) if not stations_df.empty else -97.8

        fig = go.Figure(go.Scattermap(
            lat=stations_df["latitude"],
            lon=stations_df["longitude"],
            mode="markers+text",
            text=stations_df["name"],
            textposition="top right",
            customdata=stations_df["station_id"],
            marker=dict(size=14, color="#00E5FF"),
            textfont=dict(size=11, color="#FFFFFF"),
            hovertemplate="<b>%{text}</b><br>Station: %{customdata}<br>Lat: %{lat:.4f}, Lon: %{lon:.4f}<extra></extra>"
        ))
        fig.update_layout(
            height=440,
            margin=dict(l=10, r=10, t=35, b=10),
            title=dict(text="Station locations · High-resolution satellite imagery (Online)", font=dict(size=14)),
            map=dict(
                style="white-bg",
                layers=[{
                    "below": "traces",
                    "sourcetype": "raster",
                    "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
                }],
                center=dict(lat=center_lat, lon=center_lon),
                zoom=6.6,
            ),
            paper_bgcolor="rgba(0,0,0,0)"
        )
        return accessible_chart(fig)

    # ---------------------------------------------------------------------------
    # Baked-in Vector GIS Map (100% Offline, Zero Cloud Calls, Zero Tile Servers)
    # ---------------------------------------------------------------------------
    geo = load_texas_vector_data()
    fig = go.Figure()

    # 1. Texas Landmass Base Polygon (Slate land vs Navy Gulf of Mexico ocean)
    if geo["state_x"]:
        fig.add_trace(go.Scatter(
            x=geo["state_x"],
            y=geo["state_y"],
            mode="lines",
            fill="toself",
            fillcolor="#162032",
            line=dict(color="#0ea5e9", width=2.0),
            name="Texas Coast & Border",
            hoverinfo="skip",
            showlegend=False,
        ))

    # 2. Texas County Boundaries (Subtle administrative lines)
    if geo["county_x"]:
        fig.add_trace(go.Scatter(
            x=geo["county_x"],
            y=geo["county_y"],
            mode="lines",
            line=dict(color="#2a3b53", width=1.0),
            name="County Boundaries",
            hoverinfo="skip",
            showlegend=False,
        ))

    # 3. Major River Channels (Nueces, Frio, San Antonio, Guadalupe)
    for river in RIVERS:
        rx = [pt[0] for pt in river["coords"]]
        ry = [pt[1] for pt in river["coords"]]
        fig.add_trace(go.Scatter(
            x=rx,
            y=ry,
            mode="lines",
            line=dict(color="#0284c7", width=2.2),
            name=river["name"],
            hovertemplate=f"<b>{river['name']}</b><extra>River Basin Channel</extra>",
            showlegend=False,
        ))

    # 4. Critical Water Supply Reservoirs & Bays (Lake Corpus Christi, Choke Canyon, Corpus Bay)
    for res in RESERVOIRS:
        fig.add_trace(go.Scatter(
            x=res["lon"],
            y=res["lat"],
            mode="lines",
            fill="toself",
            fillcolor="#0284c7",
            line=dict(color="#38bdf8", width=1.8),
            name=res["name"],
            hovertemplate=f"<b>{res['name']}</b><br>{res['details']}<extra>Water Storage Reservoir</extra>",
            showlegend=False,
        ))

    # 5. Station Halo / Pulse Rings (Visual radar target styling)
    fig.add_trace(go.Scatter(
        x=stations_df["longitude"],
        y=stations_df["latitude"],
        mode="markers",
        marker=dict(size=26, color="rgba(0, 229, 255, 0.18)", line=dict(width=1.5, color="rgba(0, 229, 255, 0.45)")),
        hoverinfo="skip",
        showlegend=False,
    ))

    # 6. Active Weather Observation Stations
    is_custom = stations_df.get("is_custom", pd.Series(False, index=stations_df.index))
    custom_mask = is_custom.to_numpy(dtype=bool) if not stations_df.empty else np.array([])
    has_custom = custom_mask.any() if len(custom_mask) > 0 else False

    if has_custom:
        noaa_df = stations_df[~custom_mask]
        cust_df = stations_df[custom_mask]

        if not noaa_df.empty:
            fig.add_trace(go.Scatter(
                x=noaa_df["longitude"],
                y=noaa_df["latitude"],
                mode="markers+text",
                name="NOAA Benchmark Stations",
                text=noaa_df["name"],
                textposition="top right",
                customdata=noaa_df["station_id"],
                marker=dict(size=13, color="#00E5FF", line=dict(width=2, color="#0369a1"), symbol="circle"),
                textfont=dict(size=11, color="#f8fafc"),
                hovertemplate="<b>%{text}</b><br>NOAA Station: %{customdata}<br>Lat: %{y:.4f}, Lon: %{x:.4f}<extra>NOAA Baseline Station</extra>",
            ))

        if not cust_df.empty:
            fig.add_trace(go.Scatter(
                x=cust_df["longitude"],
                y=cust_df["latitude"],
                mode="markers+text",
                name="Custom Uploaded Gauges",
                text=cust_df["name"],
                textposition="top right",
                customdata=cust_df["station_id"],
                marker=dict(size=14, color="#F59E0B", line=dict(width=2, color="#B45309"), symbol="diamond"),
                textfont=dict(size=11, color="#FBBF24"),
                hovertemplate="<b>%{text}</b><br>Custom Gauge: %{customdata}<br>Lat: %{y:.4f}, Lon: %{x:.4f}<extra>Custom Rain Gauge</extra>",
            ))
    else:
        fig.add_trace(go.Scatter(
            x=stations_df["longitude"],
            y=stations_df["latitude"],
            mode="markers+text",
            name="Observation Stations",
            text=stations_df["name"],
            textposition="top right",
            customdata=stations_df["station_id"],
            marker=dict(size=13, color="#00E5FF", line=dict(width=2, color="#0369a1")),
            textfont=dict(size=11, color="#f8fafc"),
            hovertemplate="<b>%{text}</b><br>Station: %{customdata}<br>Lat: %{y:.4f}, Lon: %{x:.4f}<extra>Station</extra>",
        ))

    # 7. Viewport Bounds (Auto-center around stations with South Texas regional boundary limits)
    min_lon = float(stations_df["longitude"].min()) if not stations_df.empty else -98.5
    max_lon = float(stations_df["longitude"].max()) if not stations_df.empty else -96.9
    min_lat = float(stations_df["latitude"].min()) if not stations_df.empty else 27.7
    max_lat = float(stations_df["latitude"].max()) if not stations_df.empty else 29.6

    pad_lon = max(0.65, (max_lon - min_lon) * 0.35)
    pad_lat = max(0.55, (max_lat - min_lat) * 0.35)

    x_range = [min(-100.5, min_lon - pad_lon), max(-95.8, max_lon + pad_lon)]
    y_range = [min(26.6, min_lat - pad_lat), max(30.6, max_lat + pad_lat)]

    # 8. Cartographic Layout, Proportions, and Annotations
    fig.update_layout(
        height=450,
        margin=dict(l=25, r=25, t=38, b=25),
        title=dict(
            text="Texas Regional Hydrology & Station Network · 100% Baked-in Offline GIS Map",
            font=dict(size=14, color="#e2e8f0"),
        ),
        xaxis=dict(
            range=x_range,
            showgrid=False,
            zeroline=False,
            tickmode="linear",
            dtick=1.0,
            ticksuffix="°W",
            tickformat="-.0f",
            tickfont=dict(size=10, color="#94a3b8"),
            title=dict(text="Longitude", font=dict(size=11, color="#94a3b8")),
            showline=True,
            linecolor="#334155",
        ),
        yaxis=dict(
            range=y_range,
            showgrid=False,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1.13,  # Geometrically true aspect ratio at 28.5°N latitude
            tickmode="linear",
            dtick=1.0,
            ticksuffix="°N",
            tickformat=".0f",
            tickfont=dict(size=10, color="#94a3b8"),
            title=dict(text="Latitude", font=dict(size=11, color="#94a3b8")),
            showline=True,
            linecolor="#334155",
        ),
        plot_bgcolor="#0b1329",   # Gulf of Mexico / Ocean Body color
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1.0,
            font=dict(size=10, color="#cbd5e1"),
            bgcolor="rgba(15, 23, 42, 0.75)",
            bordercolor="#334155",
            borderwidth=1,
        ),
        annotations=[
            # Gulf of Mexico Water Annotation
            dict(
                x=-96.4,
                y=27.2,
                text="<i>Gulf of Mexico</i>",
                showarrow=False,
                font=dict(size=12, color="#38bdf8", family="serif"),
                opacity=0.6,
            ),
            # Corpus Christi Bay Annotation
            dict(
                x=-97.15,
                y=27.95,
                text="<i>Corpus Christi Bay</i>",
                showarrow=False,
                font=dict(size=9, color="#7dd3fc"),
                opacity=0.7,
            ),
            # North Arrow Compass
            dict(
                xref="paper",
                yref="paper",
                x=0.98,
                y=0.95,
                text="<b>▲ N</b>",
                showarrow=False,
                font=dict(size=13, color="#f8fafc"),
                bgcolor="rgba(15, 23, 42, 0.8)",
                bordercolor="#38bdf8",
                borderwidth=1,
                borderpad=3,
            ),
            # Cartographic Scale Bar (Approx. 50 miles / 80 km at 28.5°N)
            dict(
                xref="paper",
                yref="paper",
                x=0.03,
                y=0.04,
                text="━━━ 50 mi (80 km) ━━━",
                showarrow=False,
                font=dict(size=9, color="#94a3b8"),
                bgcolor="rgba(15, 23, 42, 0.75)",
                bordercolor="#334155",
                borderwidth=1,
                borderpad=3,
            ),
        ],
    )

    return accessible_chart(fig)