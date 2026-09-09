"""Interactive hydrologic visualizers for BASIN.

Provides:
- pareto_frontier_figure: Multi-objective Pareto frontier of duration vs. rainfall deficit
  with bubble sizing for multi-station concurrence and shortlist annotations.
- stage_trigger_milestone_figure: Horizontal milestone timeline (Gantt analysis)
  tracking storage progression through restriction stages (Normal, Stage 1, Stage 2,
  Critical Reserve, Emergency).
- drought_anomaly_matrix_figure: 35-year (1991–2025) x 12-month climatological
  monthly anomaly matrix relative to the 35-year norm.
"""

from __future__ import annotations

import calendar
import pandas as pd
import plotly.graph_objects as go


def pareto_frontier_figure(view: pd.DataFrame, shortlist_ids: list[str] = None) -> go.Figure:
    """Render a Pareto Frontier Bubble Plot comparing scenario duration vs. rainfall deficit.

    Bubble sizes represent multi-station concurrence %, colors represent drought profile groups,
    and the dashed amber line connects the non-dominated maximum-deficit Pareto envelope.
    """
    fig = go.Figure()
    if shortlist_ids is None:
        shortlist_ids = []

    cluster_colors = ["#087e8b", "#cc9145", "#638c72", "#826f9e", "#ac675d", "#4c6c94", "#858844", "#a25789"]

    # 1. Bubble scatter trace: All candidates categorized by drought group
    for g in sorted(view["Group"].unique()):
        sub = view[view["Group"] == g]
        c = cluster_colors[g % len(cluster_colors)]
        profile_name = sub["Profile"].iloc[0] if "Profile" in sub else f"Group {g}"
        sizes = 8 + (sub["Stations stressed together %"] / 100.0) * 16

        fig.add_trace(go.Scatter(
            x=sub["Days"],
            y=sub["Deficit mm"],
            mode="markers",
            name=profile_name,
            marker=dict(
                size=sizes,
                color=c,
                opacity=0.65,
                line=dict(width=1, color="rgba(255,255,255,0.4)")
            ),
            customdata=sub[["ID", "Profile", "Deficit in", "Stations stressed together %", "Score", "Onset"]].values,
            hovertemplate=(
                "<b>Scenario %{customdata[0]}</b> (%{customdata[1]})<br>"
                "Duration: %{x} days · Onset: %{customdata[5]}<br>"
                "Rainfall Deficit: %{y:.1f} mm (%{customdata[2]:.2f} in)<br>"
                "Station Concurrence: %{customdata[3]:.1f}%<br>"
                "Score: %{customdata[4]:.2f}<extra></extra>"
            )
        ))

    # 2. Pareto Optimal Frontier (Upper Deficit Envelope across durations)
    sorted_v = view.sort_values(by=["Days", "Deficit mm"], ascending=[True, False])
    pareto_pts = []
    curr_max = -1.0
    for _, row in sorted_v.iterrows():
        if row["Deficit mm"] > curr_max:
            pareto_pts.append(row)
            curr_max = row["Deficit mm"]

    if pareto_pts:
        pareto_df = pd.DataFrame(pareto_pts)
        fig.add_trace(go.Scatter(
            x=pareto_df["Days"],
            y=pareto_df["Deficit mm"],
            mode="lines+markers",
            name="Pareto Optimal Frontier (Worst-Case)",
            line=dict(color="#f59e0b", width=2.5, dash="dash"),
            marker=dict(size=9, symbol="diamond", color="#f59e0b", line=dict(width=1.5, color="#ffffff")),
            customdata=pareto_df[["ID", "Profile", "Deficit in", "Stations stressed together %"]].values,
            hovertemplate=(
                "<b>⚡ Pareto Boundary: %{customdata[0]}</b><br>"
                "Duration: %{x} days<br>"
                "Peak Deficit: %{y:.1f} mm (%{customdata[2]:.2f} in)<br>"
                "Concurrence: %{customdata[3]:.1f}%<extra>Pareto Envelope</extra>"
            )
        ))

    # 3. Shortlist Candidates Overlay with direct text labels
    shortlist_rows = view[view["ID"].isin(shortlist_ids)]
    if not shortlist_rows.empty:
        fig.add_trace(go.Scatter(
            x=shortlist_rows["Days"],
            y=shortlist_rows["Deficit mm"],
            mode="markers+text",
            text=shortlist_rows["ID"],
            textposition="top center",
            textfont=dict(size=11, color="#00E5FF", family="Arial Black, Arial"),
            marker=dict(
                size=18,
                symbol="circle-open",
                line=dict(width=2.5, color="#00E5FF")
            ),
            name="Selected for review",
            customdata=shortlist_rows[["ID", "Profile", "Deficit in", "Stations stressed together %", "Score"]].values,
            hovertemplate=(
                "<b>★ Shortlisted: %{customdata[0]}</b><br>"
                "Duration: %{x} days<br>"
                "Deficit: %{y:.1f} mm (%{customdata[2]:.2f} in)<br>"
                "Concurrence: %{customdata[3]:.1f}%<br>"
                "Score: %{customdata[4]:.2f}<extra>Shortlist Selection</extra>"
            )
        ))

    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=25, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
        xaxis=dict(title="Scenario Duration (Days)", showgrid=False, zeroline=False),
        yaxis=dict(title="Rainfall Deficit from Reference (mm)", showgrid=True, zeroline=False),
    )
    return fig


