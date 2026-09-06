from __future__ import annotations

import calendar
from datetime import datetime, timezone
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from basin_core.analysis import comparison, COMMUNITY_PRESETS, simulate_reservoir_drawdown
from basin_core.data import CachedSource, ROOT
from basin_core.engine import ScenarioParams
from basin_core.exporter import export_bundle, verify_bundle
from basin_core.workspace import Workspace

icon_file = ROOT / "assets/basin.ico"
st.set_page_config(page_title="BASIN", page_icon=str(icon_file) if icon_file.exists() else "◉", layout="wide")
st.markdown('''<style>
.block-container{padding-top:3.2rem;padding-bottom:1.5rem;max-width:1800px}
[data-testid="stAppDeployButton"]{display:none}
[data-testid="stSidebar"]{border-right:1px solid #d4dedd}
[data-testid="stSidebar"] .block-container{padding-top:1.2rem}
h1{font-size:1.5rem!important;letter-spacing:.06em;font-weight:700!important}
h2{font-size:1.15rem!important}h3{font-size:1rem!important}
[data-testid="stMetricValue"]{font-size:1.45rem;font-variant-numeric:tabular-nums}
[data-testid="stMetricLabel"]{font-size:.75rem;color:#61706d}
[data-testid="stMetric"]{border-bottom:1px solid #d9e2df;padding:4px 0 10px}
[data-testid="stCaptionContainer"]{font-size:.75rem}
[data-testid="stVerticalBlock"]{gap:.7rem}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.45rem}
button{border-radius:4px!important}
@media(max-width:700px){.block-container{padding-top:3rem}h1{font-size:1.25rem!important}}
</style>''', unsafe_allow_html=True)


@st.cache_resource
def load_source():
    return CachedSource()


def save(w):
    try:
        w.save()
    except OSError as error:
        st.error(f"Save failed: {error}")


def chart(fig, height=300):
    fig.update_layout(height=height, margin=dict(l=5, r=8, t=10, b=5),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial", size=11, color="#42605a"),
                      legend=dict(orientation="h", y=-.22),
                      colorway=["#087e8b", "#cc9145", "#638c72", "#826f9e", "#ac675d", "#4c6c94", "#858844", "#a25789"])
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#e0e7e4", zeroline=False)
    return fig


def basin_map(stations_df):
    fig = go.Figure()
    reservoirs = pd.DataFrame([
        {"name": "Choke Canyon Reservoir", "latitude": 28.48, "longitude": -98.27, "desc": "Frio River · 662k ac-ft storage"},
        {"name": "Lake Corpus Christi", "latitude": 28.05, "longitude": -97.87, "desc": "Nueces River · 257k ac-ft terminal pool"},
        {"name": "Lake Texana", "latitude": 28.83, "longitude": -96.53, "desc": "Navidad River · Mary Rhodes Pipeline"},
    ])
    fig.add_trace(go.Scattergeo(
        lat=reservoirs["latitude"],
        lon=reservoirs["longitude"],
        mode="markers+text",
        text=reservoirs["name"],
        textposition=["bottom center", "top right", "top right"],
        customdata=reservoirs["desc"],
        hovertemplate="<b>%{text}</b><br>%{customdata}<extra>Reservoir</extra>",
        marker=dict(size=11, color="#087e8b", symbol="diamond", line=dict(width=1.5, color="#103632")),
        name="Drinking Reservoirs"
    ))
    fig.add_trace(go.Scattergeo(
        lat=stations_df["latitude"],
        lon=stations_df["longitude"],
        mode="markers+text",
        text=stations_df["name"].str.replace(" Intl Ap", "").str.replace(" Rgnl Ap", "").str.replace(" Airport", ""),
        textposition=["top center", "bottom right", "top left"],
        customdata=stations_df["station_id"],
        hovertemplate="<b>%{text}</b> (%{customdata})<br>Lat: %{lat:.2f}, Lon: %{lon:.2f}<extra>NOAA Proxy Station</extra>",
        marker=dict(size=10, color="#cc9145", symbol="circle", line=dict(width=1.5, color="#503513")),
        name="NOAA GHCN-Daily Stations"
    ))
    fig.update_geos(
        fitbounds="locations",
        visible=True,
        resolution=50,
        showcountries=True,
        countrycolor="#c8d6d3",
        showsubunits=True,
        subunitcolor="#c8d6d3",
        showcoastlines=True,
        coastlinecolor="#8fa8a2",
        showland=True,
        landcolor="#f4f7f6",
        showlakes=True,
        lakecolor="#d6e8e6",
        showrivers=True,
        rivercolor="#c2dedb",
        projection_type="albers usa"
    )
    fig.update_layout(
        height=320,
        margin=dict(l=5, r=8, t=10, b=5),
        legend=dict(orientation="h", y=-0.15, x=0.0),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=11, color="#42605a")
    )
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

    fig.add_hline(y=40, line_dash="dash", line_color="#d97706", annotation_text="Stage 1 (40%)",
                  annotation_position="top right", row=1, col=2)
    fig.add_hline(y=30, line_dash="dash", line_color="#ea580c", annotation_text="Stage 2 (30%)",
                  annotation_position="top right", row=1, col=2)
    fig.add_hline(y=20, line_dash="dash", line_color="#dc2626", annotation_text="Stage 3 (20%)",
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
    fig.update_yaxes(range=[0, 65], title="Combined %", row=1, col=2)
    fig.update_xaxes(range=[0, days + 2], title="Scenario Day", row=1, col=2)

    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=11, color="#42605a"),
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
    fig.update_yaxes(gridcolor="#e0e7e4", zeroline=False)
    return fig


