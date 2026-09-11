from __future__ import annotations

import calendar
from copy import deepcopy
import base64
from contextlib import contextmanager
from html import escape
from datetime import datetime, timezone, timedelta
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from basin_core.analysis import comparison, COMMUNITY_PRESETS, RESERVOIR_ASSUMPTIONS, simulate_reservoir_drawdown, simulate_stress_spectrum
from basin_core.water_system import WaterSource, WaterSystemConfig, REGION_N_PRESET, SMALL_MUNI_PRESET, RURAL_FARM_PRESET, SYSTEM_PRESETS
from basin_core.summary import scenario_summary, reservoir_summary
from basin_core.review_preferences import (DATA_SOURCES, GOALS, GUIDANCE, GUIDED_TAB_NOTES,
                                           TAB_LABELS, ReviewPreferences, load_preferences,
                                           save_preferences)
from basin_ui import evidence_panel, comparison_panel, assistant_panel
from basin_theme import apply_design, appearance_picker, custom_appearance, accessible_chart, reveal_tour_target
from basin_core.data import CachedSource, ROOT
from basin_core.engine import ScenarioParams
from basin_core.exporter import export_bundle, verify_bundle, generate_brief, summary_record, rainfall_rows
from basin_core.pdf_report import ExperimentConfig, generate_pdf_report, report_state_token
from basin_core.workspace import Workspace, session_dir
from basin_core.uploads import TEMPLATE, preview_rainfall
from basin_core.rainfall_comparison import compare_rainfall
from basin_core.custom_data import active_ids, digest
from basin_core.visualizers import rainfall_reference_figure, rainfall_shortfall_figure, stage_trigger_milestone_figure, drought_anomaly_matrix_figure
from basin_core.agronomics import calculate_crop_water_deficit, calculate_kbdi, CROP_COEFFICIENTS

icon_file = ROOT / "assets/basin.ico"
st.set_page_config(page_title="BASIN", page_icon=str(icon_file) if icon_file.exists() else "◉", layout="wide", initial_sidebar_state="collapsed")
apply_design()
assistant_w = int(st.session_state.get("assistant_width", 520))
notes_h = int(st.session_state.get("notes_height", 420))
st.html(f"""<style>
:root {{
    --basin-assistant-width: {assistant_w}px;
    --basin-notes-height: {notes_h}px;
}}
</style>""")
if st.session_state.get("assistant_open", False):
    st.html(f"""<style>
    .block-container, [data-testid="stMainBlockContainer"] {{
        margin-right: {assistant_w + 10}px !important;
        max-width: calc(100% - {assistant_w + 20}px) !important;
        padding-right: 1.5rem !important;
        transition: margin-right 0.35s cubic-bezier(0.16, 1, 0.3, 1), max-width 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    .st-key-assistant_drawer {{
        width: {assistant_w}px;
        min-width: 360px;
        max-width: 90vw;
        resize: horizontal;
    }}
    .st-key-assistant_tab_open {{
        right: {assistant_w}px !important;
        transition: right 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    body:has(.st-key-assistant_drawer) .st-key-notes_slide_drawer {{
        left: calc((100vw - {assistant_w + 10}px)/2) !important;
        transition: left 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    @media(max-width: 950px) {{
        .block-container, [data-testid="stMainBlockContainer"] {{
            margin-right: 0 !important;
            max-width: 100% !important;
        }}
        .st-key-assistant_drawer {{
            width: 92vw !important;
        }}
        .st-key-assistant_tab_open {{
            right: 92vw !important;
        }}
    }}
    </style>""")


@st.cache_resource
def load_source():
    return CachedSource()



