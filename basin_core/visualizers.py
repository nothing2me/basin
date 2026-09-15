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
from typing import Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def rainfall_shortfall_figure(
    view: pd.DataFrame, shortlist_ids: list[str] | None = None,
    focused_id: str | None = None, *, colorblind: bool = False,
    unit: str = "mm",
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
    val_col = "Deficit in" if unit == "in" and "Deficit in" in data.columns else "Deficit mm"
    if "Group" not in data.columns:
        data["Group"] = 0
    if "Profile" not in data.columns:
        data["Profile"] = data["Group"].astype(str)
    if "Deficit in" not in data.columns:
        data["Deficit in"] = (data["Deficit mm"] / 25.4) if "Deficit mm" in data.columns else 0.0
    if "Deficit mm" not in data.columns:
        data["Deficit mm"] = (data["Deficit in"] * 25.4) if "Deficit in" in data.columns else 0.0
    if "Stations stressed together %" not in data.columns:
        data["Stations stressed together %"] = 0.0
    if "Score" not in data.columns:
        data["Score"] = 0.0
    if "Onset" not in data.columns:
        data["Onset"] = "Drought Period"
    if "Days" not in data.columns:
        data["Days"] = 30

    unit_label = "in" if val_col == "Deficit in" else "mm"
    durations = sorted(data["Days"].unique())
    cols = min(3, len(durations))
    rows = (len(durations) + cols - 1) // cols
    fig = make_subplots(
        rows=rows, cols=cols, shared_yaxes="all",
        specs=[[{} if r * cols + c < len(durations) else None for c in range(cols)] for r in range(rows)],
        subplot_titles=[f"{d:g} days" for d in durations],
        horizontal_spacing=0.07, vertical_spacing=0.15 if rows > 1 else 0,
    )
    low, high = min(0.0, data[val_col].min()), max(0.0, data[val_col].max())
    span = max(high - low, 0.1 if unit_label == "in" else 1.0)
    y_range = [low - span * 0.04, high + span * 0.13]
    # Approximate a 12px separation in each 300px-high plotting panel.
    separation = (y_range[1] - y_range[0]) / 25
    offsets = {}
    for _, panel in data.groupby("Days"):
        placed = []
        for _, point in panel.sort_values([val_col, "ID"]).iterrows():
            nearby = [(lane, y) for lane, y in placed if point[val_col] - y < separation]
            lane = 0
            for candidate in [0] + [v for n in range(1, len(nearby) + 2) for v in (n, -n)]:
                if all((candidate - x) ** 2 + ((point[val_col] - y) / separation) ** 2 >= 1
                       for x, y in nearby):
                    lane = candidate
                    break
            offsets[point["ID"]] = lane
            placed.append((lane, point[val_col]))
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
                x=points["_offset"], y=points[val_col],
                mode="markers+text" if focus else "markers",
                text=points["ID"] if focus else None, textposition="top center",
                name=name, legendgroup=group, legendrank=rank, showlegend=group not in shown and not focus,
                marker=marker, customdata=points[custom_columns].values,
                hovertemplate=hover, cliponaxis=False,
            ), row=row, col=col)
            shown.add(group)

        for group, points in panel.groupby("Group"):
            color_index = groups.index(group)
            add_points(points, points["Profile"].iloc[0], f"profile-{group}", dict(
                size=8, opacity=0.8, color=palette[color_index % len(palette)],
                symbol=symbols[color_index % len(symbols)] if colorblind else "circle",
            ), rank=groups.index(group))
        add_points(panel[panel[val_col] == panel[val_col].max()],
                   "Highest deficit in each duration", "maximum",
                   dict(size=12, symbol="diamond-open", color="#E69F00", line=dict(width=2)))
        add_points(panel[panel["ID"].isin(shortlist_ids or [])], "Selected for review", "shortlist",
                   dict(size=14, symbol="circle-open", color="#E69F00", line=dict(width=2)), rank=101)
        add_points(panel[panel["ID"] == focused_id], "Scenario details", "focus",
                   dict(size=18, symbol="square-open", color="#E69F00", line=dict(width=2)), focus=True)
        fig.update_xaxes(range=[-extent, extent], visible=False, fixedrange=True, showgrid=False, zeroline=False, showticklabels=False, ticks="", row=row, col=col)
        fig.update_yaxes(range=y_range, showgrid=True, zeroline=False,
                         title_text=f"Total rainfall deficit ({unit_label})" if col == 1 else None,
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


def rainfall_reference_figure(
    series: pd.Series, reference: pd.Series, mode: str = "Cumulative rainfall",
    unit: str = "mm"
) -> go.Figure:
    """Compare one station with its own climatology on the same scenario days."""
    scale = 1.0 / 25.4 if unit == "in" else 1.0
    u_str = "in" if unit == "in" else "mm"
    s_vals = series * scale
    r_vals = reference * scale
    days = list(range(1, len(series) + 1))
    fig = go.Figure()
    if mode == "30-day deficit":
        values = (r_vals - s_vals).rolling(30, min_periods=30).sum()
        fig.add_trace(go.Scatter(x=days, y=values, name="30-day reference minus scenario",
                                line=dict(color="#2878A0", width=2)))
        fig.add_hline(y=0, line_dash="dot")
        title = f"Rolling 30-day rainfall difference ({u_str})"
    else:
        cumulative = mode == "Cumulative rainfall"
        for values, name, dash, color in (
            (r_vals, "Historical monthly reference", "dash", "#888888"),
            (s_vals, "Selected scenario", "solid", "#2878A0"),
        ):
            fig.add_trace(go.Scatter(x=days, y=values.cumsum() if cumulative else values,
                                    name=name, line=dict(color=color, width=2.2, dash=dash)))
        title = f"Accumulated rainfall ({u_str})" if cumulative else f"Daily rainfall ({u_str})"
    fmt = ".2f" if unit == "in" else ".1f"
    fig.update_traces(hovertemplate=f"Day %{{x}}<br>%{{y:{fmt}}} {u_str}<extra>%{{fullData.name}}</extra>")
    fig.update_layout(height=340, margin=dict(l=15, r=15, t=15, b=15), hovermode="x unified",
                      legend=dict(orientation="h", y=1.15),
                      xaxis=dict(title="Days since scenario start"), yaxis=dict(title=title))
    return fig


def stage_trigger_milestone_figure(
    spec: dict,
    stage_bands_pct: tuple[float, float, float, float] = (40.0, 30.0, 20.0, 15.0)
) -> go.Figure:
    """Render a horizontal milestone timeline across stress tiers or single scenario drawdown."""
    fig = go.Figure()

    from basin_core.analysis import rainfall_tier_label

    bands = [b * 100.0 if b <= 1.0 else b for b in stage_bands_pct]
    b1, b2, b3, b4 = bands[0], bands[1], bands[2], bands[3]
    # Inclusive like the crossing days: storage exactly at 40% is already in the 40% band.
    stages_meta = [
        {"name": f"Above {b1:g}%", "color": "#059669"},
        {"name": f"Above {b2:g}% to {b1:g}%", "color": "#d97706"},
        {"name": f"Above {b3:g}% to {b2:g}%", "color": "#ea580c"},
        {"name": f"Above {b4:g}% to {b3:g}%", "color": "#dc2626"},
        {"name": f"At or below {b4:g}%", "color": "#7f1d1d"},
    ]

    added_to_legend = set()
    tier_keys = sorted(list(spec["tier_results"].keys()))

    def get_stage_idx(pct):
        if pct > b1:
            return 0
        elif pct > b2:
            return 1
        elif pct > b3:
            return 2
        elif pct > b4:
            return 3
        else:
            return 4

    for m in tier_keys:
        res = spec["tier_results"][m]
        sim_df = res["df"]
        tier_label = ("Scenario Timeline" if len(tier_keys) == 1
                      else (res.get("metrics") or {}).get("tier_label") or rainfall_tier_label(m))
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
        height=220 if len(tier_keys) == 1 else 280,
        margin=dict(l=45 if len(tier_keys) == 1 else 145, r=24, t=78, b=62),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.16,
            xanchor="left",
            x=0.0,
            font=dict(size=10),
            traceorder="normal",
        ),
        xaxis=dict(title=dict(text="Scenario day", standoff=14), showgrid=True, zeroline=False),
        yaxis=dict(
            title="",
            showgrid=False,
            zeroline=False,
            automargin=True,
            showticklabels=len(tier_keys) > 1,
        ),
    )
    return fig