def stage_trigger_milestone_figure(spec: dict) -> go.Figure:
    """Render a horizontal milestone timeline across stress tiers or single scenario drawdown."""
    fig = go.Figure()

    stages_meta = [
        {"name": "Normal (≥40%)", "color": "#059669"},
        {"name": "Stage 1 Watch (30–40%)", "color": "#d97706"},
        {"name": "Stage 2 Warning (20–30%)", "color": "#ea580c"},
        {"name": "Stage 3 Critical (15–20%)", "color": "#dc2626"},
        {"name": "Emergency (<15%)", "color": "#7f1d1d"},
    ]

    added_to_legend = set()
    tier_keys = sorted(list(spec["tier_results"].keys()))

    tier_display_names = {
        1.0: "100% Baseline",
        0.8: "80% Moderate",
        0.6: "60% Severe",
        0.4: "40% Catastrophic",
    }

    def get_stage_idx(pct):
        if pct >= 40.0:
            return 0
        elif pct >= 30.0:
            return 1
        elif pct >= 20.0:
            return 2
        elif pct >= 15.0:
            return 3
        else:
            return 4

    for m in tier_keys:
        res = spec["tier_results"][m]
        sim_df = res["df"]
        tier_label = "Scenario Timeline" if len(tier_keys) == 1 else tier_display_names.get(m, f"{int(m*100)}% Rain")
        total_days = int(sim_df["day"].max())

        segments = []
        curr_idx = get_stage_idx(sim_df.iloc[0]["combined_pct"])
        seg_start = int(sim_df.iloc[0]["day"])

        for _, row in sim_df.iterrows():
            d = int(row["day"])
            idx = get_stage_idx(row["combined_pct"])
            if idx != curr_idx:
                segments.append((seg_start, d, curr_idx))
                seg_start = d
                curr_idx = idx
        segments.append((seg_start, total_days, curr_idx))

        for start, end, s_idx in segments:
            duration = max(1, end - start)
            meta = stages_meta[s_idx]
            show_leg = meta["name"] not in added_to_legend
            added_to_legend.add(meta["name"])

            text = f"D{start}" if duration >= 18 and start > 0 else ""

            fig.add_trace(go.Bar(
                y=[tier_label],
                x=[duration],
                base=[start],
                orientation="h",
                name=meta["name"],
                legendgroup=meta["name"],
                showlegend=show_leg,
                marker=dict(color=meta["color"], line=dict(width=1, color="rgba(0,0,0,0.2)")),
                text=text,
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="#ffffff", size=11, family="Arial Black, Arial"),
                customdata=[[tier_label, meta["name"], start, end, duration]],
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Regime: %{customdata[1]}<br>"
                    "Days: Day %{customdata[2]} to Day %{customdata[3]} (%{customdata[4]} days)<extra></extra>"
                )
            ))

    fig.update_layout(
        barmode="overlay",
        height=130 if len(tier_keys) == 1 else 230,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1.0),
        xaxis=dict(title="Scenario Timeline (Elapsed Days)", showgrid=True, zeroline=False),
        yaxis=dict(title="", showgrid=False, zeroline=False),
    )
    return fig