def table(w):
    return pd.DataFrame([{"ID": s.id, "Group": s.cluster, "Profile": getattr(s, "cluster_name", f"Group {s.cluster}"),
                          "Score": round(s.score, 2),
                          "Days": s.features["duration_days"], "Onset": calendar.month_abbr[s.features["onset_month"]],
                          "Deficit mm": round(s.features["deficit_mm"], 2),
                          "Deficit in": round(s.features["deficit_mm"] / 25.4, 2),
                          "Concurrence %": round(s.features["concurrence"] * 100, 1),
                          "Reference percentile": round(s.features["historical_percentile"] * 100, 1),
                          "Dry spell days": s.features["max_dry_days"],
                          "Revision": s.revision, "Status": s.status, "Shortlist": s.id in w.selected} for s in w.scenarios])


def open_review(identifier):
    st.session_state.inspect_id = identifier
    st.session_state.page = "Review"


def switch_page(name):
    st.session_state.page = name


try:
    source = load_source()
except (OSError, ValueError, KeyError) as error:
    st.error(f"Snapshot unavailable: {error}")
    st.stop()
names = {s["id"]: s["name"].title().replace(" Intl Ap", "").replace(" Rgnl Ap", "") for s in source.manifest["stations"]}
w = st.session_state.get("workspace")