def storage_trajectory_figure(
    sim_df: pd.DataFrame,
    stage_bands_pct: tuple[float, ...] = (0.40, 0.30, 0.20, 0.15),
) -> go.Figure:
    """Show the combined-storage result without detailed playback controls."""
    fig = go.Figure()
    bands = [float(value * 100 if value <= 1 else value) for value in stage_bands_pct]
    colors = ["#059669", "#d97706", "#ea580c", "#dc2626", "#7f1d1d"]
    bounds = [100.0, *bands, 0.0]
    for index, (upper, lower) in enumerate(zip(bounds, bounds[1:])):
        fig.add_hrect(y0=lower, y1=upper, fillcolor=colors[index], opacity=0.07,
                      line_width=0, layer="below")
    for level in bands:
        fig.add_hline(y=level, line_dash="dot", line_color="#8b949e", line_width=1)
    fig.add_trace(go.Scatter(
        x=sim_df["day"], y=sim_df["combined_pct"], mode="lines",
        line=dict(color="#087e8b", width=3), fill="tozeroy",
        fillcolor="rgba(8,126,139,0.08)", name="Combined storage",
        hovertemplate="Day %{x}<br>Combined storage: %{y:.1f}%<extra></extra>",
    ))
    end = sim_df.iloc[-1]
    fig.add_trace(go.Scatter(
        x=[end["day"]], y=[end["combined_pct"]], mode="markers+text",
        text=[f"End {end['combined_pct']:.1f}%"], textposition="top left",
        marker=dict(size=10, color="#087e8b", line=dict(width=2, color="#ffffff")),
        showlegend=False, cliponaxis=False,
        hovertemplate="Day %{x}<br>Combined storage: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        height=390, margin=dict(l=58, r=24, t=24, b=54), showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12), hovermode="x unified",
        xaxis=dict(title="Scenario day", showgrid=False, zeroline=False),
        yaxis=dict(title="Combined storage", range=[0, 103], ticksuffix="%",
                   tickvals=sorted(set([0.0, 100.0, *bands])),
                   gridcolor="rgba(128,128,128,0.15)", zeroline=False),
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


def shortlist_cumulative_deficit_figure(
    workspace: Any,
    unit: str = "in",
    highlight_id: str | None = None,
    show_envelope: bool = True,
) -> go.Figure:
    """Compare cumulative rainfall deficits across all shortlisted scenarios on a single timeline.

    Plots the accumulation trajectory of meteorological drought stress (inches or mm)
    from Day 1 to the end of each scenario, with an envelope showing the shortlist range
    and mean trajectory.
    """
    fig = go.Figure()
    if not workspace or not getattr(workspace, "selected", None):
        fig.add_annotation(text="No shortlisted scenarios to compare", showarrow=False)
        return fig

    is_us = unit.lower() in ("in", "us", "ac-ft")
    scale = 1.0 / 25.4 if is_us else 1.0
    u_label = "in" if is_us else "mm"

    palette = [
        "#0ea5e9", "#f59e0b", "#10b981", "#8b5cf6",
        "#ec4899", "#06b6d4", "#f97316", "#6366f1",
    ]

    all_series_days: dict[str, tuple[list[int], list[float]]] = {}
    max_day = 0

    for idx, s_id in enumerate(workspace.selected):
        s = workspace.get(s_id)
        if s is None:
            continue
        expected = workspace.reference.expected(s.series.index)
        scenario_vals = s.series.to_numpy()
        daily_deficit = np.maximum(expected - scenario_vals, 0.0).mean(axis=1) * scale
        cum_deficit = np.cumsum(daily_deficit).tolist()
        days = list(range(1, len(cum_deficit) + 1))
        all_series_days[s_id] = (days, cum_deficit)
        if days and days[-1] > max_day:
            max_day = days[-1]

    if not all_series_days:
        fig.add_annotation(text="No valid scenario data available", showarrow=False)
        return fig

    # If requested and >= 2 scenarios, calculate and draw the envelope behind lines
    if show_envelope and len(all_series_days) >= 2 and max_day > 0:
        day_range = list(range(1, max_day + 1))
        min_curve = []
        max_curve = []
        mean_curve = []
        for d in day_range:
            vals_at_d = [
                c_vals[d - 1] for (days, c_vals) in all_series_days.values() if len(c_vals) >= d
            ]
            if vals_at_d:
                min_curve.append(float(np.min(vals_at_d)))
                max_curve.append(float(np.max(vals_at_d)))
                mean_curve.append(float(np.mean(vals_at_d)))
            else:
                break
        valid_days = day_range[:len(min_curve)]
        if valid_days:
            # Envelope fill (max curve down to min curve)
            fig.add_trace(go.Scatter(
                x=valid_days + valid_days[::-1],
                y=max_curve + min_curve[::-1],
                fill="toself",
                fillcolor="rgba(14, 165, 233, 0.08)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=True,
                name="Shortlist Range (Min–Max)",
            ))
            # Mean curve
            fig.add_trace(go.Scatter(
                x=valid_days,
                y=mean_curve,
                mode="lines",
                line=dict(color="#94a3b8", width=1.8, dash="dash"),
                name="Shortlist Average Deficit",
                hovertemplate=f"Shortlist Average<br>Day %{{x}}: %{{y:.2f}} {u_label}<extra></extra>",
            ))

    # Add each scenario's cumulative deficit trajectory
    for idx, s_id in enumerate(workspace.selected):
        s = workspace.get(s_id)
        if s_id not in all_series_days:
            continue
        days, cum_deficit = all_series_days[s_id]
        color = palette[idx % len(palette)]
        is_highlight = s_id == highlight_id
        line_w = 3.5 if is_highlight else 2.2
        opacity = 1.0 if (highlight_id is None or is_highlight) else 0.45

        status_tag = " [Included]" if s.status == "accepted" else (" [Excluded]" if s.status == "rejected" else "")
        hist_window = f"{s.provenance.get('source_start', '')} to {s.provenance.get('source_end', '')}"
        rarity = f"{s.features['historical_percentile']:.0%}"

        fig.add_trace(go.Scatter(
            x=days,
            y=cum_deficit,
            mode="lines",
            name=f"{s_id}{status_tag}",
            line=dict(color=color, width=line_w),
            opacity=opacity,
            customdata=[[s_id, s.features['duration_days'], cum_deficit[-1], hist_window, rarity]] * len(days),
            hovertemplate=(
                f"<b>Scenario %{{customdata[0]}}</b><br>"
                f"Day %{{x}} of %{{customdata[1]}}<br>"
                f"Cumulative Deficit: <b>%{{y:.2f}} {u_label}</b><br>"
                f"Final Deficit: %{{customdata[2]:.2f}} {u_label}<br>"
                f"Historical Window: %{{customdata[3]}}<br>"
                f"Historical Rarity: %{{customdata[4]}}<extra></extra>"
            ),
        ))

    fig.update_layout(
        height=450,
        margin=dict(l=55, r=25, t=35, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        hovermode="x unified",
        xaxis=dict(
            title="Scenario Timeline (Elapsed Days)",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            zeroline=False,
        ),
        yaxis=dict(
            title=f"Cumulative Rainfall Deficit ({u_label})",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11),
        ),
    )
    return fig


def multi_scenario_storage_figure(
    workspace: Any,
    simulation_results_by_scenario: dict[str, pd.DataFrame] | None = None,
    config: Any = None,
    initial_pct: float = 0.48,
    conservation_pct: float = 0.0,
    pipeline_active: bool = True,
    unit: str = "us",
    highlight_id: str | None = None,
) -> go.Figure:
    """Overlay reservoir storage drawdown trajectories across all shortlisted scenarios.

    Shows combined storage % alongside standard regulatory drought contingency stages
    (Stage 1, Stage 2, Stage 3 Critical Reserve, and Emergency).
    """
    from basin_core.analysis import simulate_reservoir_drawdown, REGION_N_PRESET

    fig = go.Figure()
    if not workspace or not getattr(workspace, "selected", None):
        fig.add_annotation(text="No shortlisted scenarios to simulate", showarrow=False)
        return fig

    cfg = config if config is not None else getattr(workspace, "water_system_config", None) or REGION_N_PRESET
    bands = [float(v * 100 if v <= 1.0 else v) for v in cfg.stage_bands_pct]
    band_colors = ["#059669", "#d97706", "#ea580c", "#dc2626", "#7f1d1d"]
    bounds = [100.0, *bands, 0.0]

    # Add horizontal stage background rectangles
    for idx, (upper, lower) in enumerate(zip(bounds, bounds[1:])):
        fig.add_hrect(
            y0=lower, y1=upper,
            fillcolor=band_colors[min(idx, len(band_colors) - 1)],
            opacity=0.06,
            line_width=0,
            layer="below",
        )

    # Threshold horizontal reference lines
    for idx, lvl in enumerate(bands):
        fig.add_hline(
            y=lvl,
            line_dash="dot",
            line_color="rgba(150, 150, 150, 0.6)",
            line_width=1,
            annotation_text=f"Stage {idx + 1} ({lvl:.0f}%)",
            annotation_position="top left",
            annotation_font_size=10,
        )

    palette = [
        "#0ea5e9", "#f59e0b", "#10b981", "#8b5cf6",
        "#ec4899", "#06b6d4", "#f97316", "#6366f1",
    ]

    sims = simulation_results_by_scenario or {}

    for idx, s_id in enumerate(workspace.selected):
        s = workspace.get(s_id)
        if s is None:
            continue

        if s_id in sims:
            sim_df = sims[s_id]
        else:
            try:
                sim_df = simulate_reservoir_drawdown(
                    s.series,
                    initial_pct=initial_pct,
                    conservation_pct=conservation_pct,
                    pipeline_active=pipeline_active,
                    config=cfg,
                )
            except Exception:
                sim_df = None

        if sim_df is None or sim_df.empty:
            continue

        color = palette[idx % len(palette)]
        is_highlight = s_id == highlight_id
        line_w = 3.5 if is_highlight else 2.2
        opacity = 1.0 if (highlight_id is None or is_highlight) else 0.5

        status_tag = " [Included]" if s.status == "accepted" else (" [Excluded]" if s.status == "rejected" else "")

        fig.add_trace(go.Scatter(
            x=sim_df["day"],
            y=sim_df["combined_pct"],
            mode="lines",
            name=f"{s_id}{status_tag}",
            line=dict(color=color, width=line_w),
            opacity=opacity,
            customdata=[[s_id, s.features['duration_days'], float(r["combined_pct"]), float(r["combined_acft"])] for _, r in sim_df.iterrows()],
            hovertemplate=(
                f"<b>Scenario %{{customdata[0]}}</b><br>"
                "Day %{x}: <b>%{y:.1f}%</b> (%{customdata[3]:,.0f} ac-ft)<br>"
                f"Duration: %{{customdata[1]}} days<extra></extra>"
            ),
        ))

    fig.update_layout(
        height=450,
        margin=dict(l=55, r=25, t=35, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
        hovermode="x unified",
        xaxis=dict(
            title="Simulation Timeline (Elapsed Days)",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Combined Reservoir Storage (% Capacity)",
            range=[0, max(100.0, initial_pct * 100 + 5)],
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11),
        ),
    )
    return fig