def drought_anomaly_matrix_figure(observations: pd.DataFrame, title_prefix: str = "Catchment Average") -> go.Figure:
    """Render a 35-year (1991–2025) x 12-month precipitation anomaly heatmap matrix."""
    if isinstance(observations, pd.DataFrame):
        daily_series = observations.mean(axis=1)
    else:
        daily_series = observations

    monthly_precip = daily_series.resample("MS").sum()
    df = pd.DataFrame({"precip": monthly_precip, "year": monthly_precip.index.year, "month": monthly_precip.index.month})

    baseline = df.groupby("month")["precip"].mean()
    df["baseline"] = df["month"].map(baseline)
    df["anomaly_pct"] = ((df["precip"] - df["baseline"]) / df["baseline"].replace(0, 1e-6)) * 100
    df["anomaly_mm"] = df["precip"] - df["baseline"]
    df["precip_in"] = df["precip"] / 25.4

    matrix_z = df.pivot(index="year", columns="month", values="anomaly_pct")
    matrix_precip = df.pivot(index="year", columns="month", values="precip")
    matrix_in = df.pivot(index="year", columns="month", values="precip_in")
    matrix_baseline = df.pivot(index="year", columns="month", values="baseline")
    matrix_diff_mm = df.pivot(index="year", columns="month", values="anomaly_mm")

    month_names = [calendar.month_abbr[m] for m in range(1, 13)]
    years = sorted(matrix_z.index.tolist(), reverse=True)

    z_vals = matrix_z.reindex(years).values
    precip_vals = matrix_precip.reindex(years).values
    in_vals = matrix_in.reindex(years).values
    base_vals = matrix_baseline.reindex(years).values
    diff_vals = matrix_diff_mm.reindex(years).values

    custom_data = []
    for y_idx, yr in enumerate(years):
        row_data = []
        for m_idx, m_name in enumerate(month_names):
            p = precip_vals[y_idx, m_idx] if y_idx < len(precip_vals) and m_idx < len(precip_vals[y_idx]) else 0.0
            pi = in_vals[y_idx, m_idx] if y_idx < len(in_vals) and m_idx < len(in_vals[y_idx]) else 0.0
            b = base_vals[y_idx, m_idx] if y_idx < len(base_vals) and m_idx < len(base_vals[y_idx]) else 0.0
            d = diff_vals[y_idx, m_idx] if y_idx < len(diff_vals) and m_idx < len(diff_vals[y_idx]) else 0.0
            row_data.append([yr, m_name, p, pi, b, d])
        custom_data.append(row_data)

    colorscale = [
        [0.0, "#7f1d1d"],
        [0.2, "#dc2626"],
        [0.35, "#f97316"],
        [0.5, "#1e293b"],
        [0.65, "#0284c7"],
        [0.8, "#0d9488"],
        [1.0, "#059669"],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=month_names,
        y=[str(y) for y in years],
        colorscale=colorscale,
        zmin=-100,
        zmax=150,
        colorbar=dict(
            title="Anomaly %",
            ticksuffix="%",
            len=0.9,
            thickness=14,
            outlinewidth=0,
        ),
        customdata=custom_data,
        hovertemplate=(
            "<b>%{customdata[0]} %{customdata[1]}</b><br>"
            "Precipitation: %{customdata[2]:.1f} mm (%{customdata[3]:.2f} in)<br>"
            "35-Yr Norm: %{customdata[4]:.1f} mm<br>"
            "Anomaly: %{z:+.1f}% (%{customdata[5]:+.1f} mm)<extra></extra>"
        )
    ))

    fig.update_layout(
        height=580,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        xaxis=dict(title="Month", side="top"),
        yaxis=dict(title="Year", dtick=1, showgrid=False),
    )
    return fig
