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
from basin_ui import evidence_panel, comparison_panel, assistant_panel
from basin_theme import apply_design, appearance_picker, custom_appearance, accessible_chart, reveal_tour_target
from basin_core.data import CachedSource, ROOT
from basin_core.engine import ScenarioParams
from basin_core.exporter import export_bundle, verify_bundle, generate_brief
from basin_core.pdf_report import ExperimentConfig, generate_pdf_report, report_state_token
from basin_core.workspace import Workspace
from basin_core.uploads import TEMPLATE, preview_rainfall
from basin_core.rainfall_comparison import compare_rainfall
from basin_core.custom_data import active_ids, digest
from basin_core.visualizers import pareto_frontier_figure, stage_trigger_milestone_figure, drought_anomaly_matrix_figure

icon_file = ROOT / "assets/basin.ico"
st.set_page_config(page_title="BASIN", page_icon=str(icon_file) if icon_file.exists() else "◉", layout="wide", initial_sidebar_state="collapsed")
apply_design()
if st.session_state.get("assistant_open", False):
    st.html("""<style>
    .block-container, [data-testid="stMainBlockContainer"] {
        margin-right: 485px !important;
        max-width: calc(100% - 495px) !important;
        padding-right: 1.5rem !important;
        transition: margin-right 0.08s ease-out !important;
    }
    @media(max-width: 950px) {
        .block-container, [data-testid="stMainBlockContainer"] {
            margin-right: 0 !important;
            max-width: 100% !important;
        }
    }
    </style>""")


@st.cache_resource
def load_source():
    return CachedSource()



def local_rainfall_preview():
    with st.expander("Upload and observe your custom CSV."):
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
        try:
            preview = preview_rainfall(upload.getvalue(), station, location, unit)
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
        fig = go.Figure(go.Scatter(x=frame.date, y=frame.precip_mm, mode="lines+markers", connectgaps=False, name="Local observations"))
        fig.update_yaxes(title="Daily rainfall · mm")
        st.plotly_chart(accessible_chart(fig), width="stretch")
        st.dataframe(frame, hide_index=True, width="stretch")
        st.caption(f"Original file SHA-256: {preview.original_sha256}")
        st.info("Local station suitability and historical reference are not yet established. No percentile, forecast or scenario change is produced by this preview.")
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
    fig = go.Figure()
    for field, label in [("uploaded_mm", "Uploaded rainfall"), ("reference_mm", "NOAA reference")]:
        fig.add_trace(go.Scatter(x=frame.date, y=frame[field], name=label, connectgaps=False))
    fig.update_yaxes(title="Daily rainfall · mm")
    st.plotly_chart(accessible_chart(fig), width="stretch")
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
            provider = st.text_input("Source / provider")
            basis = st.text_input("Observation-day definition", help="Timezone and daily reporting window, or explicitly explain what is unknown.")
            rationale = st.text_area("Why this reference is appropriate, or what remains uncertain")
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
            st.plotly_chart(chart(fig), width="stretch")
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
    """Render station locations on an interactive high-resolution satellite map."""
    fig = go.Figure(go.Scattermap(
        lat=stations_df["latitude"],
        lon=stations_df["longitude"],
        mode="markers+text",
        text=stations_df["name"],
        textposition="top right",
        customdata=stations_df["station_id"],
        marker=dict(size=14, color="#00E5FF"),
        textfont=dict(size=11, color="#FFFFFF"),
        hovertemplate="<b>%{text}</b><br>Station: %{customdata}<br>Lat: %{lat:.4f}, Lon: %{lon:.4f}<extra></extra>"))
    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=35, b=10),
        title=dict(text="Station locations · High-resolution satellite view", font=dict(size=14)),
        map=dict(
            style="white-bg",
            layers=[{
                "below": "traces",
                "sourcetype": "raster",
                "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
            }],
            center=dict(lat=28.7, lon=-97.8),
            zoom=6.6,
        ),
        paper_bgcolor="rgba(0,0,0,0)")
    return fig


