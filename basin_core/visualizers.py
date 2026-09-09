"""Interactive hydrologic visualizers for BASIN.

Provides:
- rainfall_shortfall_figure: Shared-scale duration panels with separated scenario dots.
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
from plotly.subplots import make_subplots


def rainfall_shortfall_figure(
    view: pd.DataFrame, shortlist_ids: list[str] | None = None,
    focused_id: str | None = None, *, colorblind: bool = False,
) -> go.Figure:
    """Compare total deficits on a shared scale; horizontal offsets only separate dots.

    Packing is deterministic and changes neither duration nor deficit. Each duration
    has its own maximum, including ties; there is no implied interpolation between
    durations or claim of multi-objective optimality.
    """
    if view.empty:
        fig = go.Figure()
        fig.add_annotation(text="No scenarios to compare", showarrow=False)
        return fig

    data = view.copy()
    durations = sorted(data["Days"].unique())
    cols = min(3, len(durations))
    rows = (len(durations) + cols - 1) // cols
    fig = make_subplots(
        rows=rows, cols=cols, shared_yaxes="all",
        specs=[[{} if r * cols + c < len(durations) else None for c in range(cols)] for r in range(rows)],
        subplot_titles=[f"{d:g} days" for d in durations],
        horizontal_spacing=0.07, vertical_spacing=0.15 if rows > 1 else 0,
    )
    low, high = min(0.0, data["Deficit mm"].min()), max(0.0, data["Deficit mm"].max())
    span = max(high - low, 1.0)
    y_range = [low - span * 0.04, high + span * 0.13]
    # Approximate a 12px separation in each 300px-high plotting panel.
    separation = (y_range[1] - y_range[0]) / 25
    offsets = {}
    for _, panel in data.groupby("Days"):
        placed = []
        for _, point in panel.sort_values(["Deficit mm", "ID"]).iterrows():
            nearby = [(lane, y) for lane, y in placed if point["Deficit mm"] - y < separation]
            lane = 0
            for candidate in [0] + [v for n in range(1, len(nearby) + 2) for v in (n, -n)]:
                if all((candidate - x) ** 2 + ((point["Deficit mm"] - y) / separation) ** 2 >= 1
                       for x, y in nearby):
                    lane = candidate
                    break
            offsets[point["ID"]] = lane
            placed.append((lane, point["Deficit mm"]))
    data["_offset"] = data["ID"].map(offsets)
    extent = max(8, max(abs(v) for v in offsets.values()) + 2)
    palette = (["#0072B2", "#E69F00", "#56B4E9", "#CC79A7", "#D55E00", "#009E73"]
               if colorblind else
               ["#087e8b", "#cc9145", "#638c72", "#826f9e", "#ac675d", "#4c6c94", "#858844", "#a25789"])
    groups = sorted(data["Group"].unique())
    symbols = ["circle", "square", "diamond", "cross", "triangle-up", "x"]
    shown = set()
    custom_columns = ["ID", "Profile", "Deficit in", "Stations stressed together %", "Score", "Onset", "Days"]
    hover = (
        "<b>Scenario %{customdata[0]}</b> · %{customdata[1]}<br>"
        "Duration: %{customdata[6]} days · Onset: %{customdata[5]}<br>"
        "Total deficit: %{y:.1f} mm (%{customdata[2]:.2f} in)<br>"
        "30-day windows with all selected stations stressed: %{customdata[3]:.1f}%<br>"
        "Ranking score: %{customdata[4]:.2f}<extra></extra>"
    )
    for index, duration in enumerate(durations):
        row, col = index // cols + 1, index % cols + 1
        panel = data[data["Days"] == duration]

        def add_points(points, name, group, marker, *, focus=False, rank=100):
            if points.empty:
                return
            fig.add_trace(go.Scatter(
                x=points["_offset"], y=points["Deficit mm"],
                mode="markers+text" if focus else "markers",
                text=points["ID"] if focus else None, textposition="top center",
                name=name, legendgroup=group, legendrank=rank, showlegend=group not in shown and not focus,
                marker=marker, customdata=points[custom_columns].values,
                hovertemplate=hover, cliponaxis=False,
            ), row=row, col=col)
            shown.add(group)

        for group, points in panel.groupby("Group"):
            color_index = int(group)
            add_points(points, points["Profile"].iloc[0], f"profile-{group}", dict(
                size=8, opacity=0.8, color=palette[color_index % len(palette)],
                symbol=symbols[color_index % len(symbols)] if colorblind else "circle",
            ), rank=groups.index(group))
        add_points(panel[panel["Deficit mm"] == panel["Deficit mm"].max()],
                   "Highest deficit in each duration", "maximum",
                   dict(size=12, symbol="diamond-open", color="#E69F00", line=dict(width=2)))
        add_points(panel[panel["ID"].isin(shortlist_ids or [])], "Selected for review", "shortlist",
                   dict(size=14, symbol="circle-open", color="#E69F00", line=dict(width=2)), rank=101)
        add_points(panel[panel["ID"] == focused_id], "Scenario details", "focus",
                   dict(size=18, symbol="square-open", color="#E69F00", line=dict(width=2)), focus=True)
        fig.update_xaxes(range=[-extent, extent], visible=False, fixedrange=True, row=row, col=col)
        fig.update_yaxes(range=y_range, showgrid=True, zeroline=False,
                         title_text="Total rainfall deficit (mm)" if col == 1 else None,
                         showticklabels=col == 1, row=row, col=col)

    fig.update_layout(
        height=370 * rows + 110, margin=dict(l=55, r=20, t=45, b=100),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12), hovermode="closest",
        legend=dict(orientation="h", yanchor="top", y=-0.06, xanchor="left", x=0,
                    itemclick=False, itemdoubleclick=False),
    )
    return fig


def pareto_frontier_figure(view: pd.DataFrame, shortlist_ids: list[str] | None = None) -> go.Figure:
    """Compatibility entry point for callers of the former frontier chart."""
    return rainfall_shortfall_figure(view, shortlist_ids)


def rainfall_reference_figure(series: pd.Series, reference: pd.Series, mode: str = "Cumulative rainfall") -> go.Figure:
    """Compare one station with its own climatology on the same scenario days."""
    days = list(range(1, len(series) + 1))
    fig = go.Figure()
    if mode == "30-day deficit":
        values = (reference - series).rolling(30, min_periods=30).sum()
        fig.add_trace(go.Scatter(x=days, y=values, name="30-day reference minus scenario",
                                line=dict(color="#2878A0", width=2)))
        fig.add_hline(y=0, line_dash="dot")
        title = "Rolling 30-day rainfall difference (mm)"
    else:
        cumulative = mode == "Cumulative rainfall"
        for values, name, dash, color in (
            (reference, "Historical monthly reference", "dash", "#888888"),
            (series, "Selected scenario", "solid", "#2878A0"),
        ):
            fig.add_trace(go.Scatter(x=days, y=values.cumsum() if cumulative else values,
                                    name=name, line=dict(color=color, width=2.2, dash=dash)))
        title = "Accumulated rainfall (mm)" if cumulative else "Daily rainfall (mm)"
    fig.update_traces(hovertemplate="Day %{x}<br>%{y:.1f} mm<extra>%{fullData.name}</extra>")
    fig.update_layout(height=340, margin=dict(l=15, r=15, t=15, b=15), hovermode="x unified",
                      legend=dict(orientation="h", y=1.15),
                      xaxis=dict(title="Days since scenario start"), yaxis=dict(title=title))
    return fig


def stage_trigger_milestone_figure(spec: dict) -> go.Figure:
    """Render a horizontal milestone timeline across stress tiers or single scenario drawdown."""
    fig = go.Figure()

    stages_meta = [
        {"name": "At least 40%", "color": "#059669"},
        {"name": "30% to below 40%", "color": "#d97706"},
        {"name": "20% to below 30%", "color": "#ea580c"},
        {"name": "15% to below 20%", "color": "#dc2626"},
        {"name": "Below 15%", "color": "#7f1d1d"},
    ]

    added_to_legend = set()
    tier_keys = sorted(list(spec["tier_results"].keys()))

    tier_display_names = {
        1.0: "Selected scenario",
        0.8: "20% further reduction",
        0.6: "40% further reduction",
        0.4: "60% further reduction",
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