with st.sidebar:
    st.title("BASIN")
    page = st.radio("View", ["Workspace", "Review", "Exports", "Data"], key="page", label_visibility="collapsed")
    st.divider()
    with st.expander("New run", expanded=w is None):
        with st.form("generate"):
            stations = st.multiselect("Stations", list(names), default=list(w.params.stations) if w else list(names), format_func=names.get)
            durations = st.multiselect("Durations · days", [30, 60, 90, 180, 270, 365], default=list(w.params.durations) if w else [90, 180, 270])
            months = st.multiselect("Onset months", list(range(1, 13)), default=list(w.params.months) if w else [1, 4, 7, 10], format_func=lambda m: calendar.month_abbr[m])
            retention = st.slider("Rainfall retained · %", 0, 100, (35, 85), 5,
                                  help="Multiply observed daily rainfall by this fraction at the affected stations.")
            extent = st.selectbox("Reduction extent", ["All stations", "One station", "Mixed"])
            a, b = st.columns(2)
            count = a.selectbox("Candidates", [100, 300, 500, 1000], index=1)
            size = b.selectbox("Shortlist", [3, 4, 6, 8], index=2)
            seed = st.number_input("Seed", 0, 4294967295, w.params.seed if w else 22)
            generate = st.form_submit_button("Generate", type="primary", width="stretch")
        if generate:
            try:
                with st.spinner("Computing…"):
                    params = ScenarioParams(tuple(stations), tuple(durations), tuple(months), retention[0]/100, retention[1]/100, extent, count, int(seed))
                    new = Workspace(source, params, size)
                    if w:
                        new.notes = w.notes
                    st.session_state.workspace = new
                    for key in list(st.session_state):
                        if key.startswith(("weight_", "review_", "note_", "edit_", "swap_", "provider_")):
                            del st.session_state[key]
                    st.session_state.pop("inspect_id", None)
                    st.session_state.pop("packet", None)
                    save(new)
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(str(error))
    if w:
        with st.expander("Ranking weights", expanded=page == "Workspace"):
            preset_options = ["Custom weights"] + list(COMMUNITY_PRESETS.keys())
            matched = "Custom weights"
            for p_name, p_vals in COMMUNITY_PRESETS.items():
                if w.weights == p_vals:
                    matched = p_name
                    break
            chosen_preset = st.selectbox("Community priority preset", preset_options,
                                         index=preset_options.index(matched),
                                         key=f"preset_select_{w.id}")
            if chosen_preset != "Custom weights" and chosen_preset != matched:
                new_w = dict(COMMUNITY_PRESETS[chosen_preset])
                for k, v in new_w.items():
                    st.session_state[f"weight_{k}"] = v
                w.rerank(new_w)
                save(w)
                st.rerun()

            labels = {"severity": "Severity", "duration": "Duration", "concurrence": "Concurrence", "season": "Jun–Sep timing"}
            weights = {k: st.slider(label, 0, 100, int(w.weights[k]), key=f"weight_{k}") for k, label in labels.items()}
            if sum(weights.values()) == 0:
                st.error("At least one weight must be positive.")
            elif weights != w.weights:
                w.rerank(weights)
                save(w)
            if st.button("Rebuild shortlist", disabled=sum(weights.values()) == 0, width="stretch"):
                try:
                    w.rebuild_shortlist()
                    save(w)
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
        with st.expander("Private notes"):
            note = st.text_area("Provider notes", value=w.notes, key=f"provider_{w.id}", label_visibility="collapsed")
            if st.button("Save notes", width="stretch"):
                w.notes = note
                save(w)
                st.toast("Saved locally")
    with st.expander("Saved runs"):
        sessions = sorted((ROOT / "local").glob("session-*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if (ROOT / "local").exists() else []
        if sessions:
            previous = st.selectbox("Run", sessions, format_func=lambda p: p.stem.replace("session-", ""))
            if st.button("Open run", width="stretch"):
                try:
                    restored = Workspace.load(source, previous)
                    st.session_state.clear()
                    st.session_state.workspace = restored
                    st.rerun()
                except (ValueError, KeyError, OSError, TypeError) as error:
                    st.error(f"Cannot open run: {error}")
        else:
            st.caption("No saved runs")
    st.divider()
    st.caption(f"Local · NOAA snapshot {source.manifest['downloaded_at'][:10]}")

header, status = st.columns([3, 2])
header.subheader(page if page != "Workspace" else "Scenario workspace")
status.caption(f"{w.id}  /  {len(w.scenarios)} candidates  /  seed {w.params.seed}" if w else "NOAA GHCN-Daily  /  1991–2025")

if page == "Data" or (page == "Workspace" and w is None):
    metadata = pd.DataFrame(source.manifest["stations"]).rename(columns={"id": "station_id"})
    quality = pd.DataFrame(source.manifest["quality"])
    station_table = metadata.merge(quality, on="station_id")
    st.plotly_chart(basin_map(station_table), width="stretch")
    st.caption("Provisional Regional Proxies: Corpus Christi (USW00012924), Victoria (USW00012912), and San Antonio (USW00012921) represent downstream and adjacent First-Order NOAA stations used for methodology demonstration. Full operational deployment requires upstream COOP/mesonet gauge calibration across the Nueces and Frio headwaters.")
    st.dataframe(station_table[["station_id", "name", "latitude", "longitude", "completeness_pct", "missing_or_excluded_days", "trace_days"]],
                 hide_index=True, width="stretch", column_config={"completeness_pct": st.column_config.NumberColumn("Complete %", format="%.3f")})
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
    with st.expander("Snapshot metadata & quality policy"):
        st.json(source.manifest)
    a, b = st.columns(2)
    a.download_button("Download station registry", metadata.to_csv(index=False), "stations.csv", "text/csv")
    b.download_button("Download methodology", (ROOT / "docs/methodology.md").read_bytes(), "BASIN-methodology.md", "text/markdown")
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(source.manifest["downloaded_at"])).days
    if age > 90:
        st.warning(f"Snapshot age: {age} days.")

elif w is None:
    st.info("No active run.")

elif page == "Workspace":
    selected = [w.get(i) for i in w.selected]
    a, b, c, d = st.columns(4)
    a.metric("Candidates", len(w.scenarios))
    b.metric("Groups", w.clustering["groups"])
    c.metric("Shortlisted", len(selected))
    d.metric("Approved", sum(s.status == "accepted" and s.approved_revision == s.revision for s in selected))
    view = table(w)
    left, right = st.columns([1.6, 1])
    with left:
        fig = px.scatter(view, x="Days", y="Deficit mm", color="Group", hover_name="ID",
                         hover_data=["Score", "Onset", "Concurrence %"], color_continuous_scale="Teal")
        shortlist_rows = view[view.Shortlist]
        fig.add_trace(go.Scatter(x=shortlist_rows["Days"], y=shortlist_rows["Deficit mm"], mode="markers",
                                marker=dict(size=14, symbol="circle-open", line=dict(width=2), color="#233f3b"),
                                text=shortlist_rows.ID, name="Shortlist", hovertemplate="%{text}<extra>Shortlist</extra>"))
        fig.update_layout(coloraxis_colorbar=dict(title="Group", thickness=8))
        st.plotly_chart(chart(fig, 290), width="stretch")
    with right:
        fig = go.Figure()
        for key in w.weights:
            fig.add_trace(go.Bar(name=key.title(), y=[s.id for s in selected], x=[s.components[key] for s in selected], orientation="h"))
        fig.update_layout(barmode="stack")
        fig.update_xaxes(range=[0,100], title="Score contributions")
        st.plotly_chart(chart(fig, 290), width="stretch")
    a, b, c, d = st.columns([2, 1, 1, 1])
    query = a.text_input("Find scenario", placeholder="Scenario ID")
    group_filter = b.selectbox("Group", ["All"] + sorted(view.Group.unique().tolist()))
    review_filter = c.selectbox("Status", ["All", "unreviewed", "accepted", "rejected"])
    only_selected = d.checkbox("Shortlist only", value=True)
    filtered = view[view.ID.str.contains(query, case=False, regex=False)].copy()
    if group_filter != "All":
        filtered = filtered[filtered.Group.eq(group_filter)]
    if review_filter != "All":
        filtered = filtered[filtered.Status.eq(review_filter)]
    if only_selected:
        filtered = filtered[filtered.Shortlist]
    filtered = filtered.sort_values(["Score", "ID"], ascending=[False, True]).reset_index(drop=True)
    selection = st.dataframe(filtered, hide_index=True, width="stretch", height=min(430, 40+len(filtered)*35),
                             on_select="rerun", selection_mode="single-row", key=f"candidates_{w.id}")
    rows = selection.selection.rows
    if rows and rows[0] < len(filtered):
        selected_id = filtered.iloc[rows[0]].ID
        st.button(f"Inspect {selected_id}", on_click=open_review, args=(selected_id,), type="primary")
    elif len(filtered):
        st.button("Review shortlist", on_click=open_review, args=(w.selected[0],))
    with st.expander("Selection diagnostics"):
        st.dataframe(pd.DataFrame(comparison(w.scenarios, w.selected, w.params.seed)), hide_index=True, width="stretch")
        st.json({"clustering": w.clustering, "generation": w.generation, "selection_history": w.selection_history})

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
    a, b, c, d, e = st.columns(5)
    a.metric("Deficit", f"{f['deficit_mm']:.1f} mm", f"{f['deficit_mm']/25.4:.2f} in")
    b.metric("Duration · days", f["duration_days"])
    c.metric("Concurrence", f"{f['concurrence']:.1%}")
    d.metric("Reference percentile", f"{f['historical_percentile']:.0%}")
    e.metric("Score", f"{s.score:.2f}")
    left, right = st.columns([2.2, 1])
    with left:
        mode = st.radio("Series", ["Cumulative rainfall", "Daily rainfall", "30-day deficit", "Reservoir simulation"], horizontal=True, label_visibility="collapsed")
        if mode == "Reservoir simulation":
            c_pace, c_init = st.columns([1, 1])
            pace_choice = c_pace.selectbox("Playback pace", ["Presentation mode (2.5 min)", "Deliberate (45 sec)", "Rapid preview (10 sec)"], label_visibility="collapsed")
            pace_ms = 2500 if "2.5 min" in pace_choice else (800 if "45 sec" in pace_choice else 150)
            init_choice = c_init.selectbox("Initial storage", ["48% (2024 Drought Entry)", "60% (Historical Baseline)", "35% (Pre-Stressed Pool)"], label_visibility="collapsed")
            init_pct = 0.48 if "48%" in init_choice else (0.60 if "60%" in init_choice else 0.35)

            sim_df = simulate_reservoir_drawdown(s.series, initial_pct=init_pct)
            st.plotly_chart(reservoir_simulation_figure(sim_df, pace_ms=pace_ms), width="stretch")

            s1 = next((r["day"] for _, r in sim_df.iterrows() if r["combined_pct"] < 40), None)
            s2 = next((r["day"] for _, r in sim_df.iterrows() if r["combined_pct"] < 30), None)
            term = sim_df.iloc[-1]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Final Combined", f"{term['combined_pct']:.1f}%", f"{term['combined_acft']:,.0f} ac-ft")
            m2.metric("Terminal Status", term["stage"])
            m3.metric("Stage 1 Breach (<40%)", f"Day {s1}" if s1 else "Not breached")
            m4.metric("Stage 2 Breach (<30%)", f"Day {s2}" if s2 else "Not breached")
            st.caption("Physical Reservoir Stress Model: Choke Canyon (662k ac-ft) and Lake Corpus Christi (257k ac-ft) mass-balance under ~180 MGD regional draw and seasonal evaporation. Pre-engineering scoping tool; official firm yield modeling requires Texas WAM Run 3 by a licensed P.E.")
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
        st.markdown(f"**{s.id}** ({getattr(s, 'cluster_name', f'Group {s.cluster}')}) / revision {s.revision} / {s.status}")
        note = st.text_area("Review note", key=f"note_{s.id}_{w.id}", height=90)
        a, b = st.columns(2)
        if a.button("Accept", type="primary", width="stretch"):
            s.review(True, note)
            save(w)
            st.rerun()
        if b.button("Reject", width="stretch"):
            try:
                s.review(False, note)
                save(w)
                st.rerun()
            except ValueError as error:
                st.error(str(error))
        with st.expander("Scale rainfall"):
            factor = st.number_input("Multiplier", 0.0, 2.0, 0.8, 0.05, key=f"edit_{s.id}_{w.id}")
            if st.button("Apply multiplier", width="stretch"):
                try:
                    w.edit(s.id, note, factor=factor)
                    save(w)
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
        with st.expander("Replace from CSV"):
            st.download_button("CSV template", s.series.rename_axis("date").to_csv(), f"{s.id}-template.csv", "text/csv")
            upload = st.file_uploader("Daily rainfall · mm", type="csv", key=f"replacement_{w.id}_{s.id}")
            if st.button("Apply CSV", disabled=upload is None):
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
                    other = st.selectbox("Candidate", alternatives, format_func=lambda i: f"{i} · {w.get(i).score:.1f}")
                    if st.button("Replace entry"):
                        w.swap(s.id, other)
                        save(w)
                        st.session_state.inspect_id = other
                        st.rerun()
        else:
            old = st.selectbox("Replace shortlisted scenario", w.selected)
            if st.button("Use this candidate", disabled=s.status == "rejected"):
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
        if c_save.button("Save daily edits", width="stretch"):
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
                                   "Initial rainfall retained": list(s.provenance["retention_by_station"].values()),
                                   "Current deficit mm": [f["station_deficits_mm"][i] for i in s.provenance["retention_by_station"]]}),
                     hide_index=True, width="stretch")
        st.json({"source": s.provenance, "features": f, "score_contributions": s.components, "snapshot_sha256": source.manifest["sha256"]})
    with history_tab:
        if s.history:
            st.dataframe(pd.DataFrame([{k:v for k,v in event.items() if k != "replacement_values"} for event in s.history]), hide_index=True, width="stretch")
        else:
            st.caption("No revisions or review decisions")