def reservoir_simulation_figure(sim_df: pd.DataFrame, pace_ms: int = 150):
    days = len(sim_df)
    step = max(1, days // 45)
    indices = list(range(0, days, step))
    if indices[-1] != days - 1:
        indices.append(days - 1)

    fig = make_subplots(
        rows=1, cols=2, column_widths=[0.36, 0.64],
        subplot_titles=["Active Storage (ac-ft)", "Combined Pool Trajectory (%)"],
        specs=[[{"type": "bar"}, {"type": "xy"}]]
    )

    init_row = sim_df.iloc[0]
    fig.add_trace(go.Bar(
        x=["Lake Corpus Christi<br>(Max 257k)", "Choke Canyon<br>(Max 662k)"],
        y=[init_row["lcc_acft"], init_row["ccr_acft"]],
        marker=dict(color=["#0d9488", "#087e8b"], line=dict(width=1.5, color="#123d38")),
        text=[f"{init_row['lcc_acft']:,.0f} ac-ft<br>({init_row['lcc_pct']}%)",
              f"{init_row['ccr_acft']:,.0f} ac-ft<br>({init_row['ccr_pct']}%)"],
        textposition="inside",
        name="Reservoir Storage",
        hovertemplate="<b>%{x}</b><br>Storage: %{y:,.0f} ac-ft<extra></extra>"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=[sim_df.iloc[0]["day"]],
        y=[sim_df.iloc[0]["combined_pct"]],
        mode="lines",
        line=dict(color="#087e8b", width=2.5),
        name="Combined %",
        hovertemplate="Day %{x}<br>Storage: %{y:.1f}%<extra></extra>"
    ), row=1, col=2)

    fig.add_hline(y=40, line_dash="dash", line_color="#d97706", annotation_text="Band 1 (40%)",
                  annotation_position="top right", row=1, col=2)
    fig.add_hline(y=30, line_dash="dash", line_color="#ea580c", annotation_text="Band 2 (30%)",
                  annotation_position="top right", row=1, col=2)
    fig.add_hline(y=20, line_dash="dash", line_color="#dc2626", annotation_text="Band 3 (20%)",
                  annotation_position="top right", row=1, col=2)

    frames = []
    for idx in indices:
        row = sim_df.iloc[idx]
        d = row["day"]
        sub_df = sim_df.iloc[:idx+1]
        frame = go.Frame(
            data=[
                go.Bar(
                    y=[row["lcc_acft"], row["ccr_acft"]],
                    text=[f"{row['lcc_acft']:,.0f} ac-ft<br>({row['lcc_pct']}%)",
                          f"{row['ccr_acft']:,.0f} ac-ft<br>({row['ccr_pct']}%)"]
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

    fig.update_yaxes(range=[0, 700000], title="ac-ft", row=1, col=1)
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
            direction="left",
            x=0.0, y=1.24,
            buttons=[
                dict(label="▶ Play Simulation", method="animate",
                     args=[None, {"frame": {"duration": pace_ms, "redraw": True}, "fromcurrent": True, "mode": "immediate"}]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}])
            ]
        )],
        sliders=[dict(
            active=0,
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
        1.0: {"name": "100% Historical Baseline", "color": "#0d9488", "width": 2.5, "dash": "solid"},
        0.8: {"name": "80% Moderate Stress (-20%)", "color": "#d97706", "width": 2.2, "dash": "solid"},
        0.6: {"name": "60% Severe Stress (-40%)", "color": "#ea580c", "width": 2.2, "dash": "solid"},
        0.4: {"name": "40% Catastrophic Stress (-60%)", "color": "#dc2626", "width": 2.2, "dash": "solid"},
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
    fig.add_hline(y=40, line_dash="dash", line_color="#d97706", annotation_text="Stage 1 (40%)",
                  annotation_position="top right")
    fig.add_hline(y=30, line_dash="dash", line_color="#ea580c", annotation_text="Stage 2 (30%)",
                  annotation_position="top right")
    fig.add_hline(y=20, line_dash="dash", line_color="#dc2626", annotation_text="Critical (20%)",
                  annotation_position="top right")
    fig.add_hline(y=15, line_dash="dot", line_color="#991b1b", annotation_text="Emergency (15%)",
                  annotation_position="top right")

    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
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
    "Review": "Does this scenario survive human challenge?",
    "Exports": "What evidence should the recipient receive?",
}


PAGE_ACTIONS = {
    "Data": "Check source identity, coverage, location and limitations before building scenarios.",
    "Workspace": "Configure settings, prioritize weights, and compare shortlisted candidates.",
    "Review": "Inspect the evidence, record a rationale, and accept, reject or revise the rainfall.",
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


def switch_page(name):
    st.session_state.page = name
    w = st.session_state.get("workspace")
    if name == "Review" and w and w.selected and not st.session_state.get("inspect_id"):
        st.session_state.inspect_id = w.selected[0]


def render_top_navigation(current_page, w):
    data_accepted = st.session_state.get("data_accepted", False) or (w is not None)
    scenarios_accepted = st.session_state.get("scenarios_accepted", False) or (w is not None and len(w.selected) > 0 and any(s.status != "unreviewed" for s in (w.get(i) for i in w.selected)))
    export_ready = w is not None and all(w.get(i).status in ("accepted", "rejected") for i in w.selected) and any(w.get(i).status == "accepted" for i in w.selected)

    stages = [
        ("Data", "Data Dashboard", True),
        ("Workspace", "Scenario Builder", data_accepted),
        ("Review", "Review Selections", scenarios_accepted or (w is not None)),
        ("Exports", "Export", export_ready),
    ]

    cols = st.columns(4)
    for col, (page_key, label, is_ready) in zip(cols, stages):
        is_active = current_page == page_key
        state_class = "basin-nav-active" if is_active else ("basin-nav-ready" if is_ready else "basin-nav-locked")
        with col:
            st.markdown(f'<div class="basin-header-text-btn {state_class}">', unsafe_allow_html=True)
            st.button(
                label,
                key=f"nav_tab_{page_key}",
                disabled=not is_ready,
                on_click=switch_page,
                args=(page_key,),
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
            tab_c1, tab_c2 = st.columns([5, 1])
            with tab_c1:
                st.markdown('<div class="basin-notes-tab-title">📝 Personal Notes</div>', unsafe_allow_html=True)
            with tab_c2:
                toggle_txt = "▼ Close" if is_open else "▲ Notes"
                if st.button(toggle_txt, key="btn_toggle_notes", help="Toggle Personal Notes panel"):
                    st.session_state.notes_open = not is_open
                    st.rerun()

            with st.container(key="notes_body_content"):
                st.caption("Saved locally with this analysis. Included in exports only if you opt in.")
                p_key = f"provider_{w.id}" if w else "provider_default"
                note = st.text_area("Provider notes", value=current_val, key=p_key, height=110)
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
        "directive": "Enter an audit rationale note and click 'Accept' to approve this scenario.",
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


def start_example(source, names):
    """Open a reproducible example without approving any scenario."""
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
            st.session_state.review_series_mode = TUTORIAL_STEPS[next_idx]["review_mode"]
    else:
        st.session_state.tutorial_active = False


def tutorial_prev():
    step_idx = st.session_state.get("tutorial_step", 0)
    prev_idx = max(0, step_idx - 1)
    st.session_state.tutorial_step = prev_idx
    st.session_state.page = TUTORIAL_STEPS[prev_idx]["page"]
    if TUTORIAL_STEPS[prev_idx].get("review_mode"):
        st.session_state.review_series_mode = TUTORIAL_STEPS[prev_idx]["review_mode"]


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
            st.session_state.review_series_mode = step["review_mode"]


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
    source = load_source()
except (OSError, ValueError, KeyError) as error:
    st.error(f"Snapshot unavailable: {error}")
    st.stop()
names = {s["id"]: s["name"].title().replace(" Intl Ap", "").replace(" Rgnl Ap", "") for s in source.manifest["stations"]}
w = st.session_state.get("workspace")
if w is not None and st.session_state.get("report_workspace_id") != w.id:
    for report_key in ("experiment_config", "preview_pdf", "packet",
                       "review_initial_storage", "review_conservation", "review_pipeline_active"):
        st.session_state.pop(report_key, None)
    st.session_state["report_workspace_id"] = w.id
curr_target = TUTORIAL_STEPS[st.session_state.get("tutorial_step", 0)]["target"] if st.session_state.get("tutorial_active") else ""

with st.sidebar:
    page = st.radio("View", ["Data", "Workspace", "Review", "Exports"], key="page",
                    index=0, format_func=PAGE_LABELS.get, label_visibility="collapsed")

# Centered Brand Header with Top-Right Utilities
top_l, top_c, top_r = st.columns([1, 2, 1])

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
            sessions = sorted((ROOT / "local").glob("session-*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if (ROOT / "local").exists() else []
            if sessions:
                previous = st.selectbox("Select saved run", sessions, format_func=lambda p: p.stem.replace("session-", ""), key="saved_run_select")
                if st.button("Open run", key="btn_open_saved_run", width="stretch", type="primary"):
                    try:
                        restored = Workspace.load(source, previous)
                        st.session_state.clear()
                        st.session_state.workspace = restored
                        st.session_state.data_accepted = True
                        st.session_state.scenarios_accepted = True
                        st.rerun()
                    except (ValueError, KeyError, OSError, TypeError) as error:
                        st.error(f"Cannot open run: {error}")
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

if w is None and page == "Data":
    with st.container(key="welcome"):
        st.markdown('<div class="basin-eyebrow">YOUR FIRST EXPLORATION</div><h2 class="welcome-title">Explore rainfall evidence<br>for your area.</h2><p class="welcome-copy">Compare observations, explore drier rainfall scenarios, and prepare a source-backed report.</p>', unsafe_allow_html=True)
        primary, secondary = st.columns(2)
        primary.button("Try an example", type="primary", on_click=start_example, args=(source, names), width="stretch")
        secondary.button("Proceed to Step 2: Scenario Builder ➔", on_click=switch_page, args=("Workspace",), width="stretch")
        st.caption("Generates 300 multi-duration candidates across the 1991–2025 NOAA record and shortlists 6 diverse drought profiles (Seed 22). It is not a forecast.")
        st.button("Take a tour", key="welcome_tour", on_click=start_tutorial, args=(source, names))
        st.markdown('<div class="welcome-steps"><span><b>01</b> Data Dashboard</span><span><b>02</b> Scenario Builder</span><span><b>03</b> Review Selections</span><span><b>04</b> Export</span></div>', unsafe_allow_html=True)

if page == "Data":
    saved_custom_panel(w)
    local_rainfall_preview()
    with tour_target("data_map"):
        metadata = pd.DataFrame(source.manifest["stations"]).rename(columns={"id": "station_id"})
        quality = pd.DataFrame(source.manifest["quality"])
        station_table = metadata.merge(quality, on="station_id")
        st.plotly_chart(accessible_chart(basin_map(station_table)), width="stretch")
        st.caption("Corpus Christi, Victoria and San Antonio airport observations are provisional regional proxies. These coordinates do not establish catchment coverage. Station suitability and spatial aggregation require practitioner review. The coordinate overview works offline.")
        with st.expander("Station details and completeness"):
            st.dataframe(station_table[["station_id", "name", "latitude", "longitude", "completeness_pct", "missing_or_excluded_days", "trace_days"]],
                         hide_index=True, width="stretch", column_config={"completeness_pct": st.column_config.NumberColumn("Complete %", format="%.3f")})
    tab_ts, tab_heatmap = st.tabs(["📈 Observed Time Series", "🗓️ 35-Year Drought Anomaly Matrix"])
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
            else:
                observed = observations
            fig = go.Figure()
            for station in observed:
                fig.add_trace(go.Scatter(x=observed.index, y=observed[station], name=names[station], mode="lines", connectgaps=False))
            fig.update_yaxes(title="Precipitation · mm")
            st.plotly_chart(chart(fig, 350), width="stretch")
            with st.expander("Observation table"):
                st.dataframe(observations, width="stretch")
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
        st.plotly_chart(accessible_chart(drought_anomaly_matrix_figure(hm_obs, title_prefix=hm_title)), width="stretch")
    with st.expander("Snapshot metadata & quality policy"):
        st.json(source.manifest)
    a, b = st.columns(2)
    a.download_button("Download station registry", metadata.to_csv(index=False), "stations.csv", "text/csv")
    b.download_button("Download methodology", (ROOT / "docs/methodology.md").read_bytes(), "BASIN-methodology.md", "text/markdown")
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(source.manifest["downloaded_at"])).days
    if age > 90:
        st.warning(f"Snapshot age: {age} days.")
    st.divider()
    with st.container():
        st.markdown('<div class="basin-gate-card">', unsafe_allow_html=True)
        st.markdown("**Step 1 Acceptance: Confirm Observation Baseline**")
        st.caption("Verify NOAA station proxies and data completeness before proceeding to scenario generation. Uploaded local rainfall CSVs (if any) are validated here.")
        def accept_data_baseline():
            st.session_state.data_accepted = True
            switch_page("Workspace")

        st.button(
            "✅ Accept Baseline & Proceed to Scenario Builder ➔",
            key="btn_accept_data_baseline",
            type="primary",
            on_click=accept_data_baseline,
            width="stretch"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    st.button("Proceed to Step 2: Scenario Builder ➔", key="btn_nav_to_workspace", on_click=switch_page, args=("Workspace",), width="stretch")

elif w is None and page in ("Review", "Exports"):
    st.warning("⚠️ This section is locked until scenarios are generated and reviewed. Start in Step 1 (Data Dashboard) or click 'Try an example' below.")
    st.button("Try an example", key=f"btn_try_example_{page}", type="primary", on_click=start_example, args=(source, names))
    st.button("◀ Return to Step 1: Data Dashboard", key=f"btn_return_data_{page}", on_click=switch_page, args=("Data",))

elif page == "Workspace":
    st.markdown("**Which rainfall scenarios deserve a closer look?**")
    st.caption("Configure generation settings, establish ranking priorities, and examine candidate shortlists.")

    # 1. Scenario Generation & Priority Weights Builder
    c_gen, c_weights = st.columns([1, 1])
    with c_gen:
        with tour_target("sidebar_generator"):
            with st.form("generate", border=True):
                st.markdown("##### 1. Resample Weather Windows")
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
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(str(error))

    with c_weights:
        with tour_target("sidebar_presets"):
            with st.container(border=True):
                st.markdown("##### 2. Ranking Priorities & Weights")
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
        left = st.container()
        right = st.expander("How ranking scores are calculated")
        with left:
            st.markdown("**Pareto Frontier of Hydrologic Extremes**")
            st.caption("Bubble size indicates multi-station concurrence %. The dashed amber curve connects the non-dominated Pareto frontier (worst-case historical rainfall shortfall envelope across duration tiers). Teal rings denote shortlisted candidates.")
            st.plotly_chart(accessible_chart(pareto_frontier_figure(view, w.selected)), width="stretch")
        with right:
            fig = go.Figure()
            for key in w.weights:
                fig.add_trace(go.Bar(name=key.title(), y=[s.id for s in selected], x=[s.components[key] for s in selected], orientation="h"))
            fig.update_layout(barmode="stack")
            fig.update_xaxes(range=[0,100], title="Contribution to ranking score")
            st.plotly_chart(chart(fig, 290), width="stretch")
        st.button("Review selected scenarios", key="btn_review_selected_scenarios", on_click=open_review, args=(w.selected[0],), type="primary")
        with st.expander("Scenario list and filters", expanded=curr_target == "workspace_table"):
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
        comparison_panel(w, save)
        with st.expander("Selection diagnostics"):
            st.dataframe(pd.DataFrame(comparison(w.scenarios, w.selected, w.params.seed)), hide_index=True, width="stretch")
            st.json({"clustering": w.clustering, "generation": w.generation, "selection_history": w.selection_history})
        
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
                "✅ Accept Shortlist & Proceed to Review Selections ➔",
                key="btn_accept_shortlist",
                type="primary",
                on_click=accept_shortlist,
                width="stretch"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        col_w_b1, col_w_b2 = st.columns([1, 2])
        col_w_b1.button("◀ Back to Step 1: Data Dashboard", key="btn_nav_back_to_data", on_click=switch_page, args=("Data",), width="stretch")
        col_w_b2.button("Proceed to Step 3: Review Selections ➔", key="btn_nav_to_review", type="primary", on_click=open_review, args=(w.selected[0],), width="stretch")
    else:
        st.info("💡 Configure settings above and click 'Create rainfall scenarios' (or 'Try an example') to generate candidates.")
        st.button("◀ Back to Step 1: Data Dashboard", key="btn_nav_back_to_data_empty", on_click=switch_page, args=("Data",), width="stretch")

elif page == "Review":
    candidates = w.selected + [s.id for s in w.scenarios if s.id not in w.selected]
    current = st.session_state.get("inspect_id", candidates[0])
    if current not in candidates:
        current = candidates[0]
    selected_id = st.selectbox("Scenario", candidates, index=candidates.index(current),
                               format_func=lambda i: f"{i} · {w.get(i).status} · r{w.get(i).revision}" + (" · shortlisted" if i in w.selected else ""))
    st.session_state.inspect_id = selected_id
    s = w.get(selected_id)
    f = s.features
    a, b = st.columns(2)
    a.metric("Rainfall shortfall · mm", f"{f['deficit_mm']:.1f}")
    b.metric("Duration · days", f["duration_days"])
    with st.expander("Reference and ranking details"):
        st.write(f"Rainfall shortfall: {f['deficit_mm']/25.4:.2f} inches")
        st.write(f"{'Station stress frequency' if len(s.series.columns) == 1 else 'Stations stressed together'}: {f['concurrence']:.1%}")
        st.write(f"How unusual vs history: {f['historical_percentile']:.0%}")
        st.write(f"Ranking score: {s.score:.2f} (priority, not probability)")
    left = st.container()
    right = st.container()
    with left:
        mode = st.radio("Series", ["Cumulative rainfall", "Daily rainfall", "30-day deficit", "Reservoir simulation"], horizontal=True, label_visibility="collapsed", key="review_series_mode")
        if mode == "Reservoir simulation":
            sim_subview = st.radio(
                "Simulation View",
                ["Single Scenario Drawdown", "Multi-Tier Stress Spectrum (100% · 80% · 60% · 40%)"],
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
            pace_choice = c_pace.selectbox("Playback pace", ["Presentation mode (2.5 min)", "Deliberate (45 sec)", "Rapid preview (10 sec)"], label_visibility="collapsed")
            pace_ms = 2500 if "2.5 min" in pace_choice else (800 if "45 sec" in pace_choice else 150)
            init_choice = c_init.selectbox("Initial storage", ["48% (illustrative)", "60% (illustrative)", "35% (illustrative)"], label_visibility="collapsed", key="review_initial_storage")
            init_pct = 0.48 if "48%" in init_choice else (0.60 if "60%" in init_choice else 0.35)
            conserve_choice = c_conserve.select_slider("Emergency Conservation", options=[0, 10, 20, 30], value=0, format_func=lambda v: f"Conservation: {v}%", label_visibility="collapsed", key="review_conservation")

            pipeline_active = st.checkbox("Assume pipeline supply available", value=True, key="review_pipeline_active")

            # The one configuration the report preview and both PDF paths render from.
            st.session_state["experiment_config"] = ExperimentConfig(
                initial_pct=init_pct,
                conservation_pct=conserve_choice / 100.0,
                pipeline_active=pipeline_active,
                scenario_id=s.id,
                scenario_revision=s.revision,
                selected=True,
            )
            st.info("Illustrative experiment: conditional storage under assumed inputs. Not calibrated, not a forecast, and excluded from saved evidence packets and their verification.")
            with st.expander("All experiment assumptions and accounting"):
                st.json(RESERVOIR_ASSUMPTIONS)

            if sim_subview == "Multi-Tier Stress Spectrum (100% · 80% · 60% · 40%)":
                spec = simulate_stress_spectrum(s.series, initial_pct=init_pct, conservation_pct=conserve_choice/100.0, pipeline_active=pipeline_active)
                st.plotly_chart(accessible_chart(stress_spectrum_figure(spec)), width="stretch")

                st.markdown("**Restriction Milestone Timeline (Gantt Analysis)**")
                st.caption("Horizontal timeline showing elapsed days until mandatory restriction triggers (Stage 1 @ 40%, Stage 2 @ 30%, Critical @ 20%, Emergency @ 15%) across each rainfall tier.")
                st.plotly_chart(accessible_chart(stage_trigger_milestone_figure(spec)), width="stretch")

                # Tipping point analysis
                passed = [r for r in spec["summary_table"] if r["survived_critical_20pct"]]
                failed = [r for r in spec["summary_table"] if not r["survived_critical_20pct"]]
                if passed and failed:
                    lowest_pass = min(passed, key=lambda x: x["retention_pct"])
                    highest_fail = max(failed, key=lambda x: x["retention_pct"])
                    st.warning(
                        f"⚡ **Critical Breaking Point Identified**: Infrastructure survives at **{lowest_pass['retention_pct']:.0f}% rainfall**, "
                        f"but breaches critical Stage 3 (20%) reserves under **{highest_fail['retention_pct']:.0f}% rainfall** on Day {highest_fail['day_stage3_20']}."
                    )
                elif not failed:
                    st.success("✅ **System Resilient Across All Tiers**: Storage remains above 20% critical reserve even under catastrophic 40% rainfall.")
                else:
                    st.error(f"⚠️ **System Vulnerable Across All Tiers**: Critical 20% threshold is breached even under baseline rainfall on Day {failed[0]['day_stage3_20']}.")

                countdown_df = pd.DataFrame([
                    {
                        "Rainfall Tier": r["tier_label"],
                        "Retention": f"{r['retention_pct']:.0f}%",
                        "Lowest Storage": f"{r['min_pct']:.1f}% ({r['min_acft']:,.0f} ac-ft)",
                        "Final Storage": f"{r['final_pct']:.1f}%",
                        "Stage 1 (40%)": f"Day {r['day_stage1_40']}" if r["day_stage1_40"] else "Not reached ✓",
                        "Stage 2 (30%)": f"Day {r['day_stage2_30']}" if r["day_stage2_30"] else "Not reached ✓",
                        "Critical (20%)": f"Day {r['day_stage3_20']}" if r["day_stage3_20"] else "Not reached ✓",
                        "Outcome": r["status"],
                    }
                    for r in spec["summary_table"]
                ])
                st.dataframe(countdown_df, hide_index=True, width="stretch")
                st.caption("Countdown days indicate elapsed duration from scenario onset until stage triggers occur under each rainfall tier. Simulates simultaneous vulnerability across historical and climate-stressed regimes.")
            else:
                sim_df = simulate_reservoir_drawdown(s.series, initial_pct=init_pct, conservation_pct=conserve_choice/100.0, pipeline_active=pipeline_active)

                with tour_target("review_simulation"):
                    st.plotly_chart(accessible_chart(reservoir_simulation_figure(sim_df, pace_ms=pace_ms)), width="stretch")
                    st.plotly_chart(accessible_chart(stage_trigger_milestone_figure({"tier_results": {1.0: {"df": sim_df}}})), width="stretch")

                s1 = next((r["day"] for _, r in sim_df.iterrows() if r["combined_pct"] < 40), None)
                s2 = next((r["day"] for _, r in sim_df.iterrows() if r["combined_pct"] < 30), None)
                term = sim_df.iloc[-1]
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Final Combined", f"{term['combined_pct']:.1f}%", f"{term['combined_acft']:,.0f} ac-ft")
                m2.metric("Illustrative band", term["stage"])
                m3.metric("Below 40% (conditional)", f"Day {s1}" if s1 else "Not breached")
                m4.metric("Below 30% (conditional)", f"Day {s2}" if s2 else "Not breached")
                st.caption("Capacity and operational parameters are illustrative assumptions. Threshold timing is conditional on these settings; it is not an official restriction date. Experiment settings reset independently of saved rainfall sessions.")
        else:
            expected = pd.DataFrame(w.reference.expected(s.series.index), index=s.series.index, columns=s.series.columns)
            fig = go.Figure()
            for station in s.series:
                values = s.series[station].cumsum() if mode == "Cumulative rainfall" else s.series[station] if mode == "Daily rainfall" else (expected[station] - s.series[station]).rolling(30).sum()
                fig.add_trace(go.Scatter(x=s.series.index, y=values, name=names[station], line=dict(width=1.7)))
            if mode == "Cumulative rainfall":
                fig.add_trace(go.Scatter(x=s.series.index, y=expected.mean(axis=1).cumsum(), name="Mean climatology", line=dict(color="#9ba8a0", dash="dot")))
            fig.update_yaxes(title="mm")
            st.plotly_chart(chart(fig, 320), width="stretch")
            st.caption(f"Matched rainfall reference: {f['benchmark_mm']:.1f} mm ({f['benchmark_mm']/25.4:.2f} in) · n={f['benchmark_n']} · {'exceeded' if f['beyond_rainfall_reference'] else 'not exceeded'} · 30-day windows: {f['eligible_concurrence_days']}")
    with right:
        with tour_target("review_decision"):
            st.markdown(f"**{s.id}** ({getattr(s, 'cluster_name', f'Group {s.cluster}')}) / revision {s.revision} / {s.status}")
            note = st.text_area("Review note", key=f"note_{s.id}_{w.id}", height=90)
            with st.container(key="review_accept_box"):
                if st.button("Accept", key=f"btn_accept_{s.id}_{s.revision}", type="primary", width="stretch"):
                    s.review(True, note)
                    save(w)
                    st.rerun()
            if st.button("Reject", key=f"btn_reject_{s.id}_{s.revision}", width="stretch"):
                try:
                    s.review(False, note)
                    save(w)
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
            with st.expander("Scale rainfall"):
                factor = st.number_input("Multiplier", 0.0, 2.0, 0.8, 0.05, key=f"edit_{s.id}_{w.id}")
                if st.button("Apply multiplier", key=f"btn_apply_multiplier_{s.id}_{s.revision}", width="stretch"):
                    try:
                        w.edit(s.id, note, factor=factor)
                        save(w)
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
        with st.expander("Replace from CSV"):
            st.download_button("CSV template", s.series.rename_axis("date").to_csv(), f"{s.id}-template.csv", "text/csv", key=f"dl_template_{s.id}_{s.revision}")
            upload = st.file_uploader("Daily rainfall · mm", type="csv", key=f"replacement_{w.id}_{s.id}")
            if st.button("Apply CSV", key=f"btn_apply_csv_{s.id}_{s.revision}", disabled=upload is None):
                try:
                    replacement = pd.read_csv(upload, index_col="date", parse_dates=["date"])
                    w.edit(s.id, note, replacement=replacement)
                    save(w)
                    st.rerun()
                except (ValueError, KeyError, TypeError) as error:
                    st.error(str(error))
        if s.id in w.selected:
            alternatives = [x.id for x in w.scenarios if x.id not in w.selected and x.status != "rejected"]
            with st.expander("Replace shortlist entry"):
                if alternatives:
                    other = st.selectbox("Candidate", alternatives, format_func=lambda i: f"{i} · {w.get(i).score:.1f}", key=f"sel_alt_{s.id}_{w.id}")
                    if st.button("Replace entry", key=f"btn_replace_entry_{s.id}_{w.id}"):
                        w.swap(s.id, other)
                        save(w)
                        st.session_state.inspect_id = other
                        st.rerun()
        else:
            old = st.selectbox("Replace shortlisted scenario", w.selected, key=f"sel_shortlist_target_{s.id}_{w.id}")
            if st.button("Use this candidate", key=f"btn_use_candidate_{s.id}_{w.id}", disabled=s.status == "rejected"):
                w.swap(old, s.id)
                save(w)
                st.rerun()
    data_tab, evidence_tab, history_tab = st.tabs(["Daily values", "Reference & provenance", "Revision history"])
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
        st.dataframe(pd.DataFrame({"Station": list(s.provenance["retention_by_station"]),
                                   "Scenario rainfall (fraction of observed)": list(s.provenance["retention_by_station"].values()),
                                   "Current deficit mm": [f["station_deficits_mm"][i] for i in s.provenance["retention_by_station"]]}),
                     hide_index=True, width="stretch")
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
    export_ready = all_reviewed and has_accepted

    with st.container():
        st.markdown('<div class="basin-gate-card">', unsafe_allow_html=True)
        g_r1, g_r2 = st.columns([3, 2])
        with g_r1:
            if export_ready:
                st.markdown(f"**Step 3 Acceptance: Review Decisions Complete ({sum(w.get(i).status == 'accepted' for i in w.selected)} Accepted)**")
                st.caption("All shortlisted scenarios have documented review decisions. Step 4 (Export) is unlocked.")
            else:
                unreviewed_count = sum(w.get(i).status == "unreviewed" for i in w.selected)
                st.markdown(f"**Step 3 Gating: {unreviewed_count} Candidate(s) Awaiting Review Decision**")
                st.caption("BASIN requires every shortlisted scenario to have a recorded Accept or Reject decision before export can be unlocked.")
        with g_r2:
            if not export_ready:
                if st.button("✅ Accept all shortlisted for export", key="btn_review_accept_all_shortlist", type="primary", width="stretch"):
                    for cand_id in w.selected:
                        cand = w.get(cand_id)
                        if cand.status == "unreviewed":
                            cand.review(True, "Batch accepted during review stage.")
                    save(w)
                    st.rerun()
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
    chosen = [w.get(i) for i in w.selected]
    st.markdown("**Review what your recipient will receive**")
    st.caption("A readable rainfall brief, daily values, source evidence and a replayable audit. Review decisions control what can be exported.")
    
    col_opt1, col_opt2 = st.columns([1, 1])
    share = col_opt1.checkbox("Include provider notes and free-text review notes", value=False, key=f"share_notes_{w.id}")
    share_custom = False
    if w.custom_uploads:
        col_opt2.warning("This analysis contains custom evidence. Replay requires all saved normalized upload versions, station/location/source metadata and suitability rationale.")
        share_custom = col_opt2.checkbox("Include custom numerical inputs and source metadata in this replayable export", key="custom_export_" + digest(w.custom_uploads))
    
    # The single experiment configuration every report on this page is generated from.
    experiment_config = st.session_state.get("experiment_config")
    if not isinstance(experiment_config, ExperimentConfig):
        experiment_config = ExperimentConfig()

    def report_token(accepted_scenarios):
        return report_state_token({"id": w.id, "content": digest(w.record(share, include_custom=True))}, accepted_scenarios, share, share_custom, experiment_config)

    with st.expander("Experiment configuration used for reports", expanded=False):
        if not experiment_config.selected:
            st.info("No experiment has been configured in Review. Reports use BASIN's documented defaults, shown below. These are not a record of an earlier run.")
        else:
            st.caption("Selected in Review. Every simulated figure in the preview and the exported PDF uses exactly these settings.")
        st.dataframe(
            pd.DataFrame(experiment_config.describe_rows(), columns=["Setting", "Value"]),
            hide_index=True,
            width="stretch",
        )

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
                st.session_state.packet = {
                    "data": payload,
                    "pdf_bytes": pdf_bytes,
                    "brief_text": brief_text,
                    "saved_pdf": str(pdf_path.name),
                    "saved_zip": str(zip_path.name),
                    "saved_brief": str(brief_path.name),
                    "fingerprint": json.dumps(w.record(share, include_custom=share_custom), sort_keys=True),
                    "share": share,
                    "custom": share_custom,
                    "config": experiment_config.fingerprint(),
                    "token": report_token(w.exportable()),
                    "report": report
                }
                st.success(f"✅ Verified ZIP and separate, unverified PDF generated and saved to disk: `output/{pdf_path.name}` and `output/{zip_path.name}`")
            except (ValueError, AssertionError, OSError) as error:
                st.error(f"Verification failed: {error}")

    # 2. GENERATED DELIVERABLES STAGE (MAIN PDF & ZIP DOWNLOAD CARDS)
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
        # Inputs, settings or consent moved on. Drop the generated bytes rather than leave
        # a download that no longer matches the workspace and settings it claims to report.
        st.session_state.pop("packet", None)
        packet = None
        st.info("Inputs, experiment settings or consent changed since the last export. Rebuild the verified export to download it again.")

    if packet_fresh:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 18px 22px; border-radius: 10px; border: 1px solid #334155; margin: 18px 0 12px 0; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.72rem; font-weight: 800; letter-spacing: 1px; color: #38bdf8; text-transform: uppercase;">⭐ MAIN STAGE DELIVERABLE · COUNCIL & ANALYSTS</span>
                <span style="font-size: 0.72rem; background: #087e8b; padding: 2px 8px; border-radius: 4px; font-weight: 700;">ZIP BUNDLE VERIFIED · PDF NOT COVERED</span>
            </div>
            <div style="font-size: 1.45rem; font-weight: 800; color: #ffffff; line-height: 1.2;">Executive Technical Brief (PDF)</div>
            <div style="font-size: 0.85rem; color: #cbd5e1; margin: 6px 0 14px 0; line-height: 1.45;">
                Professionally structured for City Council members, regional water boards, and technical analysts.
                Includes plain-language bottom-line takeaways, the experiment configuration used, illustrative storage bands and the stress spectrum matrix.
                SHA-256 verification covers the companion replay ZIP; this PDF is generated separately and is outside that contract.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        pdf_data = packet.get("pdf_bytes")
        if pdf_data:
            st.download_button(
                "📕 Download Executive Brief (PDF)",
                pdf_data,
                f"BASIN-Executive-Brief-{w.id}.pdf",
                "application/pdf",
                key=f"dl_pdf_main_{w.id}",
                type="primary",
                width="stretch"
            )

        st.markdown("**Companion Deliverables & Replay Package:**")
        col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 1])
        with col_dl1:
            st.download_button("📦 Download Replay ZIP", packet["data"], f"BASIN-{w.id}.zip", "application/zip", key=f"dl_zip_{w.id}", width="stretch")
        with col_dl2:
            brief_bytes = packet.get("brief_text", "").encode("utf-8") if packet.get("brief_text") else b""
            st.download_button("📄 Download Brief (.md)", brief_bytes, f"Hydrologist_Handoff_Brief_{w.id}.md", "text/markdown", key=f"dl_brief_export_{w.id}", width="stretch")
        with col_dl3:
            if st.button("📂 Open Output Folder", key=f"btn_open_out_folder_{w.id}", width="stretch"):
                import subprocess, sys
                out_folder = ROOT / "output"
                if sys.platform == "win32":
                    subprocess.Popen(["explorer", str(out_folder.resolve())])
        st.caption(f"📁 Local copies on disk: `output/{packet.get('saved_pdf', f'BASIN-Executive-Brief-{w.id}.pdf')}`, `output/{packet.get('saved_zip', f'BASIN-{w.id}.zip')}` and `output/{packet.get('saved_brief', f'Hydrologist_Handoff_Brief_{w.id}.md')}`")
        st.json(packet["report"])
        st.caption(f"{packet['report']['scenarios_replayed']} revisions verified · daily_rainfall.csv / shortlist.csv / audit.json / input snapshot / checksums")

    # 3. TECHNICAL VERIFICATION ACCORDIONS (AUDIT TRAIL & METHODOLOGY)
    accepted_preview = [s for s in chosen if s.status == "accepted" and s.approved_revision == s.revision]
    if not accepted_preview:
        st.session_state.pop("preview_pdf", None)
    with st.expander("Read the report preview", expanded=False):
        if accepted_preview:
            st.caption("Draft preview of currently accepted revisions. Building the packet still requires every shortlisted revision to be reviewed.")
            st.caption(
                "Experiment configuration: "
                + " · ".join(f"{label} — {value}" for label, value in experiment_config.describe_rows())
            )
            brief_preview_text = generate_brief(w, accepted_preview)
            col_prev_a, col_prev_b, col_prev_c = st.columns([2, 1, 1])
            with col_prev_b:
                preview_token = report_token(accepted_preview)
                preview_state = st.session_state.get("preview_pdf")
                if preview_state and preview_state.get("token") != preview_token:
                    # Scenario selection, consent or experiment settings changed: discard the
                    # prepared bytes so a stale preview can never be downloaded.
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
            st.markdown(brief_preview_text)
        else:
            st.info("No accepted scenarios yet. In Review, inspect a scenario and choose Accept to see its report here.")
            st.button("Go to Review", on_click=switch_page, args=("Review",))

    with st.expander("Shortlist details"):
        selected_table = table(w)
        selected_table = selected_table[selected_table["Selected for review"]].drop(columns="Selected for review")
        st.dataframe(selected_table, hide_index=True, width="stretch")

    unresolved = [c for c in w.conflicts if c["status"] == "unresolved"]
    if unresolved:
        st.warning(f"{len(unresolved)} unresolved evidence disagreement(s) will be included for the recipient.")
        st.dataframe(pd.DataFrame(unresolved).drop(columns="private_note", errors="ignore"), hide_index=True)

    with st.expander("Evidence included in packet"):
        st.dataframe(pd.DataFrame(w.evidence).drop(columns="private_note", errors="ignore"), hide_index=True)

    with st.expander("Run resource usage"):
        st.json(w.footprint)

    st.divider()
    st.button("◀ Back to Step 3: Review Selections", key="btn_nav_back_to_review", on_click=switch_page, args=("Review",), width="stretch")

st.caption("Rainfall evidence workbench · Regional station proxies unvalidated · Optional reservoir experiment is illustrative")

assistant_panel(w, source=source, names=names)
personal_notes_panel(w)