def local_rainfall_preview(expanded=False):
    with st.expander("Upload and observe your custom CSV.", expanded=expanded):
        st.caption("One station per file. Preview only: uploads do not change scenarios or the NOAA snapshot. Preview stays in this session until you explicitly save reviewed evidence to an active analysis.")
        st.download_button("Local rainfall template", TEMPLATE, "local-rainfall-template.csv", "text/csv")
        station = st.text_input("Local station name", key="local_station")
        location = st.text_input("Location description", key="local_location", help="Town, area or gauge location. This does not establish catchment suitability.")
        unit = st.selectbox("Uploaded rainfall unit", ["Choose a unit", "mm", "inches"], key="local_unit")
        upload = st.file_uploader("Local observations CSV · date,precipitation", type=["csv"], key="local_rainfall_file")
        st.caption("Use YYYY-MM-DD dates. Blank rainfall means missing, not zero. Limit: 10 MB / 250,000 rows. Remove the file with the uploader's × to clear the preview.")
        if upload is None:
            return
        if unit == "Choose a unit" or not station.strip() or not location.strip():
            st.info("Enter the station, location and unit to preview this file.")
            return
        with st.expander("⚙️ CSV Parsing Options", expanded=False):
            c_p1, c_p2 = st.columns(2)
            fmt_opt = c_p1.selectbox("Date format", ["ISO (YYYY-MM-DD)", "US (MM/DD/YYYY)", "Auto-detect"], index=0, key="local_date_format")
            flex_hdr = c_p2.checkbox("Flexible column names (e.g. date, rain)", value=False, key="local_flex_headers")
        chosen_fmt = "iso" if "ISO" in fmt_opt else ("us" if "US" in fmt_opt else "auto")
        try:
            preview = preview_rainfall(upload.getvalue(), station, location, unit,
                                       date_format=chosen_fmt, allow_flexible_headers=flex_hdr)
        except ValueError as error:
            st.error(str(error))
            return
        st.text(f"{preview.station} — {preview.location}")
        st.caption(f"{preview.observations[0][0]} to {preview.observations[-1][0]} · Input: {preview.unit}; charts: mm")
        a, b, c = st.columns(3)
        a.metric("Valid rainfall days", preview.valid_days)
        b.metric("Missing rainfall days", preview.missing_days)
        c.metric("Calendar coverage", f"{preview.valid_days / preview.expected_days:.1%}")
        if preview.missing_days:
            st.warning("Missing dates and blank values remain gaps. Totals cover available observations only.")
        lookup = dict(preview.observations)
        days = [preview.observations[0][0] + timedelta(days=i) for i in range(preview.expected_days)]
        frame = pd.DataFrame({"date": days, "precip_mm": [lookup.get(day) for day in days]})
        if frame.precip_mm.max() > 500:
            st.warning("Values above 500 mm/day need a unit/source check. They have not been changed or excluded.")
        plot_frame = frame if len(frame) <= 5000 else frame.iloc[::(len(frame) // 5000 + 1)]
        fig = go.Figure(go.Scatter(x=plot_frame.date, y=plot_frame.precip_mm, mode="lines+markers", connectgaps=False, name="Local observations"))
        fig.update_yaxes(title="Daily rainfall · mm")
        st.plotly_chart(accessible_chart(fig), width="stretch", config={"displayModeBar": False})
        st.dataframe(frame, hide_index=True, width="stretch")
        st.caption(f"Original file SHA-256: {preview.original_sha256}")
        st.info("Local station suitability and historical reference are not yet established. No percentile, forecast or scenario change is produced by this preview.")

        with st.container(border=True):
            st.markdown("##### 🌟 Data Sovereignty: Use in Scenario Generator")
            st.caption("Register your uploaded rain gauge so you can resample drought scenarios and simulate storage drawdown directly on your own local records.")
            if st.button("🚀 Activate Gauge & Build Scenarios on Your Data", key=f"btn_activate_custom_gauge_{preview.original_sha256[:8]}", type="primary", width="stretch"):
                clean_lookup = {pd.to_datetime(d): v for d, v in preview.observations if v is not None}
                s_series = pd.Series(clean_lookup).sort_index()
                st_id = f"LOCAL_{preview.station[:10].upper().replace(' ', '_')}"
                curr_src = st.session_state.get("custom_source") or load_source()
                new_src = curr_src.with_custom_station(st_id, preview.station, s_series, preview.location)
                st.session_state["custom_source"] = new_src
                st.session_state["selected_stations"] = [st_id]
                params = ScenarioParams((st_id,), (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
                st.session_state.workspace = Workspace(new_src, params, 6)
                st.session_state.data_accepted = True
                st.session_state.page = "Workspace"
                st.rerun()

        uploaded_reference_comparison(preview, upload.getvalue())




def uploaded_reference_comparison(preview, raw):
    st.subheader("Compare with public rainfall")
    reference_source = load_source()
    registry = {item["id"]: item for item in reference_source.manifest["stations"]}
    station_id = st.selectbox("Public reference station", ["Choose a station", *registry],
                              format_func=lambda value: value if value not in registry else f"{registry[value]['name']} ({value})",
                              key="upload_reference_station")
    if station_id not in registry:
        st.caption("Select a station deliberately. BASIN does not infer the closest station or catchment suitability.")
        return
    metadata = registry[station_id]
    st.write({"Reference": metadata["name"], "Latitude": metadata["latitude"], "Longitude": metadata["longitude"],
              "Snapshot period": f"{reference_source.manifest['start']} to {reference_source.manifest['end']}"})
    st.caption("Source: NOAA GHCN-Daily, bundled snapshot. This is a same-date comparison, not a seasonal normal or an official drought category.")
    st.markdown(f"[Source documentation]({reference_source.manifest['documentation']})")
    token = f"{preview.original_sha256}_{preview.unit}_{preview.station}_{preview.location}_{station_id}"
    relationship = st.selectbox("Relationship to uploaded station", ["Not established", "Same physical station (user confirmed)", "Different station: regional proxy only"], key=f"relationship_{token}")
    daily = st.checkbox("I checked that the daily observation periods are comparable", key=f"daily_basis_{token}", help="Dates alone do not prove the gauges observe the same 24-hour period. Leave unchecked if unknown.")
    st.warning("Nearby or regional stations may experience different rain. A difference does not show which dataset is correct, establish catchment rainfall or predict a shortage.")
    relation = "not_established" if relationship == "Not established" else "same_station" if relationship.startswith("Same") else "regional_proxy"
    persist_custom_panel(preview, raw, station_id, relation, daily, token)
    if relationship == "Not established" or not daily:
        st.info("Comparison is blocked until the location relationship and daily basis are reviewed. You can still inspect the uploaded data above.")
        return
    relation = "same_station" if relationship.startswith("Same") else "regional_proxy"
    series = reference_source.select([station_id])[station_id]
    reference = {day.date(): None if pd.isna(value) else float(value) for day, value in series.items()}
    try:
        result = compare_rainfall(preview, reference, relationship=relation, daily_basis_confirmed=daily)
    except ValueError as error:
        st.warning(str(error))
        return
    a, b, c = st.columns(3)
    a.metric("Paired valid days", f"{result.paired_days} / {len(result.rows)}")
    b.metric("Uploaded total on paired days · mm", f"{result.upload_total_mm:.2f}")
    c.metric("Reference total on paired days · mm", f"{result.reference_total_mm:.2f}")
    st.write(f"Uploaded minus reference: {result.difference_mm:+.2f} mm")
    if result.relative_difference_pct is None:
        st.caption("Relative difference unavailable: the reference total is zero.")
    else:
        st.caption(f"Relative difference: {result.relative_difference_pct:+.2f}% of the reference total, not a forecast probability.")
    st.caption(f"{len(result.rows) - result.paired_days} days excluded from both totals because one or both values are missing. No gaps are filled.")
    frame = pd.DataFrame(result.rows, columns=["date", "uploaded_mm", "reference_mm"])
    plot_frame = frame if len(frame) <= 5000 else frame.iloc[::(len(frame) // 5000 + 1)]
    fig = go.Figure()
    for field, label in [("uploaded_mm", "Uploaded rainfall"), ("reference_mm", "NOAA reference")]:
        fig.add_trace(go.Scatter(x=plot_frame.date, y=plot_frame[field], name=label, connectgaps=False))
    fig.update_yaxes(title="Daily rainfall · mm")
    st.plotly_chart(accessible_chart(fig), width="stretch", config={"displayModeBar": False})
    st.dataframe(frame, hide_index=True, width="stretch")
    st.caption("This is a live preview. Save reviewed evidence above to retain a version, link it to scenarios and include it in a consented verified packet.")
    include = st.checkbox("Include my uploaded values in a downloadable comparison report", key=f"share_comparison_{token}_{relation}")
    if include:
        report = {"schema_version": "rainfall-comparison-1", "method": "paired-valid-calendar-days-v1",
                  "upload_sha256": preview.original_sha256, "uploaded_input_unit": preview.unit,
                  "reference_snapshot_sha256": reference_source.manifest["sha256"], "reference_station_id": station_id,
                  "reference_source": reference_source.manifest["documentation"], "relationship_declared_by_user": relation,
                  "daily_basis_confirmed_by_user": True, "units": "mm", "paired_days": result.paired_days,
                  "upload_total_mm": result.upload_total_mm, "reference_total_mm": result.reference_total_mm,
                  "difference_mm": result.difference_mm, "relative_difference_pct": result.relative_difference_pct,
                  "limitations": "Descriptive same-date comparison; geography and daily basis are user declarations, not independently validated. No forecast, climatology or scenario approval.",
                  "rows": [{"date": str(day), "uploaded_mm": x, "reference_mm": y} for day, x, y in result.rows]}
        st.download_button("Download comparison JSON", json.dumps(report, indent=2, allow_nan=False), "rainfall-comparison.json", "application/json")


def persist_custom_panel(preview, raw, reference_station, relationship, daily, token):
    workspace = st.session_state.get("workspace")
    if workspace is None:
        st.info("To retain this upload, first create or open an analysis from Workspace. Preview alone does not save it.")
        return
    with st.expander("Save reviewed upload into this analysis"):
        st.caption("Links this comparison as supporting evidence; does not replace NOAA scenario rainfall. Saving or replacing evidence clears affected scenario approvals. Unknown suitability can be recorded without calculating a comparison.")
        active = active_ids(workspace.custom_uploads)
        versions = {r["id"]: r for r in workspace.custom_uploads}
        with st.form("save_custom_" + digest(token)):
            previous = st.selectbox("Evidence version to replace", ["New evidence", *sorted(active)],
                                    format_func=lambda i: i if i == "New evidence" else versions[i]["station"] + " · " + i[-8:])
            chosen = st.multiselect("Scenarios supported by this evidence", [s.id for s in workspace.scenarios], default=workspace.selected)
            provider = st.text_input("Source / provider", value="Local Municipal / Sponsor Observation")
            basis = st.text_input("Observation-day definition", value="Midnight-to-midnight local standard time; unflagged observations", help="Timezone and daily reporting window, or explicitly explain what is unknown.")
            rationale = st.text_area("Why this reference is appropriate, or what remains uncertain", value="Nearby municipal monitoring gage providing secondary ground-truth verification of regional drought conditions.")
            reviewed = st.checkbox("I reviewed the upload and declarations and consent to saving the original bytes and metadata locally")
            submit = st.form_submit_button("Save reviewed evidence")
        if submit:
            try:
                if previous != "New evidence" and sorted(chosen) != versions[previous]["scenario_ids"]:
                    raise ValueError("Replacing a version must retain its scenario links. Select the same scenarios shown in Saved custom evidence.")
                candidate = deepcopy(workspace)
                candidate.save_custom_upload(raw, reviewed=reviewed, station=preview.station, location=preview.location,
                                             unit=preview.unit, provider=provider, observation_basis=basis,
                                             reference_station=reference_station, relationship=relationship, daily_confirmed=daily,
                                             rationale=rationale, scenario_ids=chosen,
                                             supersedes="" if previous == "New evidence" else previous)
                if save(candidate):
                    st.session_state.workspace = candidate
                    st.session_state.pop("packet", None)
                    st.rerun()
            except ValueError as error:
                st.error(str(error))


def saved_custom_panel(workspace):
    if not workspace or not workspace.custom_uploads:
        return
    with st.expander("Saved custom evidence", expanded=True):
        active = active_ids(workspace.custom_uploads)
        versions = {r["id"]: r for r in workspace.custom_uploads}
        identifier = st.selectbox("Saved upload version", list(versions), format_func=lambda i: versions[i]["station"] + " · " + i[-8:] + (" · current" if i in active else " · superseded"))
        record = versions[identifier]
        st.markdown("**" + record["station"].replace("*", "") + "**")
        st.caption(f"{record['start']} to {record['end']} · original unit: {record['input_unit']} · linked scenarios: {', '.join(record['scenario_ids'])}")
        with st.expander("Source identity and suitability details"):
            st.write({k: record[k] for k in ("id", "station", "location", "provider", "input_unit", "start", "end", "original_sha256", "normalized_sha256", "reference_station", "relationship", "observation_basis", "rationale", "scenario_ids")})
        result = record["comparison"]
        st.caption("Supporting evidence only; original rainfall scenarios are unchanged. Original bytes remain local. Review decisions must be renewed after a version change.")
        if result["status"] == "calculated":
            st.write({k: result[k] for k in ("paired_days", "upload_total_mm", "reference_total_mm", "difference_mm")})
            frame = pd.DataFrame(result["rows"], columns=["date", "uploaded_mm", "reference_mm"])
            fig = go.Figure()
            for field in ("uploaded_mm", "reference_mm"):
                fig.add_trace(go.Scatter(x=frame.date, y=frame[field], name=field, connectgaps=False))
            st.plotly_chart(chart(fig), width="stretch", config={"displayModeBar": False})
        else:
            st.info("Comparison unavailable: " + result["reason"])
            frame = pd.DataFrame(record["observations"], columns=["date", "uploaded_mm"])
        st.dataframe(frame, hide_index=True, width="stretch")


def save(w):
    try:
        w.save()
        return True
    except OSError as error:
        st.error(f"Save failed: {error}")
        return False


def chart(fig, height=300):
    fig.update_layout(height=height, margin=dict(l=5, r=8, t=10, b=5),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial", size=12),
                      legend=dict(orientation="h", y=-.22),
                      colorway=["#087e8b", "#cc9145", "#638c72", "#826f9e", "#ac675d", "#4c6c94", "#858844", "#a25789"])
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(zeroline=False)
    return accessible_chart(fig)


def basin_map(stations_df):
    """Render station locations on a baked-in offline GIS map or optional satellite overlay."""
    from basin_core.geo_map import build_basin_map
    satellite = st.session_state.get("map_satellite_mode", False)
    if st.session_state.get("map_offline_mode", False):
        satellite = False
    return build_basin_map(stations_df, use_satellite=satellite)


def reservoir_simulation_figure(sim_df: pd.DataFrame, pace_ms: int = 150, config: WaterSystemConfig | None = None):
    days = len(sim_df)
    step = max(1, days // 45)
    indices = list(range(0, days, step))
    if indices[-1] != days - 1:
        indices.append(days - 1)

    cfg = config or REGION_N_PRESET
    n_sources = len(cfg.sources)
    source_labels = [f"{s.name}<br>(Max {s.capacity_acft:,.0f} ac-ft)" for s in cfg.sources]
    palette = ["#0d9488", "#087e8b", "#0284c7", "#0369a1"]
    colors = [palette[i % len(palette)] for i in range(n_sources)]
    max_cap = max(s.capacity_acft for s in cfg.sources)

    fig = make_subplots(
        rows=1, cols=2, column_widths=[0.36, 0.64],
        subplot_titles=["Active Storage (ac-ft)", "Combined Pool Trajectory (%)"],
        specs=[[{"type": "bar"}, {"type": "xy"}]]
    )

    init_row = sim_df.iloc[-1]
    y_init = []
    text_init = []
    for i in range(n_sources):
        col_acft = f"source_{i}_acft"
        col_pct = f"source_{i}_pct"
        if col_acft in init_row:
            val_acft = init_row[col_acft]
            val_pct = init_row[col_pct]
        elif i == 0 and "lcc_acft" in init_row:
            val_acft = init_row["lcc_acft"]
            val_pct = init_row["lcc_pct"]
        elif i == 1 and "ccr_acft" in init_row:
            val_acft = init_row["ccr_acft"]
            val_pct = init_row["ccr_pct"]
        else:
            val_acft = 0.0
            val_pct = 0.0
        y_init.append(val_acft)
        text_init.append(f"{val_acft:,.0f} ac-ft<br>({val_pct:.1f}%)")

    fig.add_trace(go.Bar(
        x=source_labels,
        y=y_init,
        marker=dict(color=colors, line=dict(width=1.5, color="#123d38")),
        text=text_init,
        textposition="outside", textfont=dict(size=12), cliponaxis=False,
        name="Reservoir Storage",
        hovertemplate="<b>%{x}</b><br>Storage: %{y:,.0f} ac-ft<extra></extra>"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=sim_df["day"],
        y=sim_df["combined_pct"],
        mode="lines",
        line=dict(color="#087e8b", width=2.5),
        name="Combined %",
        hovertemplate="Day %{x}<br>Storage: %{y:.1f}%<extra></extra>"
    ), row=1, col=2)

    b40 = cfg.stage_bands_pct[0] * 100 if len(cfg.stage_bands_pct) >= 1 else 40
    b30 = cfg.stage_bands_pct[1] * 100 if len(cfg.stage_bands_pct) >= 2 else 30
    b20 = cfg.stage_bands_pct[2] * 100 if len(cfg.stage_bands_pct) >= 3 else 20

    fig.add_hline(y=b40, line_dash="dash", line_color="#d97706", annotation_text=f"Band 1 ({b40:.0f}%)",
                  annotation_position="top right", row=1, col=2)
    fig.add_hline(y=b30, line_dash="dash", line_color="#ea580c", annotation_text=f"Band 2 ({b30:.0f}%)",
                  annotation_position="top right", row=1, col=2)
    fig.add_hline(y=b20, line_dash="dash", line_color="#dc2626", annotation_text=f"Band 3 ({b20:.0f}%)",
                  annotation_position="top right", row=1, col=2)

    if len(cfg.stage_bands_pct) >= 4:
        b10 = cfg.stage_bands_pct[3] * 100
        fig.add_hline(y=b10, line_dash="dot", line_color="#991b1b", annotation_text=f"Stage 4 Emergency ({b10:.0f}%)",
                      annotation_position="top right", row=1, col=2)

    dead_acft = getattr(cfg, "dead_storage_acft", 0.0)
    if dead_acft > 0 and cfg.total_capacity_acft > 0:
        dead_pct = dead_acft / cfg.total_capacity_acft * 100
        fig.add_hline(y=dead_pct, line_dash="dot", line_color="#450a0a", annotation_text=f"Dead Storage Reserve ({dead_pct:.1f}%)",
                      annotation_position="bottom right", row=1, col=2)

    if "Region N" in cfg.name or "Corpus Christi" in cfg.name:
        fig.add_hline(y=7.7, line_dash="dot", line_color="#7f1d1d", annotation_text="April 2026 Record Low (7.7%)",
                      annotation_position="bottom left", row=1, col=2)

    frames = []
    for idx in indices:
        row = sim_df.iloc[idx]
        d = row["day"]
        sub_df = sim_df.iloc[:idx+1]
        y_frame = []
        text_frame = []
        for i in range(n_sources):
            col_acft = f"source_{i}_acft"
            col_pct = f"source_{i}_pct"
            if col_acft in row:
                val_acft = row[col_acft]
                val_pct = row[col_pct]
            elif i == 0 and "lcc_acft" in row:
                val_acft = row["lcc_acft"]
                val_pct = row["lcc_pct"]
            elif i == 1 and "ccr_acft" in row:
                val_acft = row["ccr_acft"]
                val_pct = row["ccr_pct"]
            else:
                val_acft = 0.0
                val_pct = 0.0
            y_frame.append(val_acft)
            text_frame.append(f"{val_acft:,.0f} ac-ft<br>({val_pct:.1f}%)")

        frame = go.Frame(
            data=[
                go.Bar(
                    x=source_labels,
                    y=y_frame,
                    text=text_frame,
                ),
                go.Scatter(
                    x=sub_df["day"].tolist(),
                    y=sub_df["combined_pct"].tolist()
                )
            ],
            name=f"Day {d}"
        )
        frames.append(frame)

    fig.frames = frames

    fig.update_yaxes(range=[0, max_cap * 1.18], title="ac-ft", row=1, col=1)
    fig.update_yaxes(range=[0, 100], title="Combined %", row=1, col=2)
    fig.update_xaxes(range=[0, days + 2], title="Scenario Day", row=1, col=2)

    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        showlegend=False,
        updatemenus=[dict(
            type="buttons",
            showactive=False, bgcolor="#243239", font=dict(color="#ffffff"),
            direction="left",
            x=0.0, y=1.24,
            buttons=[
                dict(label="▶ Play Simulation", method="animate",
                     args=[None, {"frame": {"duration": pace_ms, "redraw": True}, "fromcurrent": False, "mode": "immediate"}]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}])
            ]
        )],
        sliders=[dict(
            active=len(indices) - 1,
            x=0.0, y=-0.18,
            len=1.0,
            currentvalue={"prefix": "Simulation: ", "visible": True, "xanchor": "right"},
            steps=[dict(label=f"D{sim_df.iloc[idx]['day']}", method="animate",
                        args=[[f"Day {sim_df.iloc[idx]['day']}"], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}])
                   for idx in indices]
        )]
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(zeroline=False)
    return fig


def stress_spectrum_figure(spec: dict) -> go.Figure:
    fig = go.Figure()
    tier_styles = {
        1.0: {"name": "Selected scenario (100%)", "color": "#0d9488", "width": 2.5, "dash": "solid"},
        0.8: {"name": "20% additional rainfall reduction", "color": "#d97706", "width": 2.2, "dash": "solid"},
        0.6: {"name": "40% additional rainfall reduction", "color": "#ea580c", "width": 2.2, "dash": "solid"},
        0.4: {"name": "60% additional rainfall reduction", "color": "#dc2626", "width": 2.2, "dash": "solid"},
    }
    for m, res in spec["tier_results"].items():
        style = tier_styles.get(m, {"name": f"{int(m*100)}% Rain", "color": "#64748b", "width": 2.0, "dash": "solid"})
        sim_df = res["df"]
        fig.add_trace(go.Scatter(
            x=sim_df["day"],
            y=sim_df["combined_pct"],
            mode="lines",
            name=style["name"],
            line=dict(color=style["color"], width=style["width"], dash=style["dash"]),
            hovertemplate=f"<b>{style['name']}</b><br>Day %{{x}}<br>Storage: %{{y:.1f}}%<extra></extra>"
        ))

    # Threshold horizontal reference bands
    fig.add_hline(y=40, line_dash="dash", line_color="#d97706", annotation_text="Assumed 40% band",
                  annotation_position="top right")
    fig.add_hline(y=30, line_dash="dash", line_color="#ea580c", annotation_text="Assumed 30% band",
                  annotation_position="top right")
    fig.add_hline(y=20, line_dash="dash", line_color="#dc2626", annotation_text="Assumed 20% band",
                  annotation_position="top right")
    fig.add_hline(y=15, line_dash="dot", line_color="#991b1b", annotation_text="Assumed 15% band",
                  annotation_position="top right")

    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
        xaxis=dict(title="Scenario Day", showgrid=False, zeroline=False),
        yaxis=dict(title="Combined Storage (%)", range=[0, 100], showgrid=True, zeroline=False),
    )
    return fig


def table(w):
    return pd.DataFrame([{"ID": s.id, "Group": s.cluster, "Profile": getattr(s, "cluster_name", f"Group {s.cluster}"),
                          "Score": round(s.score, 2),
                          "Days": s.features["duration_days"], "Onset": calendar.month_abbr[s.features["onset_month"]],
                          "Deficit mm": round(s.features["deficit_mm"], 2),
                          "Deficit in": round(s.features["deficit_mm"] / 25.4, 2),
                          "Stations stressed together %": round(s.features["concurrence"] * 100, 1),
                          "How unusual vs history %": round(s.features["historical_percentile"] * 100, 1),
                          "Dry spell days": s.features["max_dry_days"],
                          "Revision": s.revision, "Status": s.status,
                          "Selected for review": s.id in w.selected} for s in w.scenarios])


PAGE_LABELS = {
    "Data": "Data Dashboard",
    "Workspace": "Scenario Builder",
    "Review": "Review Selections",
    "Exports": "Export",
}


PAGE_QUESTIONS = {
    "Data": "Can I trust and use these observations?",
    "Workspace": "Which rainfall scenarios deserve review?",
    "Review": "Which rainfall scenarios belong in the handoff?",
    "Exports": "What evidence should the recipient receive?",
}


PAGE_ACTIONS = {
    "Data": "Check source identity, coverage, location and limitations before building scenarios.",
    "Workspace": "Configure settings, prioritize weights, and compare shortlisted candidates.",
    "Review": "Compare rainfall with its reference, check the evidence, and decide whether to include this revision.",
    "Exports": "Confirm the privacy choice, build the packet, and download the verified files.",
}


def decision_summary(w):
    lead = w.get(w.selected[0])
    evidence_count = len(w.evidence_refs.get(lead.id, []))
    unresolved = sum(conflict["status"] == "unresolved" for conflict in w.conflicts)
    approved = sum(
        scenario.status == "accepted" and scenario.approved_revision == scenario.revision
        for scenario in (w.get(identifier) for identifier in w.selected)
    )
    limitation = (
        f"{unresolved} unresolved evidence disagreement(s)"
        if unresolved else "Station suitability remains provisional"
    )
    next_action = (
        "Share the reviewed results"
        if approved == len(w.selected) else f"Review {len(w.selected) - approved} remaining scenario(s)"
    )
    with st.container(key="decision_summary", border=True):
        st.markdown("**Decision summary**")
        st.caption(
            f"Scenario to review: **{lead.id}** · Why it ranked here: "
            f"**{w.selection_reason(lead.id)}** · Evidence used: **{evidence_count} records**"
        )
        st.caption(f"Material limitation: **{limitation}** · Next action: **{next_action}**")


def open_review(identifier):
    st.session_state.inspect_id = identifier
    st.session_state.page = "Review"


def review_preferences(workspace_id):
    """Display preferences for this run, cached in session state across navigation."""
    cached = st.session_state.get("review_prefs")
    if not isinstance(cached, tuple) or len(cached) != 2 or cached[0] != workspace_id:
        cached = (workspace_id, load_preferences(workspace_id))
        st.session_state["review_prefs"] = cached
        st.session_state["review_setup_goal"] = cached[1].goal
        st.session_state["review_setup_data"] = cached[1].data_source
        st.session_state["review_setup_guidance"] = cached[1].guidance
    return cached[1]


def store_review_preferences(workspace_id, preferences):
    """Persist display choices beside the run. Never touches the audited record."""
    st.session_state["review_prefs"] = (workspace_id, preferences)
    save_preferences(workspace_id, preferences)


def switch_page(name):
    st.session_state.page = name
    w = st.session_state.get("workspace")
    if name == "Review" and w and w.selected and not st.session_state.get("inspect_id"):
        st.session_state.inspect_id = w.selected[0]


def render_top_navigation(current_page, w):
    has_run = w is not None
    stages = [
        ("Data", "Data Dashboard", True),
        ("Workspace", "Scenario Builder", True),
        ("Review", "Review Selections", has_run),
        ("Exports", "Export", has_run),
    ]

    cols = st.columns(4)
    for col, (page_key, label, is_enabled) in zip(cols, stages):
        is_active = current_page == page_key
        if is_active:
            state_class = "basin-nav-active"
        elif not is_enabled:
            state_class = "basin-nav-locked"
        else:
            state_class = "basin-nav-ready"

        with col:
            st.markdown(f'<div class="basin-header-text-btn {state_class}">', unsafe_allow_html=True)
            btn_label = label if is_enabled else f"🔒 {label}"
            st.button(
                btn_label,
                key=f"nav_tab_{page_key}",
                disabled=not is_enabled,
                on_click=switch_page,
                args=(page_key,),
                help=None if is_enabled else "Requires an active analysis run. Generate scenarios in Scenario Builder first.",
                width="stretch",
            )
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="basin-nav-divider"></div>', unsafe_allow_html=True)


def personal_notes_panel(w):
    st.session_state.setdefault("notes_open", False)
    is_open = st.session_state.notes_open
    current_val = w.notes if w else st.session_state.get("personal_notes", "")
    drawer_key = "notes_drawer_open" if is_open else "notes_drawer_closed"

    with st.container(key="notes_slide_drawer"):
        with st.container(key=drawer_key):
            tab_c1, tab_c2, tab_c3 = st.columns([3.5, 2.2, 0.8])
            with tab_c1:
                st.markdown('<div class="basin-notes-tab-title">📝 Personal Notes</div>', unsafe_allow_html=True)
            with tab_c2:
                if is_open and hasattr(st, "segmented_control"):
                    cur_h = st.session_state.get("notes_height", 420)
                    h_opts = [260, 420, 600]
                    sel_h = st.segmented_control(
                        "Height",
                        h_opts,
                        default=cur_h if cur_h in h_opts else 420,
                        format_func=lambda h: {260: "Compact", 420: "Standard", 600: "Tall"}.get(h, f"{h}px"),
                        label_visibility="collapsed",
                        key="notes_height_selector"
                    )
                    if sel_h and sel_h != cur_h:
                        st.session_state.notes_height = sel_h
                        st.rerun()
            with tab_c3:
                toggle_txt = "▼ Close" if is_open else "▲ Notes"
                if st.button(toggle_txt, key="btn_toggle_notes", help="Toggle Personal Notes panel"):
                    st.session_state.notes_open = not is_open
                    st.rerun()

            with st.container(key="notes_body_content"):
                st.caption("Saved locally with this analysis. Included in exports only if you opt in.")
                p_key = f"provider_{w.id}" if w else "provider_default"
                cur_h = st.session_state.get("notes_height", 420)
                note = st.text_area("Provider notes", value=current_val, key=p_key, height=max(130, cur_h - 180))
                if st.button("Save notes", key=f"btn_save_notes_{w.id if w else 'default'}", width="stretch", type="primary"):
                    st.session_state["personal_notes"] = note
                    if w:
                        w.notes = note
                        if save(w):
                            st.success("Notes saved locally")
                    else:
                        st.success("Notes saved locally")


TUTORIAL_STEPS = [
    {
        "target": "data_map",
        "page": "Data",
        "tag": "OBSERVATIONS · PROVENANCE",
        "title": "1. Inspect the Observation Sources",
        "desc": "Three provisional NOAA station proxies with a byte-verified snapshot. A checksum does not validate catchment suitability.",
        "directive": "Inspect the highlighted station map and completeness table. Open Snapshot metadata & quality policy for the missing-data rules.",
    },
    {
        "target": "sidebar_generator",
        "page": "Workspace",
        "tag": "SCENARIO ENGINE · RESAMPLING",
        "title": "2. Resample Historical Weather Windows",
        "desc": "Extracts synchronized multi-station historical windows (30–365 days) with retention scaling (35%–85%) with every transformation recorded.",
        "directive": "Use New run in the left sidebar, then click Generate. Choose Next Step to keep the current run.",
    },
    {
        "target": "sidebar_presets",
        "page": "Workspace",
        "tag": "COMMUNITY PRIORITIES · WEIGHTS",
        "title": "3. Illustrative User Priorities",
        "desc": "Illustrative presets and editable weights change scores. Your reviewed shortlist stays in place until you rebuild it.",
        "directive": "Choose a community priority preset in the highlighted Ranking weights section on the left. Scores update; rebuilding the shortlist is a separate action.",
    },
    {
        "target": "workspace_table",
        "page": "Workspace",
        "tag": "UNSUPERVISED ML · CLUSTERING",
        "title": "4. K-Means Drought Profiles",
        "desc": "Deterministic K-Means clusters candidates into explainable profiles, ensuring diverse representation across the shortlist.",
        "directive": "Select a row in the highlighted candidate table, then click Inspect to open it. Choose Next Step to continue the tour.",
    },
    {
        "target": "review_simulation",
        "page": "Review",
        "tag": "OPTIONAL · ILLUSTRATIVE EXPERIMENT",
        "title": "5. Explore an Illustrative Water Balance",
        "desc": "Uncalibrated two-pool experiment with assumed inflow, evaporation, demand and capacity. Its outputs are excluded from the evidence packet.",
        "directive": "Inspect assumptions, then play the conditional storage trajectory. Bands are illustrative, not official restriction dates.",
        "review_mode": "Reservoir simulation"
    },
    {
        "target": "review_decision",
        "page": "Review",
        "tag": "HUMAN REVIEW · RAINFALL CONTENT",
        "title": "6. Review, Challenge and Accept Rainfall",
        "desc": "Inspect evidence, record disagreements, and edit or accept rainfall content. Acceptance is a local review decision, not professional certification.",
        "directive": "Enter an audit rationale note and click 'Include this revision in handoff' to record your decision.",
        "review_mode": "Cumulative rainfall"
    },
    {
        "target": "export_panel",
        "page": "Exports",
        "tag": "AUDITABLE HANDOFF · EXPERT REVIEW",
        "title": "7. Export a Reviewed Evidence Packet",
        "desc": "Packages reviewed rainfall, public evidence, unresolved conflicts and a readable brief. Replay checks internal consistency within its stated scope.",
        "directive": "Click Build verified export in the highlighted area to build the reviewed handoff ZIP.",
    }
]


def start_example(source, names, force=False):
    """Open a reproducible example without approving any scenario."""
    curr_w = st.session_state.get("workspace")
    if not force and curr_w and (any(s.status == "accepted" for s in curr_w.scenarios) or curr_w.custom_uploads):
        st.session_state.confirm_reset_example = True
        return
    st.session_state.pop("confirm_reset_example", None)
    params = ScenarioParams(tuple(names), (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
    workspace = Workspace(source, params, 6)
    st.session_state.workspace = workspace
    st.session_state.data_accepted = True
    st.session_state.scenarios_accepted = True
    st.session_state.page = "Review"
    st.session_state.inspect_id = workspace.selected[0]
    save(workspace)


def start_tutorial(source, names):
    st.session_state.tutorial_visit = st.session_state.get("tutorial_visit", 0) + 1
    st.session_state.tutorial_active = True
    st.session_state.tutorial_step = 0
    st.session_state.page = TUTORIAL_STEPS[0]["page"]
    curr_w = st.session_state.get("workspace")
    if curr_w is None:
        params = ScenarioParams(tuple(names), (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
        new_w = Workspace(source, params, 6)
        st.session_state.workspace = new_w
        save(new_w)
    if st.session_state.get("workspace") and not st.session_state.get("inspect_id"):
        st.session_state.inspect_id = st.session_state.workspace.selected[0]


def tutorial_next():
    step_idx = st.session_state.get("tutorial_step", 0)
    if step_idx < len(TUTORIAL_STEPS) - 1:
        next_idx = step_idx + 1
        st.session_state.tutorial_step = next_idx
        st.session_state.page = TUTORIAL_STEPS[next_idx]["page"]
        curr_w = st.session_state.get("workspace")
        if curr_w and TUTORIAL_STEPS[next_idx]["page"] == "Review":
            if not st.session_state.get("inspect_id") and curr_w.selected:
                st.session_state.inspect_id = curr_w.selected[0]
        if TUTORIAL_STEPS[next_idx].get("review_mode"):
            st.session_state.storage_experiment = TUTORIAL_STEPS[next_idx]["review_mode"] == "Reservoir simulation"
    else:
        st.session_state.tutorial_active = False


def tutorial_prev():
    step_idx = st.session_state.get("tutorial_step", 0)
    prev_idx = max(0, step_idx - 1)
    st.session_state.tutorial_step = prev_idx
    st.session_state.page = TUTORIAL_STEPS[prev_idx]["page"]
    if TUTORIAL_STEPS[prev_idx].get("review_mode"):
        st.session_state.storage_experiment = TUTORIAL_STEPS[prev_idx]["review_mode"] == "Reservoir simulation"


def tutorial_exit():
    st.session_state.tutorial_active = False


TOUR_LOCATIONS = {
    "data_map": "Data: station map and completeness table",
    "sidebar_generator": "Left sidebar: New run",
    "sidebar_presets": "Left sidebar: Ranking weights",
    "workspace_table": "Workspace: candidate table",
    "review_simulation": "Review: reservoir playback chart",
    "review_decision": "Review: note and decision controls on the right",
    "export_panel": "Exports: build packet button",
}


def current_tour_step():
    if not st.session_state.get("tutorial_active", False):
        return None
    index = st.session_state.get("tutorial_step", 0)
    if not 0 <= index < len(TUTORIAL_STEPS):
        return None
    return TUTORIAL_STEPS[index]


def return_to_tour_step():
    step = current_tour_step()
    if step:
        st.session_state.tutorial_visit = st.session_state.get("tutorial_visit", 0) + 1
        st.session_state.page = step["page"]
        if step.get("review_mode"):
            st.session_state.storage_experiment = step["review_mode"] == "Reservoir simulation"


def render_tour_guide(workspace):
    step = current_tour_step()
    if step is None:
        return
    index = st.session_state.tutorial_step
    directive = step["directive"]
    on_page = st.session_state.page == step["page"]
    if step["target"] == "export_panel" and workspace:
        try:
            workspace.exportable()
        except ValueError:
            directive = "Export is locked. Return to Review and accept or reject every shortlisted revision, keeping at least one accepted scenario. Then build the packet. Finishing the tutorial does not approve scenarios."
    with st.container(key="tutorial_guide"):
        st.markdown(f"""<div class="tutorial-meta">GUIDED TOUR &nbsp; / &nbsp; STEP {index + 1} OF {len(TUTORIAL_STEPS)}</div>
<div class="tutorial-title">{escape(step['title'].split('. ', 1)[-1])}</div>
<p class="tutorial-description">{escape(step['desc'])}</p>
<p class="tutorial-action">{escape(directive)}</p>
<div class="tutorial-location">Current section: {escape(TOUR_LOCATIONS[step['target']])}</div>""", unsafe_allow_html=True)
        with st.container(horizontal=True, gap="small"):
            st.button("◀ Prev", key="tutorial_prev", disabled=index == 0, on_click=tutorial_prev)
            st.button("✓ Finish Tutorial" if index == len(TUTORIAL_STEPS)-1 else "Next Step ▶",
                      key="tutorial_next", type="primary", on_click=tutorial_next)
            st.button("✕ Exit", key="tutorial_exit", on_click=tutorial_exit)
            if not on_page:
                st.button("Return to this step", on_click=return_to_tour_step)



@contextmanager
def tour_target(target_id: str):
    step = current_tour_step()
    active = step is not None and step["target"] == target_id and st.session_state.page == step["page"]
    key = f"tour_target_{target_id}"
    if active:
        st.markdown(f"""<style>.st-key-{key}{{outline:2px solid currentColor;outline-offset:3px;border-radius:6px;padding:10px;box-shadow:0 0 0 5px color-mix(in srgb,currentColor 8%,transparent)}}
.st-key-{key} .stPlotlyChart{{min-width:0}}</style>""", unsafe_allow_html=True)
    with st.container(key=key, width="content" if target_id == "export_panel" else "stretch"):
        if active:
            st.markdown(f'<div id="tour-{target_id}" class="tutorial-anchor tutorial-target-label">STEP {st.session_state.tutorial_step + 1} · {escape(TOUR_LOCATIONS[target_id])}</div>', unsafe_allow_html=True)
            render_tour_guide(st.session_state.get("workspace"))
            reveal_tour_target(target_id, f"{st.session_state.get('tutorial_visit', 0)}:{st.session_state.tutorial_step}:{target_id}")
        yield


try:
    source = st.session_state.get("custom_source") or load_source()
except (OSError, ValueError, KeyError) as error:
    st.error(f"Snapshot unavailable: {error}")
    st.stop()
names = {s["id"]: s["name"].title().replace(" Intl Ap", "").replace(" Rgnl Ap", "") for s in source.manifest["stations"]}
w = st.session_state.get("workspace")
if w is not None and st.session_state.get("report_workspace_id") != w.id:
    for report_key in ("experiment_config", "preview_pdf", "packet",
                       "review_initial_storage", "review_conservation", "review_pipeline_active", "storage_experiment"):
        st.session_state.pop(report_key, None)
    st.session_state["report_workspace_id"] = w.id
curr_target = TUTORIAL_STEPS[st.session_state.get("tutorial_step", 0)]["target"] if st.session_state.get("tutorial_active") else ""

profile_context = w.id if w else "new-run"
profile_defaults = review_preferences(w.id) if w else ReviewPreferences()
if st.session_state.get("run_focus_context") != profile_context:
    st.session_state["run_focus_context"] = profile_context
    st.session_state["run_focus_goal"] = profile_defaults.goal
    st.session_state["run_focus_data"] = profile_defaults.data_source
    st.session_state["run_focus_guidance"] = profile_defaults.guidance
    st.session_state["run_focus_skip"] = profile_defaults.dismissed and not profile_defaults.configured

with st.sidebar:
    page = st.radio("View", ["Data", "Workspace", "Review", "Exports"], key="page",
                    index=0, format_func=PAGE_LABELS.get, label_visibility="collapsed")

# Centered Brand Header with Top-Right Utilities and Top-Left Unit Selector
top_l, top_c, top_r = st.columns([1.2, 1.8, 1.2])

with top_l:
    u_choice = st.selectbox(
        "Units",
        ["🇺🇸 US Customary (in, ac-ft)", "🌐 Metric (mm, m³)"],
        index=0 if st.session_state.get("unit_mode", "us") == "us" else 1,
        key="global_unit_selector",
        label_visibility="collapsed",
        help="Switch units across all charts, tables, and KPI metrics.",
    )
    st.session_state["unit_mode"] = "us" if "US Customary" in u_choice else "metric"

with top_c:
    logo_file = ROOT / "assets" / "basin-logo.png"
    if logo_file.exists():
        logo_b64 = base64.b64encode(logo_file.read_bytes()).decode()
        st.markdown(f'<div class="basin-top-logo-wrap"><img src="data:image/png;base64,{logo_b64}" alt="BASIN" class="basin-top-logo" /></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="basin-top-brand">BASIN</div>', unsafe_allow_html=True)

with top_r:
    u_col1, u_col2 = st.columns(2)
    with u_col1:
        with st.popover("Saved Runs", width="stretch"):
            st.markdown("**Saved Workspace Runs**")
            saved_dir = session_dir()
            sessions = sorted(saved_dir.glob("session-*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if saved_dir.exists() else []
            if sessions:
                total_mb = sum(p.stat().st_size for p in sessions) / (1024 * 1024)
                st.caption(f"💾 {len(sessions)} saved session(s) · {total_mb:.1f} MB in `{saved_dir.name}/`")
                previous = st.selectbox(
                    "Select saved run", sessions,
                    format_func=lambda p: f"{datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M')} · {p.stem.replace('session-', '')[:8]}…",
                    key="saved_run_select"
                )
                if st.button("Open run", key="btn_open_saved_run", width="stretch", type="primary"):
                    try:
                        restored = Workspace.load(source, previous)
                        st.session_state.clear()
                        st.session_state.workspace = restored
                        st.session_state.data_accepted = True
                        st.session_state.scenarios_accepted = True
                        if getattr(restored, "legacy_warning", None):
                            st.warning(restored.legacy_warning)
                        st.rerun()
                    except (ValueError, KeyError, OSError, TypeError) as error:
                        st.error(f"Cannot open run: {error}")
                if len(sessions) > 3:
                    if st.button("🗑️ Purge drafts older than top 3", key="btn_purge_old_runs", width="stretch"):
                        for p in sessions[3:]:
                            try:
                                p.unlink()
                                audit_p = p.parent / f"audit-{p.stem.replace('session-', '')}.jsonl"
                                if audit_p.exists():
                                    audit_p.unlink()
                            except OSError:
                                pass
                        st.success("Older drafts purged.")
                        st.rerun()
            else:
                st.caption("No saved runs found in `local/`.")

    with u_col2:
        with st.popover("Settings", width="stretch"):
            st.markdown("**Appearance & Preferences**")
            appearance_picker()
            custom_appearance()
            st.divider()
            if st.button("🤖 " + ("Close AI Assistant" if st.session_state.get("assistant_open", False) else "Open AI Assistant"), key="btn_top_assistant", width="stretch"):
                st.session_state.assistant_open = not st.session_state.get("assistant_open", False)
                st.rerun()
            st.divider()
            st.caption("Interactive walkthrough tour")
            st.button("Start tutorial", key="start_tutorial_btn", width="stretch", type="secondary", on_click=start_tutorial, args=(source, names))
            if st.session_state.get("tutorial_active", False):
                curr_step = st.session_state.get("tutorial_step", 0)
                st.caption(f"Tour running: Step {curr_step + 1} of {len(TUTORIAL_STEPS)}")
                st.button("Exit tutorial", key="sidebar_exit_tutorial_btn", width="stretch", on_click=tutorial_exit)

# Top 4-Stage Horizontal Navigation Stepper
render_top_navigation(page, w)

st.markdown(f"**{PAGE_QUESTIONS[page]}**")
st.caption(PAGE_ACTIONS[page])
if current_tour_step() and page != current_tour_step()["page"]:
    render_tour_guide(w)

if st.session_state.get("confirm_reset_example"):
    with st.container(border=True):
        st.warning("⚠️ **Active Analysis in Progress**: The current workspace contains reviewed scenarios or custom evidence. Resetting will replace this workspace.")
        col_c1, col_c2 = st.columns(2)
        if col_c1.button("Yes, reset and load example", type="primary", key="btn_confirm_reset_yes", width="stretch"):
            start_example(source, names, force=True)
            st.rerun()
        if col_c2.button("Cancel, keep my current workspace", key="btn_confirm_reset_no", width="stretch"):
            st.session_state.pop("confirm_reset_example", None)
            st.rerun()

if w is None and page == "Data":
    with st.container(key="welcome"):
        st.markdown('<div class="basin-eyebrow">DECISION SUPPORT WORKBENCH</div><h2 class="welcome-title">Test drought stress scenarios<br>against regional water supplies.</h2><p class="welcome-copy">Resample 35 years of NOAA weather records, generate auditable drought scenarios, and test reservoir storage under stress.</p>', unsafe_allow_html=True)
        primary, secondary = st.columns(2)
        primary.button("Try an example", type="primary", on_click=start_example, args=(source, names), width="stretch")
        secondary.button("Take interactive walkthrough tour", key="welcome_tour", on_click=start_tutorial, args=(source, names), width="stretch")
        st.caption("Generates 300 multi-duration candidates across the 1991–2025 NOAA record and shortlists 6 diverse drought profiles (Seed 22). It is not a forecast.")
        st.markdown('<div class="welcome-steps"><span><b>01</b> Data Dashboard</span><span><b>02</b> Scenario Builder</span><span><b>03</b> Review Selections</span><span><b>04</b> Export</span></div>', unsafe_allow_html=True)

if page == "Data":
    saved_custom_panel(w)
    
    # 1. Direct Data & Focus Intake (High-density, 0-friction)
    intake_col1, intake_col2 = st.columns([1.6, 2.4])
    with intake_col1:
        st.markdown("**1. Select Data Source**")
        curr_d = st.session_state.get("run_focus_data", profile_defaults.data_source)
        d_idx = 1 if curr_d == "own" else 0
        chosen_data_mode = st.radio(
            "Data Source",
            ["🏛️ Regional NOAA Baseline", "📂 Upload Custom CSV"],
            index=d_idx,
            horizontal=True,
            label_visibility="collapsed",
            key="step1_data_mode_radio"
        )
        st.session_state["run_focus_data"] = "own" if "Upload" in chosen_data_mode else "standard"

    with intake_col2:
        st.markdown("**2. Analysis Focus (Tailors Review)**")
        goal_labels = {
            "storage": "🌊 Storage Stress",
            "operations": "🌾 Agronomics",
            "handoff": "📋 Regulatory Handoff",
            "compare": "⚖️ Comparison"
        }
        curr_g = st.session_state.get("run_focus_goal", profile_defaults.goal)
        g_keys = list(goal_labels.keys())
        g_idx = g_keys.index(curr_g) if curr_g in g_keys else 0
        if hasattr(st, "segmented_control"):
            chosen_goal = st.segmented_control(
                "Analysis Focus",
                g_keys,
                default=curr_g if curr_g in g_keys else "storage",
                format_func=goal_labels.get,
                label_visibility="collapsed",
                key="step1_goal_segmented"
            )
            if chosen_goal:
                st.session_state["run_focus_goal"] = chosen_goal
        else:
            chosen_goal = st.selectbox(
                "Analysis Focus",
                g_keys,
                index=g_idx,
                format_func=goal_labels.get,
                label_visibility="collapsed",
                key="step1_goal_selectbox"
            )
            st.session_state["run_focus_goal"] = chosen_goal

    local_rainfall_preview(expanded=(st.session_state.get("run_focus_data") == "own"))
    with tour_target("data_map"):
        metadata = pd.DataFrame(source.manifest["stations"]).rename(columns={"id": "station_id"})
        quality = pd.DataFrame(source.manifest["quality"])
        station_table = metadata.merge(quality, on="station_id")

        col_map, col_stn = st.columns([1.35, 1.0], gap="large")
        with col_map:
            col_map_title, col_map_tog = st.columns([1.8, 1.2])
            col_map_title.markdown("**Texas Regional Observation Map**")
            col_map_tog.toggle("🛰️ Satellite overlay", key="map_satellite_mode", help="Overlay high-resolution satellite imagery tiles (requires active internet connection). When off or offline, BASIN renders the baked-in Texas vector GIS map.")
            st.plotly_chart(basin_map(station_table), width="stretch", config={"displayModeBar": False})
            st.caption("Corpus Christi, Victoria & San Antonio airport observations are provisional regional proxies. Texas Vector GIS Map works 100% offline.")
        with col_stn:
            st.markdown("**Station Registry & Observation Quality**")
            st.caption("Station completeness and data quality flags across the 35-year NOAA observation record.")
            st.dataframe(
                station_table[["station_id", "name", "latitude", "longitude", "completeness_pct", "missing_or_excluded_days", "trace_days"]],
                hide_index=True, width="stretch", height=380,
                column_config={
                    "station_id": "ID",
                    "name": "Station Name",
                    "latitude": st.column_config.NumberColumn("Lat", format="%.2f"),
                    "longitude": st.column_config.NumberColumn("Lon", format="%.2f"),
                    "completeness_pct": st.column_config.NumberColumn("Complete %", format="%.3f"),
                    "missing_or_excluded_days": st.column_config.NumberColumn("Missing"),
                    "trace_days": st.column_config.NumberColumn("Trace"),
                }
            )
    tab_ts, tab_heatmap, tab_meta = st.tabs(["📈 Observed Time Series", "🗓️ 35-Year Drought Anomaly Matrix", "ℹ️ Snapshot Metadata & Quality Policy"])
    with tab_ts:
        left, right = st.columns([3, 1])
        station_view = left.multiselect("Observed rainfall", list(names), default=list(names), format_func=names.get)
        interval = right.selectbox("Interval", ["Annual", "Monthly", "Daily"])
        if station_view:
            observations = source.select(station_view)
            if interval == "Annual":
                groups = observations.groupby(observations.index.year)
                observed = groups.sum().where(groups.count().eq(groups.size(), axis=0))
            elif interval == "Monthly":
                groups = observations.resample("MS")
                observed = groups.sum().where(groups.count().eq(groups.size(), axis=0))
            is_us = st.session_state.get("unit_mode", "us") == "us"
            plot_obs = (observed / 25.4).round(2) if is_us else observed
            fig = go.Figure()
            for station in plot_obs:
                fig.add_trace(go.Scatter(x=plot_obs.index, y=plot_obs[station], name=names[station], mode="lines", connectgaps=False))
            fig.update_yaxes(title="Precipitation · inches" if is_us else "Precipitation · mm")
            st.plotly_chart(chart(fig, 350), width="stretch", config={"displayModeBar": False})
            st.markdown(f"**Synchronized Daily Observations ({'inches' if is_us else 'mm'})**")
            table_obs = (observations / 25.4).round(2) if is_us else observations.round(1)
            st.dataframe(table_obs, width="stretch", height=240)
    with tab_heatmap:
        st.markdown("**35-Year Monthly Climatological Anomaly Matrix (1991–2025)**")
        st.caption("Displays percentage departure from the 35-year monthly mean baseline for each month. Crimson cells indicate severe drought deficits; teal/emerald cells indicate rainfall surpluses. Exposes historical multi-month drought runs (such as 1996, 2011, and 2022) across the record.")
        c_hm_st, _ = st.columns([2, 2])
        hm_station_choice = c_hm_st.selectbox("Heatmap station perspective", ["Catchment composite (All stations average)", *[f"{names[s_id]} ({s_id})" for s_id in names]])
        if hm_station_choice.startswith("Catchment"):
            hm_obs = source.select(list(names))
            hm_title = "Catchment composite"
        else:
            selected_s_id = next(s_id for s_id in names if f"({s_id})" in hm_station_choice)
            hm_obs = source.select([selected_s_id])
            hm_title = names[selected_s_id]
        st.plotly_chart(accessible_chart(drought_anomaly_matrix_figure(hm_obs, title_prefix=hm_title)), width="stretch", config={"displayModeBar": False})
    with tab_meta:
        st.markdown("**Snapshot Metadata & Quality Policy**")
        st.caption("Cryptographic hashes and data quality assurance policies for this frozen baseline.")
        st.json(source.manifest)
    a, b, c = st.columns(3)
    a.download_button("Download station registry", metadata.to_csv(index=False), "stations.csv", "text/csv")
    b.download_button("Download methodology", (ROOT / "docs/methodology.md").read_bytes(), "BASIN-methodology.md", "text/markdown")
    schema_file = ROOT / "docs/export_schema.md"
    if schema_file.exists():
        c.download_button("Download export schema", schema_file.read_bytes(), "BASIN-export-schema.md", "text/markdown")
    else:
        c.download_button("Download export schema", (ROOT / "docs/methodology.md").read_bytes(), "BASIN-export-schema.md", "text/markdown")
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(source.manifest["downloaded_at"])).days
    st.info(f"🔒 **Verified NOAA Baseline Snapshot**: Downloaded {source.manifest['downloaded_at'][:10]} ({age} days ago). Pinned SHA-256: `{source.manifest['sha256'][:16]}…`")
    st.divider()
    with st.container():
        st.markdown('<div class="basin-gate-card">', unsafe_allow_html=True)
        st.markdown("**Step 1 Acceptance: Confirm Observation Baseline**")
        st.caption("Verify NOAA station proxies and data completeness before proceeding to scenario generation. Uploaded local rainfall CSVs (if any) are validated here.")
        def accept_data_baseline():
            st.session_state.data_accepted = True
            switch_page("Workspace")

        st.button(
            "✅ Accept Baseline & Proceed to Step 2: Scenario Builder ➔",
            key="btn_accept_data_baseline",
            type="primary",
            on_click=accept_data_baseline,
            width="stretch"
        )
        st.markdown('</div>', unsafe_allow_html=True)

elif w is None and page in ("Review", "Exports"):
    st.info("💡 **No Active Analysis Run**: This section is locked until scenarios are generated. Start in **Step 2: Scenario Builder** or click 'Try an example' below.")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.button("➔ Go to Step 2: Scenario Builder", key=f"btn_go_workspace_{page}", type="primary", on_click=switch_page, args=("Workspace",), width="stretch")
    with col_e2:
        st.button("Try an example", key=f"btn_try_example_{page}", on_click=start_example, args=(source, names), width="stretch")
    st.button("◀ Return to Step 1: Data Dashboard", key=f"btn_return_data_{page}", on_click=switch_page, args=("Data",), width="stretch")

elif page == "Workspace":
    st.markdown("**Which rainfall scenarios deserve a closer look?**")
    st.caption("Configure generation settings, establish ranking priorities, and examine candidate shortlists.")

    # Review focus is chosen before generation so the resulting run opens with the
    # relevant measurements and visuals leading. Repeated runs inherit the current
    # run's profile; the profile remains presentation-only.
    profile_context = w.id if w else "new-run"
    profile_defaults = review_preferences(w.id) if w else ReviewPreferences()
    if st.session_state.get("run_focus_context") != profile_context:
        st.session_state["run_focus_context"] = profile_context
        st.session_state["run_focus_goal"] = profile_defaults.goal
        st.session_state["run_focus_data"] = profile_defaults.data_source
        st.session_state["run_focus_guidance"] = profile_defaults.guidance
        st.session_state["run_focus_skip"] = profile_defaults.dismissed and not profile_defaults.configured

    with st.expander("⚙️ Analysis Focus & Settings (Optional)", expanded=False):
        st.caption("Configures which visuals and tools appear first in Review. Does not change numerical calculations or export consent.")
        focus_goal_col, focus_data_col, focus_guidance_col = st.columns(3)
        run_focus_goal = focus_goal_col.selectbox(
            "What are you trying to do?", list(GOALS),
            format_func=lambda key: GOALS[key]["label"], key="run_focus_goal",
            help="BASIN will place the related measurements and visuals first in Review.")
        run_focus_data = focus_data_col.selectbox(
            "Which data will you use?", list(DATA_SOURCES),
            format_func=lambda key: DATA_SOURCES[key]["label"], key="run_focus_data",
            help="This records your intent. It does not upload, validate, or replace data.")
        run_focus_guidance = focus_guidance_col.selectbox(
            "How much guidance do you want?", list(GUIDANCE),
            format_func=lambda key: GUIDANCE[key]["label"], key="run_focus_guidance",
            help="Guided explanations add orientation; all scientific limitations remain visible in either mode.")
        run_focus_skip = st.checkbox(
            "Skip tailoring and show every Review tool", key="run_focus_skip",
            help="You can tailor the Review later without losing work.")
        if run_focus_data == "own":
            has_custom = any(s.startswith("LOCAL_") for s in names)
            if has_custom:
                local_name = next(names[s] for s in names if s.startswith("LOCAL_"))
                st.success(f"✅ **Custom Gauge Active**: Generating scenarios from uploaded data: **{local_name}**.")
            else:
                st.info("📂 **Upload your rainfall CSV here to drive scenarios with your own gauge:**")
                local_rainfall_preview(expanded=True)
                st.caption("Tip: You can also explore full NOAA paired-station comparisons in Step 1: Data Dashboard.")
        elif run_focus_data == "example":
            col_ex1, col_ex2 = st.columns([2.5, 1.5])
            col_ex1.caption("⚡ The reproducible example pre-loads 6 diverse drought candidates (Seed 22).")
            col_ex2.button("🚀 Load Example Run ➔", key="btn_builder_load_example_inline", on_click=start_example, args=(source, names), type="primary", width="stretch")
        elif run_focus_skip:
            st.caption("This run will use the full Review layout. You can choose a focus later in Review.")

    # Scenario Generation & Priority Weights Builder
    c_gen, c_weights = st.columns([1, 1])
    with c_gen:
        with tour_target("sidebar_generator"):
            with st.form("generate", border=True):
                st.markdown("##### Resample Weather Windows")
                stations = st.multiselect("Stations", list(names), default=list(w.params.stations) if w else list(names), format_func=names.get)
                durations = st.multiselect("Durations · days", [30, 60, 90, 180, 270, 365], default=list(w.params.durations) if w else [90, 180, 270])
                months = st.multiselect("Starting months", list(range(1, 13)), default=list(w.params.months) if w else [1, 4, 7, 10], format_func=lambda m: calendar.month_abbr[m])
                retention = st.slider("Rainfall compared with original · %", 0, 100, (35, 85), 5,
                                      help="Multiply observed daily rainfall by this fraction at the affected stations.")
                extent = st.selectbox("Where reduced rainfall occurs", ["All stations", "One station", "Mixed"])
                a, b = st.columns(2)
                count = a.selectbox("Scenarios to test", [100, 300, 500, 1000], index=1)
                size = b.selectbox("Scenarios to review", [3, 4, 6, 8], index=2)
                seed = st.number_input("Repeatable run seed", 0, 4294967295, w.params.seed if w else 22)
                generate = st.form_submit_button("Create rainfall scenarios", type="primary", width="stretch")
        if generate:
            if not stations:
                st.error("⚠️ Select at least one station before generating scenarios.")
            elif not durations:
                st.error("⚠️ Select at least one duration window.")
            elif not months:
                st.error("⚠️ Select at least one starting calendar month.")
            else:
                try:
                    with st.spinner("Computing…"):
                        params = ScenarioParams(tuple(stations), tuple(durations), tuple(months), retention[0]/100, retention[1]/100, extent, count, int(seed))
                        new = Workspace(source, params, size)
                        if w:
                            new.notes = w.notes
                        st.session_state.workspace = new
                        st.session_state.data_accepted = True
                        st.session_state.scenarios_accepted = True
                        for key in list(st.session_state):
                            if key.startswith(("weight_", "review_", "note_", "edit_", "swap_", "provider_")):
                                del st.session_state[key]
                        st.session_state.pop("inspect_id", None)
                        st.session_state.pop("packet", None)
                        save(new)
                        run_preferences = ReviewPreferences(
                            goal=run_focus_goal,
                            data_source=run_focus_data,
                            guidance=run_focus_guidance,
                            configured=not run_focus_skip,
                            dismissed=True,
                        )
                        store_review_preferences(new.id, run_preferences)
                    st.rerun()
                except (ValueError, OSError) as error:
                    st.error(str(error))

    with c_weights:
        with tour_target("sidebar_presets"):
            with st.container(border=True):
                st.markdown("##### Ranking Priorities & Weights")
                preset_options = ["Custom weights"] + list(COMMUNITY_PRESETS.keys())
                matched = "Custom weights"
                curr_weights = dict(w.weights) if w else {"severity": 40, "duration": 30, "concurrence": 20, "season": 10}
                for p_name, p_vals in COMMUNITY_PRESETS.items():
                    if curr_weights == p_vals:
                        matched = p_name
                        break
                chosen_preset = st.selectbox("Community priority preset", preset_options,
                                             index=preset_options.index(matched),
                                             key=f"preset_select_{w.id if w else 'initial'}")
                if chosen_preset != "Custom weights" and chosen_preset != matched:
                    new_w = dict(COMMUNITY_PRESETS[chosen_preset])
                    for k, v in new_w.items():
                        st.session_state[f"weight_{k}"] = v
                    if w:
                        w.rerank(new_w)
                        save(w)
                        st.rerun()

                labels = {"severity": "How unusual vs history", "duration": "Longer scenarios",
                          "concurrence": "Stations stressed together", "season": "June–September timing"}
                weights = {k: st.slider(label, 0, 100, int(curr_weights[k]), key=f"weight_{k}") for k, label in labels.items()}
                if w:
                    if sum(weights.values()) == 0:
                        st.error("At least one weight must be positive.")
                    elif weights != w.weights:
                        w.rerank(weights)
                        save(w)
                    if st.button("Rebuild shortlist", key=f"btn_rebuild_shortlist_{w.id}", disabled=sum(weights.values()) == 0, width="stretch"):
                        try:
                            w.rebuild_shortlist()
                            save(w)
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))
                else:
                    st.caption("Illustrative weights will prioritize candidate severity, duration, concurrence, and seasonality when generated.")
                    st.button("Try an example", key="btn_example_in_builder", type="secondary", on_click=start_example, args=(source, names), width="stretch")

    # 2. Candidate Shortlist & Diversity Inspection
    if w is not None:
        selected = [w.get(i) for i in w.selected]
        decision_summary(w)
        approved_count = sum(s.status == "accepted" and s.approved_revision == s.revision for s in selected)
        st.caption(f"{len(selected)} scenarios selected for review · {approved_count} approved for export")
        view = table(w)
        st.markdown("**Compare rainfall shortfalls by duration**")
        st.caption("Each dot is a scenario. Panels share the same deficit scale; sideways spacing only separates dots. Rings mark selections for review, diamonds mark each duration's highest deficit, and the square marks the scenario shown in details.")
        plot_area, detail_area = st.columns([4, 1.3], gap="medium")
        with detail_area:
            detail_ids = view["ID"].tolist()
            initial_id = w.selected[0] if w.selected else detail_ids[0]
            focused_id = st.selectbox("Scenario details", detail_ids,
                                      index=detail_ids.index(initial_id), key=f"shortfall_detail_{w.id}")
            detail = view.loc[view["ID"] == focused_id].iloc[0]
            st.caption(f"{detail['Days']:g} days · {detail['Onset']} onset")
            is_us = st.session_state.get("unit_mode", "us") == "us"
            if is_us:
                st.metric("Total rainfall deficit", f"{detail['Deficit in']:,.2f} in", delta=f"{detail['Deficit mm']:,.1f} mm", delta_color="off")
            else:
                st.metric("Total rainfall deficit", f"{detail['Deficit mm']:,.1f} mm", delta=f"{detail['Deficit in']:,.2f} in", delta_color="off")
            st.caption(detail["Profile"])
            concurrence = float(detail["Stations stressed together %"])
            concurrence_label = (
                "30-day windows with all selected stations stressed"
                if len(w.params.stations) > 1
                else "Single Station Drought Stress Persistence"
            )
            st.progress(min(1.0, max(0.0, concurrence / 100)),
                        text=f"{concurrence_label}: {concurrence:.1f}%")
            st.caption("Selected for review" if focused_id in w.selected else "Not selected for review")
            st.button("Open scenario review", key=f"shortfall_review_{w.id}",
                      on_click=open_review, args=(focused_id,))
        with plot_area:
            is_us = st.session_state.get("unit_mode", "us") == "us"
            st.plotly_chart(rainfall_shortfall_figure(
                view, w.selected, focused_id,
                colorblind=st.session_state.get("appearance_colorblind", False),
                unit="in" if is_us else "mm",
            ), width="stretch", config={"displayModeBar": False})
        st.caption("Totals accumulate over the whole scenario. A larger deficit in a longer window does not, by itself, mean greater drought intensity.")
        st.button("Review selected scenarios", key="btn_review_selected_scenarios", on_click=open_review, args=(w.selected[0],), type="primary")

        tab_candidates, tab_ranking, tab_diagnostics = st.tabs([
            "📋 Candidate Scenarios & Filters",
            "🎯 Ranking Score Breakdown",
            "🔬 Selection Diagnostics"
        ])
        with tab_candidates:
            a, b, c, d = st.columns([2, 1, 1, 1])
            query = a.text_input("Find scenario", placeholder="Scenario ID")
            group_filter = b.selectbox("Group", ["All"] + sorted(view.Group.unique().tolist()))
            review_filter = c.selectbox("Status", ["All", "unreviewed", "accepted", "rejected"])
            only_selected = d.checkbox("Selected only", value=True)
            filtered = view[view.ID.str.contains(query, case=False, regex=False)].copy()
            if group_filter != "All":
                filtered = filtered[filtered.Group.eq(group_filter)]
            if review_filter != "All":
                filtered = filtered[filtered.Status.eq(review_filter)]
            if only_selected:
                filtered = filtered[filtered["Selected for review"]]
            filtered = filtered.sort_values(["Score", "ID"], ascending=[False, True]).reset_index(drop=True)
            with tour_target("workspace_table"):
                selection = st.dataframe(filtered, hide_index=True, width="stretch", height=min(430, 40+len(filtered)*35),
                                         on_select="rerun", selection_mode="single-row", key=f"candidates_{w.id}")
            rows = selection.selection.rows
            if rows and rows[0] < len(filtered):
                selected_id = filtered.iloc[rows[0]].ID
                st.button(f"Inspect {selected_id}", key=f"btn_inspect_table_{selected_id}", on_click=open_review, args=(selected_id,), type="primary")

        with tab_ranking:
            st.markdown("**How Ranking Scores Are Calculated**")
            st.caption("Contribution of severity, duration, concurrence, and season weights to each candidate's priority score.")
            fig = go.Figure()
            for key in w.weights:
                fig.add_trace(go.Bar(name=key.title(), y=[s.id for s in selected], x=[s.components[key] for s in selected], orientation="h"))
            fig.update_layout(barmode="stack")
            fig.update_xaxes(range=[0,100], title="Contribution to ranking score")
            st.plotly_chart(chart(fig, 290), width="stretch", config={"displayModeBar": False})

        with tab_diagnostics:
            st.markdown("**Selection Diagnostics & Algorithm Clustering**")
            st.dataframe(pd.DataFrame(comparison(w.scenarios, w.selected, w.params.seed)), hide_index=True, width="stretch")
            st.json({"clustering": w.clustering, "generation": w.generation, "selection_history": w.selection_history})

        comparison_panel(w, save)
        
        # Step 2 Acceptance Gate
        st.divider()
        with st.container():
            st.markdown('<div class="basin-gate-card">', unsafe_allow_html=True)
            st.markdown(f"**Step 2 Acceptance: Candidate Shortlist Confirmed ({len(w.selected)} Scenarios)**")
            st.caption("Accept these diverse drought scenarios to proceed to individual engineering review and reservoir drawdown sensitivity analysis.")
            def accept_shortlist():
                st.session_state.scenarios_accepted = True
                open_review(w.selected[0])

            st.button(
                "✅ Accept Shortlist & Proceed to Step 3: Review Selections ➔",
                key="btn_accept_shortlist",
                type="primary",
                on_click=accept_shortlist,
                width="stretch"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        st.button("◀ Back to Step 1: Data Dashboard", key="btn_nav_back_to_data", on_click=switch_page, args=("Data",), width="stretch")
    else:
        st.info("💡 Configure settings above and click 'Create rainfall scenarios' (or 'Try an example') to generate candidates.")
        st.button("◀ Back to Step 1: Data Dashboard", key="btn_nav_back_to_data_empty", on_click=switch_page, args=("Data",), width="stretch")

elif page == "Review":
    if w is None:
        st.info("💡 **No Active Analysis Run**: To review drought scenarios, first configure and start a run in **Scenario Builder**.")
        st.button("➔ Go to Step 2: Scenario Builder", key="btn_review_to_workspace_empty", on_click=switch_page, args=("Workspace",), type="primary")
    else:
        prefs = review_preferences(w.id)

        is_editing = st.session_state.get(f"review_editing_{w.id}", False)
        if prefs.needs_setup or is_editing:
            with st.container(border=True):
                st.markdown("#### Set up this Review (optional)")
                st.caption("Three questions decide which tools appear first. Every tool stays reachable, "
                           "and none of this changes calculations, ranking weights, review decisions or export consent.")
                setup_goal, setup_data, setup_guide = st.columns(3)
                chosen_goal = setup_goal.radio(
                    "What are you trying to do?", list(GOALS),
                    format_func=lambda key: GOALS[key]["label"],
                    captions=[GOALS[key]["help"] for key in GOALS], key="review_setup_goal")
                chosen_data = setup_data.radio(
                    "Which data will you use?", list(DATA_SOURCES),
                    format_func=lambda key: DATA_SOURCES[key]["label"],
                    captions=[DATA_SOURCES[key]["help"] for key in DATA_SOURCES], key="review_setup_data")
                chosen_guidance = setup_guide.radio(
                    "How much guidance do you want?", list(GUIDANCE),
                    format_func=lambda key: GUIDANCE[key]["label"],
                    captions=[GUIDANCE[key]["help"] for key in GUIDANCE], key="review_setup_guidance")
                if chosen_data == "own":
                    st.warning("This choice only records a preference; it does not upload or validate a file. "
                               "Existing data is unchanged. Add and review a CSV in Step 1: Data Dashboard when you are ready.")
                if chosen_data == "example":
                    st.caption("The example run opens from Step 1 or Step 2 using the existing 'Try an example' control.")
                if is_editing:
                    apply_col, cancel_col, skip_col = st.columns([1, 1, 1])
                    if apply_col.button("Use this focus", key="btn_review_setup_apply", type="primary", width="stretch"):
                        st.session_state[f"review_editing_{w.id}"] = False
                        store_review_preferences(w.id, prefs.replace(
                            goal=chosen_goal, data_source=chosen_data, guidance=chosen_guidance,
                            configured=True, dismissed=True))
                        st.rerun()
                    if cancel_col.button("Cancel", key="btn_review_setup_cancel", width="stretch"):
                        st.session_state[f"review_editing_{w.id}"] = False
                        st.rerun()
                    if skip_col.button("Skip for now", key="btn_review_setup_skip", width="stretch"):
                        st.session_state[f"review_editing_{w.id}"] = False
                        store_review_preferences(w.id, prefs.replace(configured=False, dismissed=True))
                        st.rerun()
                else:
                    apply_col, skip_col, _ = st.columns([1, 1, 2])
                    if apply_col.button("Use this focus", key="btn_review_setup_apply", type="primary", width="stretch"):
                        store_review_preferences(w.id, prefs.replace(
                            goal=chosen_goal, data_source=chosen_data, guidance=chosen_guidance,
                            configured=True, dismissed=True))
                        st.rerun()
                    if skip_col.button("Skip for now", key="btn_review_setup_skip", width="stretch"):
                        store_review_preferences(w.id, prefs.replace(dismissed=True))
                        st.rerun()
        else:
            focus_text, focus_toggle, focus_change = st.columns([3, 1, 1])
            focus_text.caption("**Review focus:** " + prefs.summary())
            show_all_tools = focus_toggle.toggle(
                "Show all tools", value=prefs.show_all_tools, key=f"review_show_all_tools_{w.id}",
                help="Show every Review tool in one row instead of only your focus.")
            if show_all_tools != prefs.show_all_tools:
                prefs = prefs.replace(show_all_tools=show_all_tools)
                store_review_preferences(w.id, prefs)
            if focus_change.button("Change focus", key=f"btn_review_change_focus_{w.id}", width="stretch"):
                st.session_state[f"review_editing_{w.id}"] = True
                st.session_state["review_setup_goal"] = prefs.goal
                st.session_state["review_setup_data"] = prefs.data_source
                st.session_state["review_setup_guidance"] = prefs.guidance
                st.rerun()
            if prefs.configured and prefs.data_source == "own":
                st.caption("Your focus records an intent to use your own rainfall data. Nothing has been uploaded or "
                           "validated by that choice; add a CSV in Step 1: Data Dashboard.")
            suggested = prefs.suggested_preset()
            if suggested:
                st.caption(f"This focus often pairs with the *{suggested}* ranking preset. Ranking weights are not "
                           "changed by your focus; apply a preset yourself in Step 2: Scenario Builder if you want it.")

        col_scen_sel, col_scen_opt = st.columns([3, 1])
        show_all_candidates = col_scen_opt.checkbox("Show all candidates", value=False, key=f"review_show_all_{w.id}", help="Expand dropdown beyond the 6 shortlisted candidates to all generated candidates")
        if show_all_candidates:
            candidates = w.selected + [s.id for s in w.scenarios if s.id not in w.selected]
        else:
            candidates = list(w.selected)
            current_inspect = st.session_state.get("inspect_id")
            if current_inspect and current_inspect not in candidates and w.has(current_inspect):
                candidates.insert(0, current_inspect)
        current = st.session_state.get("inspect_id", candidates[0])
        if current not in candidates:
            current = candidates[0]
        selected_id = col_scen_sel.selectbox("Scenario", candidates, index=candidates.index(current),
                                             format_func=lambda i: f"{i} · {w.get(i).status} · r{w.get(i).revision}" + (" · shortlisted" if i in w.selected else ""))
        st.session_state.inspect_id = selected_id
        s = w.get(selected_id)
        f = s.features
        is_us = st.session_state.get("unit_mode", "us") == "us"
        unit_arg = "in" if is_us else "mm"

        # Top section: Scenario overview and review decision side-by-side
        top_left, top_right = st.columns([2.1, 1.4], gap="large")
        with top_left:
            st.markdown("### Understand this scenario")
            st.info("📢 **Plain-Language Summary**: " + scenario_summary(f, names, unit_system="us" if is_us else "metric"))
            st.write(f"A {f['duration_days']}-day rainfall scenario using the historical window "
                     f"{s.provenance['source_start']} to {s.provenance['source_end']} at {len(s.series.columns)} selected station(s). "
                     "Decide whether this revision belongs in your rainfall handoff.")
            factors = list(s.provenance['retention_by_station'].values())
            if min(factors) == max(factors):
                construction = f"Original construction retained {factors[0]:.0%} of observed rainfall at every station."
            else:
                construction = f"Original construction retained {min(factors):.0%}–{max(factors):.0%} of observed rainfall, depending on station."
            rainfall_edits = any(h['action'] in ('scale', 'replace') for h in s.history)
            st.caption(construction + (" Later rainfall edits are included in the current chart; see revision history." if rainfall_edits else "")
                       + " Historical dates identify the source window; they are not forecast dates.")
            a, b = st.columns(2)
            shortfall_metric = f"{f['deficit_mm']/25.4:.2f} in ({f['deficit_mm']:.1f} mm)" if is_us else f"{f['deficit_mm']:.1f} mm ({f['deficit_mm']/25.4:.2f} in)"
            a.metric("Average station shortfall over this scenario", shortfall_metric,
                     help="Each station's total reference minus scenario rainfall is clipped at zero, then averaged equally across stations.")
            b.metric("Scenario duration", f"{f['duration_days']} days")
            st.caption("⚖️ **Catchment Weighting Disclosure**: Rainfall deficits and reference windows weight all selected stations equally (1/N arithmetic mean). No elevation or Thiessen polygon spatial weighting is applied without local calibration.")
            st.write(f"This shortfall equals or exceeds {f['historical_percentile']:.0%} of {f['benchmark_n']} matched historical windows "
                     "with the same duration, starting month and selected stations.")
            st.caption("This describes the historical comparison, not the probability of a future drought. Reference windows end by 2015.")

        with top_right:
            with tour_target("review_decision"):
                st.markdown("### Decide on the handoff")
                status_label = {"accepted": "Included", "rejected": "Excluded", "unreviewed": "Needs review"}[s.status]
                if s.status == "accepted" and s.approved_revision != s.revision:
                    status_label = "Needs review of current revision"
                st.write(f"**{s.id} · Revision {s.revision} · {status_label}**")
                pending = [i for i in w.selected if w.get(i).status == 'unreviewed' or
                           (w.get(i).status == 'accepted' and w.get(i).approved_revision != w.get(i).revision)]
                st.caption(f"{len(w.selected) - len(pending)} of {len(w.selected)} shortlisted scenarios reviewed")
                attached = set(w.evidence_refs[s.id])
                limitations = [e for e in w.evidence if e['id'] in attached and e['id'] == 'station-suitability']
                for item in limitations:
                    st.warning(item['description'])
                conflicts = [c for c in w.conflicts if c['status'] == 'unresolved' and
                             (c['left_id'] in attached or c['right_id'] in attached)]
                for conflict in conflicts:
                    st.warning("Unresolved evidence issue: " + conflict['disagreement'])
                note = st.text_area("Review note", key=f"note_{s.id}_{w.id}", height=90,
                                    help="Record why you are including or excluding this revision. Notes are private unless explicitly included during export.")
                st.caption("Inclusion records your choice of rainfall content. It does not certify hydrologic validity or approve the storage experiment.")
                if s.id not in w.selected:
                    st.info("This candidate is outside the shortlist. Use Edit Rainfall & Refine Shortlist below to replace an entry first.")
                with st.container(key="review_accept_box"):
                    if st.button("Include this revision in handoff", key=f"btn_accept_{s.id}_{s.revision}",
                                 type="primary", width="stretch", disabled=s.id not in w.selected):
                        s.review(True, note)
                        save(w)
                        st.rerun()
                    if st.button("⚡ Batch Accept All Shortlist", key=f"btn_batch_accept_shortlist_{w.id}",
                                 help="Batch-accept all current shortlist scenarios with a standard review note", width="stretch", disabled=s.id not in w.selected):
                        batch_note = note.strip() or "Accepted during holistic shortlist review."
                        for sid in w.selected:
                            w.get(sid).review(True, batch_note)
                        save(w)
                        st.rerun()
                if st.button("Exclude from handoff", key=f"btn_reject_{s.id}_{s.revision}", width="stretch", disabled=s.id not in w.selected):
                    try:
                        s.review(False, note)
                        save(w)
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
                remaining = [i for i in pending if i != s.id]
                st.button("Next unreviewed scenario", disabled=not remaining,
                          on_click=open_review, args=(remaining[0] if remaining else s.id,), width="stretch")

        # Tabs are ordered by the reader's focus. A focus reorders the page; it never
        # removes a tool, so every tab below lands in exactly one of the two groups.
        primary_keys, secondary_keys = prefs.tab_layout()
        panes = dict(zip(primary_keys, st.tabs([TAB_LABELS[key] for key in primary_keys])))
        if secondary_keys:
            expand_secondary = bool(curr_target == "review_simulation" and "storage" in secondary_keys)
            with st.expander(f"More tools ({len(secondary_keys)})", expanded=expand_secondary):
                st.caption("Everything outside your current focus. Nothing here is disabled, and your work is unchanged.")
                panes.update(zip(secondary_keys, st.tabs([TAB_LABELS[key] for key in secondary_keys])))
        if prefs.guided and prefs.configured:
            for pane_key, pane in panes.items():
                with pane:
                    st.caption(GUIDED_TAB_NOTES[pane_key])
        tab_storage = panes["storage"]
        tab_agro = panes["agronomics"]
        tab_rainfall = panes["rainfall"]
        tab_edits = panes["edits"]
        tab_provenance = panes["provenance"]

        with tab_storage:
            experiment = st.toggle("Explore storage under assumed conditions", value=curr_target == "review_simulation" or st.session_state.get("storage_experiment", False),
                                   key="storage_experiment", help="Show the optional storage experiment and its assumptions.")
            if experiment:
                with st.container(border=True):
                    st.caption("Optional experiment. These settings affect storage exploration; the handoff decision above concerns the rainfall revision.")

                    st.markdown("##### 💧 Water Storage System")
                    sys_options = list(SYSTEM_PRESETS.keys()) + ["Custom System Configuration..."]
                    curr_sys_choice = st.session_state.get(f"sys_preset_choice_{w.id}", sys_options[0])
                    sys_choice = st.selectbox("Storage Infrastructure", sys_options,
                                              index=sys_options.index(curr_sys_choice) if curr_sys_choice in sys_options else 0,
                                              key=f"sys_preset_choice_{w.id}",
                                              help="Select a regional preset or configure custom storage pools and demand for your local district or farm.")

                    if sys_choice == "Custom System Configuration...":
                        st.markdown("**Custom Infrastructure Setup**")
                        c_cname, c_csrcs, c_cdemand = st.columns([2, 1, 1])
                        cust_name = c_cname.text_input("System / District Name", value="Local Water District", key=f"cust_sys_name_{w.id}")
                        cust_n_sources = c_csrcs.selectbox("Number of Storage Pools", [1, 2, 3], index=0, key=f"cust_sys_n_{w.id}")
                        cust_demand = c_cdemand.number_input("Daily Demand (ac-ft/day)", min_value=0.1, value=12.0, step=1.0, key=f"cust_sys_demand_{w.id}")

                        src_list = []
                        for s_idx in range(cust_n_sources):
                            col_sn, col_scap = st.columns([2, 2])
                            s_name = col_sn.text_input(f"Source {s_idx+1} Name", value=f"Storage Pool {s_idx+1}", key=f"cust_src_name_{w.id}_{s_idx}")
                            s_cap = col_scap.number_input(f"Capacity (ac-ft)", min_value=1.0, value=8000.0 if s_idx == 0 else 4000.0, step=100.0, key=f"cust_src_cap_{w.id}_{s_idx}")
                            src_list.append(WaterSource.scaled_for_capacity(s_name, float(s_cap)))
                        chosen_sys = WaterSystemConfig(name=cust_name, sources=tuple(src_list), demand_acft_day=float(cust_demand))
                    else:
                        chosen_sys = SYSTEM_PRESETS[sys_choice]

                    sim_subview = st.radio(
                        "Simulation View",
                        ["Selected scenario", "Additional rainfall reductions"],
                        horizontal=True,
                        key="reservoir_sim_subview"
                    )
                    previous_config = st.session_state.get("experiment_config")
                    if isinstance(previous_config, ExperimentConfig) and previous_config.selected:
                        restored_settings = {
                            "review_initial_storage": f"{previous_config.initial_pct * 100:.0f}% (illustrative)",
                            "review_conservation": int(round(previous_config.conservation_pct * 100)),
                            "review_pipeline_active": previous_config.pipeline_active,
                        }
                        for setting_key, setting_value in restored_settings.items():
                            if setting_key not in st.session_state:
                                st.session_state[setting_key] = setting_value
                    c_pace, c_init, c_conserve = st.columns([1, 1, 1])
                    pace_choice = c_pace.selectbox("Playback pace", ["Slow", "Medium", "Fast"], label_visibility="visible")
                    pace_ms = 2500 if pace_choice == "Slow" else (800 if pace_choice == "Medium" else 150)
                    init_choice = c_init.selectbox("Initial storage", ["48% (illustrative)", "60% (illustrative)", "35% (illustrative)"], label_visibility="visible", key="review_initial_storage")
                    init_pct = 0.48 if "48%" in init_choice else (0.60 if "60%" in init_choice else 0.35)
                    conserve_choice = c_conserve.select_slider("Assumed demand reduction", options=[0, 10, 20, 30], value=0, format_func=lambda v: f"{v}%", label_visibility="visible", key="review_conservation")
                    pipeline_active = st.checkbox("Assume pipeline supply available", value=True, key="review_pipeline_active")

                    # Preserve the report integration contract through the optional Review UI.
                    st.session_state["experiment_config"] = ExperimentConfig(
                        initial_pct=init_pct,
                        conservation_pct=conserve_choice / 100.0,
                        pipeline_active=pipeline_active,
                        scenario_id=s.id,
                        scenario_revision=s.revision,
                        selected=True,
                        system_config=chosen_sys,
                    )
                    st.caption(f"Configured for **{chosen_sys.name}** ({chosen_sys.total_capacity_acft:,.0f} ac-ft total capacity, {chosen_sys.demand_acft_day:,.1f} ac-ft/day baseline demand). These settings are preserved for reports.")
                    st.info("⚠️ **Illustrative experiment**: conditional storage under assumed inputs. Not calibrated, not a forecast, and excluded from saved evidence packets and their verification.")

                    if sim_subview == "Additional rainfall reductions":
                        spec = simulate_stress_spectrum(s.series, initial_pct=init_pct, conservation_pct=conserve_choice/100.0, pipeline_active=pipeline_active, config=chosen_sys)
                        st.plotly_chart(accessible_chart(stress_spectrum_figure(spec)), width="stretch", config={"displayModeBar": False})

                        st.markdown("**Time spent in assumed storage bands**")
                        st.caption(f"Colors show storage bands during the simulated window ({', '.join(f'{b*100:.0f}%' for b in chosen_sys.stage_bands_pct)}). These boundaries are experiment assumptions, not official restriction triggers.")
                        st.plotly_chart(accessible_chart(stage_trigger_milestone_figure(spec, chosen_sys.stage_bands_pct)), width="stretch", config={"displayModeBar": False})

                        # Describe only the tested window and threshold crossings.
                        passed = [r for r in spec["summary_table"] if r["day_stage3_20"] is None]
                        failed = [r for r in spec["summary_table"] if r["day_stage3_20"] is not None]
                        crit_pct = chosen_sys.stage_bands_pct[2] * 100 if len(chosen_sys.stage_bands_pct) >= 3 else 20.0
                        if passed and failed:
                            lowest_pass = min(passed, key=lambda x: x["retention_pct"])
                            highest_fail = max(failed, key=lambda x: x["retention_pct"])
                            st.warning(
                                f"During this {len(s.series)}-day experiment, storage stays above {crit_pct:.0f}% with **{lowest_pass['retention_pct']:.0f}% of the selected scenario rainfall**, "
                                f"and reaches the assumed {crit_pct:.0f}% band with **{highest_fail['retention_pct']:.0f}%** on Day {highest_fail['day_stage3_20']}. Only these tested reductions are compared."
                            )
                        elif not failed:
                            st.success(f"Storage stays above the assumed {crit_pct:.0f}% band throughout this {len(s.series)}-day window for all tested rainfall inputs.")
                        else:
                            st.warning(f"All tested inputs reach the assumed {crit_pct:.0f}% band within this window. The selected scenario reaches it on Day {failed[0]['day_stage3_20']}.")

                        countdown_df = pd.DataFrame([
                            {
                                "Rainfall input": r["tier_label"],
                                "% of selected scenario": f"{r['retention_pct']:.0f}%",
                                "Lowest Storage": f"{r['min_pct']:.1f}% ({r['min_acft']:,.0f} ac-ft)",
                                "Final Storage": f"{r['final_pct']:.1f}%",
                                "At or below 40%": f"Day {r['day_stage1_40']}" if r["day_stage1_40"] else "Not reached in window",
                                "At or below 30%": f"Day {r['day_stage2_30']}" if r["day_stage2_30"] else "Not reached in window",
                                "At or below 20%": f"Day {r['day_stage3_20']}" if r["day_stage3_20"] else "Not reached in window",
                                "Critical band": "Not reached in window" if r["day_stage3_20"] is None else "Reached in window",
                                "Dead Storage / Day Zero": f"Day {r['day_zero']}" if r.get("day_zero") else ("Day " + str(r['day_dead_storage']) if r.get("day_dead_storage") else "Not reached"),
                            }
                            for r in spec["summary_table"]
                        ])
                        st.dataframe(countdown_df, hide_index=True, width="stretch")
                        st.caption("100% means the selected scenario, including any existing reductions and edits. Other inputs reduce that rainfall again; they do not reconstruct the original historical observations.")
                    else:
                        sim_df = simulate_reservoir_drawdown(s.series, initial_pct=init_pct, conservation_pct=conserve_choice/100.0, pipeline_active=pipeline_active, config=chosen_sys)

                        with tour_target("review_simulation"):
                            st.plotly_chart(accessible_chart(reservoir_simulation_figure(sim_df, pace_ms=pace_ms, config=chosen_sys)), width="stretch", config={"displayModeBar": False})
                            st.plotly_chart(accessible_chart(stage_trigger_milestone_figure({"tier_results": {1.0: {"df": sim_df}}}, chosen_sys.stage_bands_pct)), width="stretch", config={"displayModeBar": False})

                        # Dire Condition & Day Zero Warning
                        if sim_df["is_day_zero"].any():
                            day_zero_val = int(sim_df.loc[sim_df["is_day_zero"], "day"].iloc[0])
                            st.error(
                                f"🚨 **Day Zero Failure**: Reservoir storage entered the inactive dead storage reserve on **Day {day_zero_val}**. "
                                f"Intake pumps cavitate and raw water deliveries cease. Cumulative unserved demand reached **{sim_df['unmet_demand_acft'].sum():,.0f} ac-ft**."
                            )
                        elif sim_df["combined_pct"].min() <= 7.7 and ("Region N" in chosen_sys.name or "Corpus Christi" in chosen_sys.name):
                            st.warning(f"⚠️ **Historic Record Low Exceeded**: Storage dropped to **{sim_df['combined_pct'].min():.1f}%**, falling below the mid-April 2026 all-time low of 7.7% and the TWDB 75,000 ac-ft inactive reserve.")

                        s1 = next((r["day"] for _, r in sim_df.iterrows() if r["combined_pct"] < (chosen_sys.stage_bands_pct[0]*100 if len(chosen_sys.stage_bands_pct) >= 1 else 40)), None)
                        s2 = next((r["day"] for _, r in sim_df.iterrows() if r["combined_pct"] < (chosen_sys.stage_bands_pct[1]*100 if len(chosen_sys.stage_bands_pct) >= 2 else 30)), None)
                        s3 = next((r["day"] for _, r in sim_df.iterrows() if r["combined_pct"] < (chosen_sys.stage_bands_pct[2]*100 if len(chosen_sys.stage_bands_pct) >= 3 else 20)), None)
                        s4 = next((r["day"] for _, r in sim_df.iterrows() if r["combined_pct"] < (chosen_sys.stage_bands_pct[3]*100 if len(chosen_sys.stage_bands_pct) >= 4 else 10)), None)
                        term = sim_df.iloc[-1]
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Storage at window end", f"{term['combined_pct']:.1f}%")
                        m1.caption(f"{term['combined_acft']:,.0f} ac-ft combined")
                        m2.metric("Lowest combined storage", f"{sim_df['combined_pct'].min():.1f}%")
                        m3.metric("Below Stage 1 (40%)", f"Day {s1}" if s1 else "No crossing")
                        m4.metric("Below Stage 3 (20%)", f"Day {s3}" if s3 else "No crossing")

                        # Multi-Sector Delivery Breakdown
                        if "served_domestic_acft" in sim_df.columns and sim_df["served_demand_acft"].sum() > 0:
                            st.markdown("##### 👥 Multi-Sector Water Delivery")
                            sec1, sec2, sec3 = st.columns(3)
                            sec1.metric("Domestic Baseload", f"{sim_df['served_domestic_acft'].sum():,.0f} ac-ft")
                            sec2.metric("Industrial Contracted", f"{sim_df['served_industrial_acft'].sum():,.0f} ac-ft")
                            sec3.metric("Outdoor / Irrigation", f"{sim_df['served_outdoor_acft'].sum():,.0f} ac-ft")

                        # Pipeline Outage Resilience Counterfactual
                        if pipeline_active and getattr(chosen_sys, "pipeline_capacity_mgd", 0) > 0 and chosen_sys.demand_no_pipeline_acft_day is not None:
                            sim_no_pipe = simulate_reservoir_drawdown(s.series, initial_pct=init_pct, conservation_pct=conserve_choice/100.0, pipeline_active=False, config=chosen_sys)
                            crit_pct = chosen_sys.stage_bands_pct[2] * 100 if len(chosen_sys.stage_bands_pct) >= 3 else 20.0
                            s_crit_with = next((r["day"] for _, r in sim_df.iterrows() if r["combined_pct"] < crit_pct), None)
                            s_crit_without = next((r["day"] for _, r in sim_no_pipe.iterrows() if r["combined_pct"] < crit_pct), None)
                            if s_crit_with and s_crit_without and s_crit_with > s_crit_without:
                                st.info(f"🛡️ **Pipeline Resilience Metric**: The Mary Rhodes Pipeline ({chosen_sys.pipeline_capacity_mgd:.0f} MGD) extends the Stage 3 survival runway by **{s_crit_with - s_crit_without} days** compared to a total pipeline outage.")
                            elif s_crit_without and not s_crit_with:
                                st.info(f"🛡️ **Pipeline Resilience Metric**: The Mary Rhodes Pipeline ({chosen_sys.pipeline_capacity_mgd:.0f} MGD) completely prevents Stage 3 breach in this window (which breaches on Day {s_crit_without} under a pipeline outage).")

                        # TCEQ Emergency Inflow Status
                        if getattr(chosen_sys, "estuary_order_active", False) and sim_df["estuary_pass_through_acft"].sum() == 0:
                            st.caption(f"🌿 **TCEQ 2026 Emergency Inflow Order Active**: Estuary pass-through suspended while storage ≤ {getattr(chosen_sys, 'estuary_threshold_pct', 0.50)*100:.0f}%, retaining 100% of inflow in municipal storage.")

                        st.info("📢 **Operational Takeaway**: " + reservoir_summary(sim_df, chosen_sys.name))
                        st.caption(f"Results cover this {len(s.series)}-day window only. Capacity and operational parameters are illustrative assumptions. Threshold timing is conditional on these settings; it is not an official restriction date. Experiment settings are retained for this workspace during the session; opening another workspace resets them.")

                        with st.expander("🏛️ Regional Policy & 'Day Zero' Context (Corpus Christi / Region N)", expanded=False):
                            st.markdown(
                                """
                                **The 'First City in America to Run Out of Water' Narrative vs. Operational Realities:**
                                - **National Coverage vs. City Rebuttal**: Throughout early-to-mid 2026, national reports (*Texas Tribune*, *Inside Climate News*, *Circle of Blue*, *Futurism*, *Deceleration News*) highlighted projections that Corpus Christi could become America's first modern "Day Zero" metropolis when combined storage plummeted to an all-time low of **7.7% in mid-April 2026**. The City pushed back, clarifying that a **Level 1 Water Emergency** is an administrative 180-day planning trigger, and that the **Mary Rhodes Pipeline** (70–72 MGD) guarantees a firm regional baseload (~70% of demand) preventing complete dry-pipe failure even if reservoirs hit dead pool.
                                - **The Fair Water Charter Amendment (Nov 3, 2026 Ballot)**: On August 11, 2026, City Council voted 6–2 to place a charter amendment on the ballot (prompted by ~13,000 citizen signatures) to eliminate the **Drought Surcharge Exemption Fee (DSEF)**. Under DSEF, industrial plants consuming >50% of regional potable water paid $0.31/kGal to bypass drought surcharges, while residents faced 20 months of Stage 3 sprinkler bans and $4–$8/kGal surcharges.
                                - **Simulating Policy Choices in BASIN**: The Multi-Sector Water Delivery metrics above reflect these dynamics. When combined storage breaches Stage 4 (10%), BASIN models the Fair Water policy mandate by curtailing industrial demand by 30% and outdoor use by 100%, protecting essential domestic baseload and extending reservoir lifespan.
                                """
                            )

        with tab_agro:
            st.caption("Cross-sector operational impacts calculated from daily scenario rainfall. Illustrative decision-support estimates based on Texas ET Network and Texas A&M Forest Service guidelines; not regulatory declarations or official crop/burn directives.")
            c_agro_tab, c_fire_tab = st.tabs(["🌾 Crop Water Deficit (ETc)", "🔥 Wildfire Risk (KBDI)"])
            with c_agro_tab:
                st.markdown("##### 🌾 Crop Evapotranspiration & Irrigation Deficit")
                c1, c2 = st.columns([2, 1])
                crop_choice = c1.selectbox("Crop Type", list(CROP_COEFFICIENTS.keys()), key=f"crop_sel_{s.id}_{w.id}")
                crop_def = calculate_crop_water_deficit(s.series, crop_name=crop_choice)
                c2.metric("Crop Coefficient (Kc)", f"{crop_def['kc']:.2f}")

                a1, a2, a3, a4 = st.columns(4)
                if is_us:
                    a1.metric("Scenario Rainfall", f"{crop_def['total_rain_in']:.2f} in")
                    a2.metric("Reference ET (ETo)", f"{crop_def['total_eto_in']:.2f} in")
                    a3.metric("Crop ET (ETc)", f"{crop_def['total_etc_in']:.2f} in")
                    a4.metric("Net Irrigation Deficit", f"{crop_def['irrigation_gap_in']:.2f} in/acre")
                else:
                    a1.metric("Scenario Rainfall", f"{crop_def['total_rain_mm']:.1f} mm")
                    a2.metric("Reference ET (ETo)", f"{crop_def['total_eto_in']*25.4:.1f} mm")
                    a3.metric("Crop ET (ETc)", f"{crop_def['total_etc_in']*25.4:.1f} mm")
                    a4.metric("Net Irrigation Deficit", f"{crop_def['irrigation_gap_mm']:.1f} mm")

                st.info("📢 **Agronomic Takeaway**: " + crop_def["takeaway"])

                st.markdown("**Monthly Water Demand vs Rainfall Breakdown**")
                m_df = pd.DataFrame(crop_def["monthly_summary"])
                st.dataframe(m_df, hide_index=True, width="stretch")

            with c_fire_tab:
                st.markdown("##### 🔥 Keetch-Byram Drought Index (KBDI) & Wildfire Stress")
                f1, f2 = st.columns([2, 1])
                start_kbdi = f1.slider("Starting KBDI (Soil Dryness)", 0, 800, 400, 10, key=f"kbdi_start_{s.id}_{w.id}",
                                      help="0 = fully saturated soil, 800 = extreme drought. Texas county commissioners courts frequently evaluate outdoor burn bans around KBDI 575–600 (illustrative decision support, not an official declaration).")
                kbdi_res = calculate_kbdi(s.series, initial_kbdi=float(start_kbdi))
                f2.metric("Danger Class", kbdi_res.danger_class)

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Initial KBDI", f"{kbdi_res.initial_kbdi:.0f}")
                k2.metric("Peak KBDI", f"{kbdi_res.peak_kbdi:.0f}")
                k3.metric("Final KBDI", f"{kbdi_res.final_kbdi:.0f}")
                k4.metric("Burn Ban Trigger (≥600)", "⚠️ Triggered (Illustrative)" if kbdi_res.burn_ban_breached else "✅ Below 600")

                if kbdi_res.burn_ban_breached:
                    st.warning(f"🚨 **Illustrative Burn Ban Threshold Breached**: KBDI reaches {kbdi_res.peak_kbdi:.0f} on Day {kbdi_res.burn_ban_day}. Texas county commissioners courts evaluate outdoor burn bans around KBDI ≥ 600 as decision support; this is an illustrative modeling threshold, not a statutory declaration.")
                else:
                    st.success(f"✅ KBDI peaks at {kbdi_res.peak_kbdi:.0f}, remaining below typical county burn-ban triggers (600).")

                st.info("📢 **Operational Takeaway**: " + kbdi_res.takeaway)
                st.caption("KBDI and crop water balance models provide exploratory scenario impacts. Official burn bans are enacted exclusively by County Commissioners Courts under Tex. Local Gov't Code § 352.081. Reservoir stages reflect illustrative operating rules, not municipal emergency orders.")

        with tab_rainfall:
            st.markdown("### Compare rainfall with its reference")
            station = st.selectbox("Station to compare", list(s.series.columns), format_func=lambda i: names[i], key=f"review_station_{w.id}")
            mode = st.radio("Rainfall view", ["Cumulative rainfall", "Daily rainfall", "30-day deficit"], horizontal=True, key="review_rainfall_view")
            expected = pd.DataFrame(w.reference.expected(s.series.index), index=s.series.index, columns=s.series.columns)
            fig = rainfall_reference_figure(s.series[station], expected[station], mode, unit=unit_arg)
            fig = chart(fig, 340)
            if mode != "30-day deficit":
                fig.data[0].line.dash = "dash"
                fig.data[1].line.dash = "solid"
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            actual_total, reference_total = s.series[station].sum(), expected[station].sum()
            difference = reference_total - actual_total
            if is_us:
                st.write(f"Over these {len(s.series)} days, **{names[station]}** receives **{actual_total/25.4:.2f} in ({actual_total:.1f} mm)** in the scenario "
                         f"versus **{reference_total/25.4:.2f} in ({reference_total:.1f} mm)** in the reference: **{abs(difference)/25.4:.2f} in ({abs(difference):.1f} mm) {'less' if difference >= 0 else 'more'} rainfall**.")
            else:
                st.write(f"Over these {len(s.series)} days, **{names[station]}** receives **{actual_total:.1f} mm ({actual_total/25.4:.2f} in)** in the scenario "
                         f"versus **{reference_total:.1f} mm ({reference_total/25.4:.2f} in)** in the reference: **{abs(difference):.1f} mm ({abs(difference):.1f} in) {'less' if difference >= 0 else 'more'} rainfall**.")
            st.caption("The dashed reference uses this station's 1991–2020 monthly mean daily rainfall. The scenario line includes your current edits.")
            if mode == "30-day deficit":
                st.caption("Above zero means less rainfall than the reference over the preceding 30 days; below zero means more. The first 29 days have no complete window.")

            st.markdown("#### Historical Comparison & Ranking Details")
            if len(w.params.stations) == 1:
                st.write(f"Single Station Drought Stress Persistence: {f['concurrence']:.1%} of {f['eligible_concurrence_days']} eligible windows.")
                st.caption("Windows where this single station exceeds its historical rainfall-deficit threshold. Multi-station concurrence requires >=2 stations.")
            else:
                st.write(f"30-day windows with all selected stations stressed: {f['concurrence']:.1%} of {f['eligible_concurrence_days']} eligible windows.")
                st.caption("Each station must exceed its own historical rainfall-deficit threshold in the same window. This is a frequency over time, not a percentage of stations.")
            st.write(f"Largest shortfall in the matched historical reference: {f['benchmark_mm']:.1f} mm ({f['benchmark_mm']/25.4:.2f} in). "
                     f"This scenario {'exceeds' if f['beyond_rainfall_reference'] else 'does not exceed'} that value.")
            if f.get("benchmark_2025_mm") is not None:
                st.caption(f"Extended 1991–2025 historical record benchmark (including 2022 drought): {f['benchmark_2025_mm']:.1f} mm ({f['benchmark_2025_mm']/25.4:.2f} in) across {f.get('benchmark_2025_n', 35)} windows.")
            st.write(f"Ranking score: {s.score:.2f}. This reflects your priorities; it is not a probability or an evidence-quality score.")

        with tab_edits:
            st.caption("Changing rainfall creates a revision and clears its previous acceptance. Add your reason in the review note first.")
            col_scale, col_csv, col_swap = st.columns(3, gap="large")
            with col_scale:
                st.markdown("##### 1. Scale Rainfall")
                factor = st.number_input("Multiplier", 0.0, 2.0, 0.8, 0.05, key=f"edit_{s.id}_{w.id}")
                if st.button("Apply multiplier", key=f"btn_apply_multiplier_{s.id}_{s.revision}", width="stretch"):
                    try:
                        w.edit(s.id, note, factor=factor)
                        save(w)
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
            with col_csv:
                st.markdown("##### 2. Replace from CSV")
                st.download_button("CSV template", s.series.rename_axis("date").to_csv(), f"{s.id}-template.csv", "text/csv", key=f"dl_template_{s.id}_{s.revision}", width="stretch")
                upload = st.file_uploader("Daily rainfall · mm", type="csv", key=f"replacement_{w.id}_{s.id}")
                if st.button("Apply CSV", key=f"btn_apply_csv_{s.id}_{s.revision}", disabled=upload is None, width="stretch"):
                    try:
                        replacement = pd.read_csv(upload, index_col="date", parse_dates=["date"])
                        w.edit(s.id, note, replacement=replacement)
                        save(w)
                        st.rerun()
                    except (ValueError, KeyError, TypeError) as error:
                        st.error(str(error))
            with col_swap:
                st.markdown("##### 3. Shortlist Candidates")
                if s.id in w.selected:
                    alternatives = [x.id for x in w.scenarios if x.id not in w.selected and x.status != "rejected"]
                    if alternatives:
                        other = st.selectbox("Candidate", alternatives, format_func=lambda i: f"{i} · {w.get(i).score:.1f}", key=f"sel_alt_{s.id}_{w.id}")
                        if st.button("Replace entry", key=f"btn_replace_entry_{s.id}_{w.id}", width="stretch"):
                            st.session_state["last_swap"] = (s.id, other)
                            w.swap(s.id, other)
                            save(w)
                            st.session_state.inspect_id = other
                            st.rerun()
                    if "last_swap" in st.session_state:
                        last_out, last_in = st.session_state["last_swap"]
                        if last_in in w.selected:
                            if st.button(f"↩️ Undo Swap ({last_in} ➔ {last_out})", key=f"btn_undo_swap_{w.id}", width="stretch"):
                                w.swap(last_in, last_out)
                                st.session_state.inspect_id = last_out
                                del st.session_state["last_swap"]
                                save(w)
                                st.rerun()
                else:
                    old = st.selectbox("Replace shortlisted scenario", w.selected, key=f"sel_shortlist_target_{s.id}_{w.id}")
                    if st.button("Use this candidate", key=f"btn_use_candidate_{s.id}_{w.id}", disabled=s.status == "rejected", width="stretch"):
                        w.swap(old, s.id)
                        save(w)
                        st.rerun()

        with tab_provenance:
            evidence_tab, data_tab, history_tab = st.tabs(["Source evidence", "Daily values", "Revision history"])
            with data_tab:
                edited = st.data_editor(s.series.rename_axis("date"), width="stretch", height=300,
                                        key=f"daily_editor_{w.id}_{s.id}_{s.revision}",
                                        column_config={col: st.column_config.NumberColumn(names[col] + " · mm", min_value=0, format="%.3f") for col in s.series})
                c_note, c_save = st.columns([3, 1])
                daily_note = c_note.text_input("Edit rationale", value=note, key=f"daily_note_{w.id}_{s.id}_{s.revision}", placeholder="Reason for adjusting daily rainfall")
                if c_save.button("Save daily edits", key=f"btn_save_daily_edits_{s.id}_{s.revision}", width="stretch"):
                    if not daily_note.strip():
                        st.warning("Please enter a brief rationale for the edit.")
                    elif edited.to_numpy().tolist() == s.series.to_numpy().tolist():
                        st.info("No daily values were modified.")
                    else:
                        try:
                            w.edit(s.id, daily_note, replacement=edited)
                            save(w)
                            st.rerun()
                        except (ValueError, TypeError) as error:
                            st.error(str(error))
            with evidence_tab:
                is_us = st.session_state.get("unit_mode", "us") == "us"
                ev_data = {
                    "Station": list(s.provenance["retention_by_station"]),
                    "Scenario rainfall (fraction of observed)": list(s.provenance["retention_by_station"].values()),
                    "Current deficit mm": [f["station_deficits_mm"][i] for i in s.provenance["retention_by_station"]],
                }
                if is_us:
                    ev_data["Current deficit in"] = [round(f["station_deficits_mm"][i] / 25.4, 2) for i in s.provenance["retention_by_station"]]
                st.dataframe(pd.DataFrame(ev_data), hide_index=True, width="stretch")
                evidence_panel(w, s, save)
                st.json({"source": s.provenance, "features": f, "score_contributions": s.components, "snapshot_sha256": source.manifest["sha256"]})
            with history_tab:
                if s.history:
                    st.dataframe(pd.DataFrame([{k:v for k,v in event.items() if k != "replacement_values"} for event in s.history]), hide_index=True, width="stretch")
                else:
                    st.caption("No revisions or review decisions")
    st.divider()
    all_reviewed = all(w.get(i).status in ("accepted", "rejected") for i in w.selected)
    has_accepted = any(w.get(i).status == "accepted" for i in w.selected)
    export_ready = all_reviewed and has_accepted and all(
        w.get(i).approved_revision == w.get(i).revision for i in w.selected if w.get(i).status == "accepted")

    with st.container():
        st.markdown('<div class="basin-gate-card">', unsafe_allow_html=True)
        g_r1, g_r2 = st.columns([3, 2])
        with g_r1:
            if export_ready:
                st.markdown(f"**Review complete · {sum(w.get(i).status == 'accepted' for i in w.selected)} scenarios included**")
                st.caption("All shortlisted scenarios have documented review decisions. Step 4 (Export) is unlocked.")
            else:
                unreviewed_count = len(pending)
                st.markdown(f"**{unreviewed_count} scenarios still need a decision**" if unreviewed_count
                            else "**All shortlisted scenarios are excluded. Include at least one to prepare a handoff.**")
                st.caption("Record an include or exclude decision for each shortlisted scenario before preparing the handoff.")
        with g_r2:
            st.button(
                "Proceed to Step 4: Export ➔",
                key="btn_nav_to_exports",
                type="primary",
                disabled=not export_ready,
                on_click=switch_page,
                args=("Exports",),
                width="stretch"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    st.button("◀ Back to Step 2: Scenario Builder", key="btn_nav_back_to_workspace", on_click=switch_page, args=("Workspace",), width="stretch")

elif page == "Exports":
    if w is None:
        st.info("💡 **No Active Analysis Run**: To prepare and verify an export packet, first configure and run scenarios in **Scenario Builder**.")
        st.button("➔ Go to Step 2: Scenario Builder", key="btn_exports_to_workspace_empty", on_click=switch_page, args=("Workspace",), type="primary")
    else:
        chosen = [w.get(i) for i in w.selected]
        st.markdown("**Review what your recipient will receive**")
        st.caption("A readable rainfall brief, daily values, source evidence and a replayable audit. Review decisions control what can be exported.")

        # Single experiment configuration every report on this page is generated from.
        experiment_config = st.session_state.get("experiment_config")
        if not isinstance(experiment_config, ExperimentConfig):
            experiment_config = ExperimentConfig()

        col_export_ctrl, col_export_view = st.columns([1.0, 1.45], gap="large")

        with col_export_ctrl:
            st.markdown("#### 1. Export Controls & Verification")
            share = st.checkbox("Include provider notes and free-text review notes", value=False, key=f"share_notes_{w.id}")
            share_custom = False
            if w.custom_uploads:
                st.warning("This analysis contains custom evidence. Replay requires all saved normalized upload versions, station/location/source metadata and suitability rationale.")
                share_custom = st.checkbox("Include custom numerical inputs and source metadata in this replayable export", key="custom_export_" + digest(w.custom_uploads))

            def report_token(accepted_scenarios):
                return report_state_token({"id": w.id, "content": digest(w.record(share, include_custom=True))}, accepted_scenarios, share, share_custom, experiment_config)

            # 1. READINESS GATE & PRIMARY EXPORT TRIGGER
            try:
                w.exportable()
                ready = True
                st.success("✅ **Export verified:** All shortlisted candidates are reviewed and ready for bundle generation.")
            except ValueError as error:
                ready = False
                st.warning(f"⚠️ **Export prerequisite:** {error}")
                unreviewed = [s for s in chosen if s.status == "unreviewed" or (s.status == "accepted" and s.approved_revision != s.revision)]
                if unreviewed:
                    st.info(
                        f"**{len(unreviewed)} shortlisted candidate(s) require review before export:** "
                        f"{', '.join(s.id for s in unreviewed)}.\n\n"
                        "BASIN's scientific provenance standard requires each shortlisted scenario to have a deliberate human decision (Accept or Reject) before generating a verified engineering bundle."
                    )
                    col_a, col_b = st.columns([1, 1])
                    if col_a.button("✅ Accept all shortlisted for export", key="btn_accept_all_for_export", type="primary"):
                        for s in unreviewed:
                            s.review(True, "Accepted during export preparation")
                        save(w)
                        st.success("All shortlisted candidates accepted.")
                        st.rerun()
                    if col_b.button("🔍 Review candidates in Review tab", key="btn_goto_review_tab"):
                        switch_page("Review")
                        st.rerun()

            with tour_target("export_panel"):
                if not ready:
                    st.warning("⚠️ **Export locked:** Review decisions required before generating verified bundle. Use '✅ Accept all shortlisted for export' above to unlock.")
                elif bool(w.custom_uploads) and not share_custom:
                    st.warning("⚠️ **Custom Evidence Consent Required:** Check 'Include custom numerical inputs and source metadata' above to enable verified export.")
                if st.button("Build verified export", key="btn_build_verified_export", type="primary", disabled=not ready or (bool(w.custom_uploads) and not share_custom)):
                    try:
                        payload = export_bundle(w, share, include_custom=share_custom)
                        report = verify_bundle(payload)
                        out_dir = ROOT / "output"
                        out_dir.mkdir(parents=True, exist_ok=True)
                        zip_path = out_dir / f"BASIN-{w.id}.zip"
                        zip_path.write_bytes(payload)
                        brief_text = generate_brief(w, w.exportable())
                        brief_path = out_dir / f"Hydrologist_Handoff_Brief_{w.id}.md"
                        brief_path.write_text(brief_text, encoding="utf-8")
                        pdf_bytes = generate_pdf_report(w, w.exportable(), include_notes=share, config=experiment_config)
                        pdf_path = out_dir / f"BASIN-Executive-Brief-{w.id}.pdf"
                        pdf_path.write_bytes(pdf_bytes)

                        # Build Excel deliverable (.xlsx)
                        import io
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                            shortlist_df = pd.DataFrame([summary_record(sc) for sc in w.exportable()])
                            shortlist_df.to_excel(writer, sheet_name="Shortlist_Summary", index=False)
                            rainfall_df = pd.concat([rainfall_rows(sc) for sc in w.exportable()])
                            rainfall_df.to_excel(writer, sheet_name="Daily_Rainfall", index=False)
                            pd.DataFrame([
                                {"Property": "Run ID", "Value": w.id},
                                {"Property": "Created At", "Value": w.created_at},
                                {"Property": "Snapshot SHA-256", "Value": w.source.manifest.get("sha256", "")},
                            ]).to_excel(writer, sheet_name="Run_Metadata", index=False)
                        xlsx_bytes = excel_buffer.getvalue()
                        xlsx_path = out_dir / f"BASIN-Shortlist-{w.id}.xlsx"
                        xlsx_path.write_bytes(xlsx_bytes)

                        st.session_state.packet = {
                            "data": payload,
                            "pdf_bytes": pdf_bytes,
                            "brief_text": brief_text,
                            "xlsx_bytes": xlsx_bytes,
                            "saved_pdf": str(pdf_path.name),
                            "saved_zip": str(zip_path.name),
                            "saved_brief": str(brief_path.name),
                            "saved_xlsx": str(xlsx_path.name),
                            "fingerprint": json.dumps(w.record(share, include_custom=share_custom), sort_keys=True),
                            "share": share,
                            "custom": share_custom,
                            "config": experiment_config.fingerprint(),
                            "token": report_token(w.exportable()),
                            "report": report
                        }
                        st.success(f"✅ Verified deliverables generated and saved to disk: `output/{pdf_path.name}`, `output/{zip_path.name}`, and `output/{xlsx_path.name}`")
                    except (ValueError, AssertionError, OSError) as error:
                        st.error(f"Verification failed: {error}")

            # 2. GENERATED DELIVERABLES STAGE (MAIN PDF, EXCEL & ZIP DOWNLOAD CARDS)
            packet = st.session_state.get("packet")
            try:
                current_fingerprint = json.dumps(w.record(share, include_custom=share_custom), sort_keys=True)
            except ValueError:
                current_fingerprint = None

            packet_fresh = bool(
                packet
                and (not w.custom_uploads or share_custom)
                and packet.get("custom", False) == share_custom
                and packet.get("share") == share
                and packet.get("config") == experiment_config.fingerprint()
                and current_fingerprint is not None
                and packet.get("fingerprint") == current_fingerprint
            )
            if packet and not packet_fresh:
                st.session_state.pop("packet", None)
                packet = None
                st.info("Inputs, experiment settings or consent changed since the last export. Rebuild the verified export to download it again.")

            disk_zip = ROOT / "output" / f"BASIN-{w.id}.zip"
            disk_pdf = ROOT / "output" / f"BASIN-Executive-Brief-{w.id}.pdf"
            disk_xlsx = ROOT / "output" / f"BASIN-Shortlist-{w.id}.xlsx"
            if not packet_fresh and disk_zip.exists() and disk_pdf.exists():
                st.info(f"📦 **Existing Verified Deliverables on Disk** for run `{w.id}`. You can download previously saved files or rebuild above.")
                c_d1, c_d2, c_d3, c_d4 = st.columns([1, 1, 1, 1])
                c_d1.download_button("Download Saved PDF", disk_pdf.read_bytes(), disk_pdf.name, "application/pdf", key=f"dl_disk_pdf_{w.id}", width="stretch")
                c_d2.download_button("Download Saved ZIP", disk_zip.read_bytes(), disk_zip.name, "application/zip", key=f"dl_disk_zip_{w.id}", width="stretch")
                if disk_xlsx.exists():
                    c_d3.download_button("Download Saved Excel", disk_xlsx.read_bytes(), disk_xlsx.name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_disk_xlsx_{w.id}", width="stretch")
                if c_d4.button("Open Output Folder", key=f"btn_open_disk_out_{w.id}", width="stretch"):
                    import subprocess, sys
                    out_folder = ROOT / "output"
                    if sys.platform == "win32":
                        subprocess.Popen(["explorer", str(out_folder.resolve())])
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", str(out_folder.resolve())])
                    else:
                        subprocess.Popen(["xdg-open", str(out_folder.resolve())])

            if packet_fresh:
                st.success(
                    "✅ **Verified Export Package Ready** — SHA-256 integrity verified for the replay ZIP bundle. "
                    "The companion Executive Brief (PDF) and Shortlist Workbook (Excel) provide decision-ready deliverables for water board and council presentation."
                )

                pdf_data = packet.get("pdf_bytes")
                if pdf_data:
                    st.download_button(
                        "Download Executive Brief (PDF)",
                        pdf_data,
                        f"BASIN-Executive-Brief-{w.id}.pdf",
                        "application/pdf",
                        key=f"dl_pdf_main_{w.id}",
                        type="primary",
                        width="stretch"
                    )

                st.markdown("**Companion Deliverables & Replay Package:**")
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button("Download Replay ZIP", packet["data"], f"BASIN-{w.id}.zip", "application/zip", key=f"dl_zip_{w.id}", width="stretch")
                with col_dl2:
                    brief_bytes = packet.get("brief_text", "").encode("utf-8") if packet.get("brief_text") else b""
                    st.download_button("Download Brief (.md)", brief_bytes, f"Hydrologist_Handoff_Brief_{w.id}.md", "text/markdown", key=f"dl_brief_export_{w.id}", width="stretch")
                col_dl3, col_dl4 = st.columns(2)
                with col_dl3:
                    xlsx_data = packet.get("xlsx_bytes")
                    if xlsx_data:
                        st.download_button("Download Shortlist (.xlsx)", xlsx_data, f"BASIN-Shortlist-{w.id}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_xlsx_{w.id}", width="stretch")
                with col_dl4:
                    if st.button("Open Output Folder", key=f"btn_open_out_folder_{w.id}", width="stretch"):
                        import subprocess, sys
                        out_folder = ROOT / "output"
                        if sys.platform == "win32":
                            subprocess.Popen(["explorer", str(out_folder.resolve())])
                        elif sys.platform == "darwin":
                            subprocess.Popen(["open", str(out_folder.resolve())])
                        else:
                            subprocess.Popen(["xdg-open", str(out_folder.resolve())])
                st.caption(f"📁 Local copies on disk: `output/{packet.get('saved_pdf', f'BASIN-Executive-Brief-{w.id}.pdf')}`, `output/{packet.get('saved_zip', f'BASIN-{w.id}.zip')}` and `output/{packet.get('saved_brief', f'Hydrologist_Handoff_Brief_{w.id}.md')}`")
                st.json(packet["report"])
                st.caption(f"{packet['report']['scenarios_replayed']} revisions verified · daily_rainfall.csv / shortlist.csv / audit.json / input snapshot / checksums")

            st.markdown("#### Experiment Configuration")
            if not experiment_config.selected:
                st.info("No experiment has been configured in Review. Reports use BASIN's documented defaults, shown below. These are not a record of an earlier run.")
            else:
                st.caption("Selected in Review. Every simulated figure in the preview and the exported PDF uses exactly these settings.")
            st.dataframe(
                pd.DataFrame(experiment_config.describe_rows(), columns=["Setting", "Value"]),
                hide_index=True,
                width="stretch",
            )

        with col_export_view:
            st.markdown("#### 2. Deliverable Workspace & Documentation")
            accepted_preview = [s for s in chosen if s.status == "accepted" and s.approved_revision == s.revision]
            if not accepted_preview:
                st.session_state.pop("preview_pdf", None)

            tab_rep_prev, tab_shortlist, tab_evidence, tab_footprint = st.tabs([
                "📄 Executive Report Preview",
                "📊 Shortlist Details",
                "📁 Evidence & Provenance",
                "🌱 Environmental Footprint"
            ])

            with tab_rep_prev:
                if accepted_preview:
                    st.caption("Draft preview of currently accepted revisions. Building the packet still requires every shortlisted revision to be reviewed.")
                    brief_preview_text = generate_brief(w, accepted_preview)
                    col_prev_a, col_prev_b, col_prev_c = st.columns([1.5, 1, 1])
                    with col_prev_b:
                        preview_token = report_token(accepted_preview)
                        preview_state = st.session_state.get("preview_pdf")
                        if preview_state and preview_state.get("token") != preview_token:
                            st.session_state.pop("preview_pdf", None)
                            preview_state = None
                        if preview_state is None:
                            if st.button("📕 Prep PDF Preview", key=f"btn_prep_pdf_prev_{w.id}", width="stretch"):
                                st.session_state["preview_pdf"] = {
                                    "token": preview_token,
                                    "bytes": generate_pdf_report(w, accepted_preview, include_notes=share, config=experiment_config),
                                }
                                st.rerun()
                        else:
                            st.download_button(
                                "📕 Download PDF Preview",
                                preview_state["bytes"],
                                f"BASIN-Executive-Brief-Preview-{w.id}.pdf",
                                "application/pdf",
                                key=f"dl_pdf_preview_{w.id}",
                                width="stretch"
                            )
                    with col_prev_c:
                        st.download_button(
                            "📄 Download Brief (.md)",
                            brief_preview_text.encode("utf-8"),
                            f"Hydrologist_Handoff_Brief_{w.id}.md",
                            "text/markdown",
                            key=f"dl_brief_preview_{w.id}",
                            width="stretch",
                        )
                    with st.container(height=520):
                        st.markdown(brief_preview_text)
                else:
                    st.info("No accepted scenarios yet. In Review, inspect a scenario and choose Accept to see its report preview here.")
                    st.button("Go to Review", on_click=switch_page, args=("Review",))

            with tab_shortlist:
                st.markdown("**Shortlist Candidate Summary**")
                selected_table = table(w)
                selected_table = selected_table[selected_table["Selected for review"]].drop(columns="Selected for review")
                st.dataframe(selected_table, hide_index=True, width="stretch", height=450)

            with tab_evidence:
                st.markdown("**Evidence Included in Packet**")
                unresolved = [c for c in w.conflicts if c["status"] == "unresolved"]
                if unresolved:
                    st.warning(f"{len(unresolved)} unresolved evidence disagreement(s) will be included for the recipient.")
                    st.dataframe(pd.DataFrame(unresolved).drop(columns="private_note", errors="ignore"), hide_index=True)
                st.dataframe(pd.DataFrame(w.evidence).drop(columns="private_note", errors="ignore"), hide_index=True, width="stretch", height=400)

            with tab_footprint:
                fp = w.footprint
                st.markdown("**Local On-Device Resource Accounting**")
                c_fp1, c_fp2, c_fp3, c_fp4 = st.columns(4)
                c_fp1.metric("Pipeline Elapsed", f"{fp['wall_seconds']:.2f} s")
                c_fp2.metric("CPU Execution", f"{fp['cpu_seconds']:.2f} s")
                c_fp3.metric("Resident Memory", f"{fp['process_rss_mib_at_end']:.1f} MiB")
                er = fp.get("energy_wh_range", [0, 0])
                c_fp4.metric("Est. Pipeline Energy", f"{er[0]:.4f}–{er[1]:.4f} Wh")

                ai_sec = float(st.session_state.get("assistant_inference_seconds", 0.0))
                ai_wh_min = (ai_sec * 15.0) / 3600.0
                ai_wh_max = (ai_sec * 35.0) / 3600.0

                st.markdown("**AI & Assistant Subsystem Energy**")
                a_col1, a_col2, a_col3 = st.columns(3)
                a_col1.metric("Assistant Compute Time", f"{ai_sec:.2f} s")
                a_col2.metric("Active AI Power", "15–35 W" if ai_sec > 0 else "0 W (Direct Tools)")
                a_col3.metric("Est. AI Energy", f"{ai_wh_min:.4f}–{ai_wh_max:.4f} Wh" if ai_sec > 0 else "0.0000 Wh")

                st.caption(
                    "Runs 100% on-device with zero cloud inference calls and zero network transmission during analysis. "
                    "Pipeline energy is an illustrative laptop estimate (15–65 W × elapsed seconds); assistant energy accounts for active on-device CPU/GPU inference. "
                    "Full lifecycle water and embodied hardware carbon costs are unquantified."
                )
                st.json(w.footprint)

        st.divider()
        st.button("◀ Back to Step 3: Review Selections", key="btn_nav_back_to_review", on_click=switch_page, args=("Review",), width="stretch")

st.caption("Rainfall evidence workbench · 100% on-device execution (0 cloud calls, <200 MiB RAM) · Optional reservoir experiment is illustrative")

assistant_panel(w, source=source, names=names)
personal_notes_panel(w)