elif page == "Exports":
    chosen = [w.get(i) for i in w.selected]
    st.dataframe(table(w).query("Shortlist").drop(columns="Shortlist"), hide_index=True, width="stretch")
    share = st.checkbox("Include provider notes and free-text review notes", value=False)
    try:
        w.exportable()
        ready = True
    except ValueError as error:
        ready = False
        st.warning(str(error))
    if st.button("Build verified export", type="primary", disabled=not ready):
        try:
            payload = export_bundle(w, share)
            report = verify_bundle(payload)
            st.session_state.packet = {"data": payload, "fingerprint": json.dumps(w.record(share), sort_keys=True), "share": share, "report": report}
        except (ValueError, AssertionError, OSError) as error:
            st.error(f"Verification failed: {error}")
    packet = st.session_state.get("packet")
    if packet and packet["share"] == share and packet["fingerprint"] == json.dumps(w.record(share), sort_keys=True):
        st.download_button("Download ZIP", packet["data"], f"BASIN-{w.id}.zip", "application/zip", type="primary")
        st.caption(f"{packet['report']['scenarios_replayed']} revisions verified · rainfall.csv / shortlist.csv / audit.json / input snapshot / checksums")
    with st.expander("Run resource usage"):
        st.json(w.footprint)

st.caption("Rainfall analysis only · Regional station proxies unvalidated")
