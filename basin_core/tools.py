"""Hydrologist-focused tools for the BASIN analyst assistant.

Each function takes a Workspace and returns a structured dict of computed
values.  These work independently of any LLM — they are the ground truth
that the assistant's template layer renders into human-readable responses.
"""
from __future__ import annotations

import calendar

import numpy as np
import pandas as pd

from basin_core.analysis import RESERVOIR_ASSUMPTIONS, vector
from basin_core.workspace import Workspace


# ---------------------------------------------------------------------------
# Tool 1 — Scenario profile
# ---------------------------------------------------------------------------

def describe_scenario(workspace: Workspace, scenario_id: str) -> dict:
    """Get the complete profile of a specific rainfall scenario including its
    duration, deficit, station stress, historical context, review status and
    source provenance.  Use this when the user asks about a specific scenario
    by ID, for example 'tell me about B-042' or 'what is scenario B-015'."""
    s = workspace.get(scenario_id)
    f = s.features
    return {
        "id": s.id,
        "revision": s.revision,
        "status": s.status,
        "approved_revision": s.approved_revision,
        "duration_days": f["duration_days"],
        "onset_month": calendar.month_name[f["onset_month"]],
        "deficit_mm": round(f["deficit_mm"], 1),
        "deficit_in": round(f["deficit_mm"] / 25.4, 2),
        "rainfall_mm": round(f["rainfall_mm"], 1),
        "expected_mm": round(f["expected_mm"], 1),
        "concurrence_pct": round(f["concurrence"] * 100, 1),
        "eligible_windows": f["eligible_concurrence_days"],
        "percentile_pct": round(f["historical_percentile"] * 100, 0),
        "benchmark_mm": round(f["benchmark_mm"], 1),
        "benchmark_n": f["benchmark_n"],
        "exceeds_reference": f["beyond_rainfall_reference"],
        "max_dry_days": f["max_dry_days"],
        "score": round(s.score, 2),
        "components": {k: round(v, 2) for k, v in s.components.items()},
        "cluster": s.cluster,
        "cluster_name": getattr(s, "cluster_name", f"Group {s.cluster}"),
        "in_shortlist": s.id in workspace.selected,
        "selection_reason": workspace.selection_reason(s.id),
        "source_start": s.provenance["source_start"],
        "source_end": s.provenance["source_end"],
        "method": s.provenance["method"],
        "retention": s.provenance["retention_by_station"],
        "station_deficits": {k: round(v, 1) for k, v in f["station_deficits_mm"].items()},
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


# ---------------------------------------------------------------------------
# Tool 2 — Side-by-side comparison
# ---------------------------------------------------------------------------

def compare_scenarios(workspace: Workspace, scenario_id_1: str,
                      scenario_id_2: str,
                      scenario_id_3: str = "") -> dict:
    """Compare two or three rainfall scenarios side by side, showing features,
    scores, cluster membership and key differences.  Use when the user asks to
    compare scenarios or asks which scenario is worse or better."""
    ids = [scenario_id_1, scenario_id_2]
    if scenario_id_3:
        ids.append(scenario_id_3)
    scenarios = [workspace.get(sid) for sid in ids]
    rows = {}
    for s in scenarios:
        f = s.features
        rows[s.id] = {
            "duration_days": f["duration_days"],
            "onset": calendar.month_name[f["onset_month"]],
            "deficit_mm": round(f["deficit_mm"], 1),
            "concurrence_pct": round(f["concurrence"] * 100, 1),
            "percentile_pct": round(f["historical_percentile"] * 100, 0),
            "score": round(s.score, 2),
            "cluster_name": getattr(s, "cluster_name", f"Group {s.cluster}"),
            "status": s.status,
            "revision": s.revision,
            "max_dry_days": f["max_dry_days"],
        }
    a, b = scenarios[0].features, scenarios[1].features
    deltas = {
        "deficit_delta_mm": round(a["deficit_mm"] - b["deficit_mm"], 1),
        "duration_delta_days": a["duration_days"] - b["duration_days"],
        "concurrence_delta_pct": round((a["concurrence"] - b["concurrence"]) * 100, 1),
    }
    return {"scenarios": rows, "deltas": deltas,
            "_snapshot": workspace.source.manifest["sha256"][:12]}


# ---------------------------------------------------------------------------
# Tool 3 — Ranking explanation
# ---------------------------------------------------------------------------

def explain_ranking(workspace: Workspace, scenario_id: str) -> dict:
    """Explain why a scenario has its current ranking score, showing each
    weight contribution and its position.  Use when the user asks 'why did
    this rank here' or 'what affects the score'."""
    s = workspace.get(scenario_id)
    ranked = sorted(workspace.scenarios, key=lambda x: (-x.score, x.id))
    position = next(i + 1 for i, x in enumerate(ranked) if x.id == s.id)
    total = sum(workspace.weights.values())
    return {
        "id": s.id,
        "score": round(s.score, 2),
        "position": position,
        "total_candidates": len(workspace.scenarios),
        "components": {k: round(v, 2) for k, v in s.components.items()},
        "weights": dict(workspace.weights),
        "weight_pcts": {k: round(v / total * 100, 1) for k, v in workspace.weights.items()},
        "cluster_name": getattr(s, "cluster_name", f"Group {s.cluster}"),
        "in_shortlist": s.id in workspace.selected,
        "selection_reason": workspace.selection_reason(s.id),
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


# ---------------------------------------------------------------------------
# Tool 4 — Historical rainfall query
# ---------------------------------------------------------------------------

def query_rainfall(workspace: Workspace, station_id: str,
                   start_date: str, end_date: str) -> dict:
    """Look up historical rainfall observations for a specific station and
    date range from the NOAA snapshot.  Use when the user asks about observed
    rainfall, historical data, or wants to check actual measurements."""
    station_ids = [s["id"] for s in workspace.source.manifest["stations"]]
    if station_id not in station_ids:
        raise ValueError(f"Unknown station: {station_id}. Available: {station_ids}")
    daily = workspace.source.select([station_id])
    subset = daily.loc[start_date:end_date]
    if subset.empty:
        raise ValueError(f"No data for {station_id} in {start_date} to {end_date}")
    values = subset[station_id]
    valid = values.dropna()
    monthly = valid.groupby(valid.index.to_period("M")).agg(["sum", "count"])
    monthly.columns = ["total_mm", "valid_days"]
    return {
        "station_id": station_id,
        "station_name": next(s["name"] for s in workspace.source.manifest["stations"]
                             if s["id"] == station_id),
        "start": str(subset.index[0].date()),
        "end": str(subset.index[-1].date()),
        "calendar_days": len(subset),
        "valid_days": len(valid),
        "missing_days": len(subset) - len(valid),
        "total_mm": round(float(valid.sum()), 1),
        "mean_daily_mm": round(float(valid.mean()), 2) if len(valid) else 0.0,
        "max_daily_mm": round(float(valid.max()), 1) if len(valid) else 0.0,
        "monthly_totals": {str(k): round(float(v["total_mm"]), 1)
                           for k, v in monthly.iterrows()},
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


# ---------------------------------------------------------------------------
# Tool 5 — Station stress / concurrence analysis
# ---------------------------------------------------------------------------

def check_concurrence(workspace: Workspace, scenario_id: str) -> dict:
    """Analyse station stress patterns for a scenario, showing which stations
    are stressed and how often they are stressed simultaneously.  Use when the
    user asks about station stress, concurrence or simultaneous drought."""
    s = workspace.get(scenario_id)
    f = s.features
    ref = workspace.reference
    expected = pd.DataFrame(ref.expected(s.series.index),
                            index=s.series.index, columns=s.series.columns)
    net = expected.to_numpy() - s.series.to_numpy()
    rolling = pd.DataFrame(net).rolling(30, min_periods=30).sum().to_numpy()[29:]
    stations = {}
    for i, col in enumerate(s.series.columns):
        stressed = int((rolling[:, i] > ref.thresholds[i]).sum())
        stations[col] = {
            "stressed_windows": stressed,
            "total_windows": len(rolling),
            "stress_pct": round(stressed / max(len(rolling), 1) * 100, 1),
            "deficit_mm": round(float(f["station_deficits_mm"][col]), 1),
        }
    return {
        "id": s.id,
        "concurrence_pct": round(f["concurrence"] * 100, 1),
        "eligible_windows": f["eligible_concurrence_days"],
        "station_count": len(s.series.columns),
        "stations": stations,
        "interpretation": (
            "station stress frequency (single station)"
            if len(s.series.columns) == 1
            else "fraction of windows where ALL stations exceeded their 75th-percentile stress threshold"
        ),
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


# ---------------------------------------------------------------------------
# Tool 6 — Weight sensitivity test
# ---------------------------------------------------------------------------

def run_sensitivity(workspace: Workspace, severity: int = -1,
                    duration: int = -1, concurrence: int = -1,
                    season: int = -1) -> dict:
    """Test how changing ranking weights would affect scenario positions and
    the shortlist without modifying the workspace.  Use when the user asks
    'what if I increase duration weight' or 'how would different priorities
    change the ranking'.  Pass only the weights to change; others keep their
    current value.  Each weight is an integer 0-100."""
    new_weights = dict(workspace.weights)
    if severity >= 0:
        new_weights["severity"] = severity
    if duration >= 0:
        new_weights["duration"] = duration
    if concurrence >= 0:
        new_weights["concurrence"] = concurrence
    if season >= 0:
        new_weights["season"] = season
    if sum(new_weights.values()) <= 0:
        raise ValueError("At least one weight must be positive")
    result = workspace.compare_weights(new_weights)
    changes = []
    for row in result["rows"]:
        delta = row["rank_before"] - row["rank_after"]
        if delta != 0:
            changes.append({
                "id": row["id"],
                "rank_before": row["rank_before"],
                "rank_after": row["rank_after"],
                "change": delta,
                "score_before": round(row["score_before"], 2),
                "score_after": round(row["score_after"], 2),
                "would_enter_shortlist": row["suggested_after"] and not row["selected_before"],
                "would_leave_shortlist": row["selected_before"] and not row["suggested_after"],
            })
    top = sorted(changes, key=lambda c: abs(c["change"]), reverse=True)[:5]
    shortlist_impact = [c for c in changes
                        if c["would_enter_shortlist"] or c["would_leave_shortlist"]]
    return {
        "weights_before": dict(workspace.weights),
        "weights_after": new_weights,
        "top_movers": top,
        "shortlist_impact": shortlist_impact,
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


# ---------------------------------------------------------------------------
# Tool 7 — Evidence summary
# ---------------------------------------------------------------------------

def summarize_evidence(workspace: Workspace, scenario_id: str) -> dict:
    """List all evidence records and unresolved conflicts attached to a
    scenario.  Use when the user asks about evidence, assumptions, sources
    or disagreements for a specific scenario."""
    s = workspace.get(scenario_id)
    attached_ids = workspace.evidence_refs.get(s.id, [])
    registry = {e["id"]: e for e in workspace.evidence}
    attached = [{
        "id": eid, "title": registry[eid]["title"],
        "kind": registry[eid]["kind"],
        "review_status": registry[eid]["review_status"],
        "publisher": registry[eid]["publisher"],
        "source": registry[eid]["source_locator"],
        "geography": registry[eid]["geographic_scope"],
    } for eid in attached_ids if eid in registry]
    conflicts = [{
        "id": c["id"], "left": c["left_id"], "right": c["right_id"],
        "disagreement": c["disagreement"], "status": c["status"],
        "resolution": c["resolution"] or "No disposition recorded",
    } for c in workspace.conflicts]
    return {
        "scenario_id": s.id,
        "evidence_count": len(attached),
        "evidence": attached,
        "conflict_count": len(conflicts),
        "unresolved_count": sum(1 for c in conflicts if c["status"] == "unresolved"),
        "conflicts": conflicts,
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


# ---------------------------------------------------------------------------
# Tool 8 — Cluster / drought profile description
# ---------------------------------------------------------------------------

def describe_cluster(workspace: Workspace, cluster_id: int) -> dict:
    """Describe a drought profile group, showing what features define it and
    which scenarios belong to it.  Use when the user asks about a drought
    profile, group, cluster or 'what makes these scenarios similar'."""
    clusters = sorted({s.cluster for s in workspace.scenarios})
    if cluster_id not in clusters:
        if (cluster_id + 1) in clusters:
            cluster_id = cluster_id + 1
        elif clusters:
            cluster_id = clusters[0]
    members = [s for s in workspace.scenarios if s.cluster == cluster_id]
    if not members:
        raise ValueError(f"No scenarios in cluster {cluster_id}. Available: {clusters}")
    name = getattr(members[0], "cluster_name", f"Group {cluster_id}")
    feat = np.array([vector(s) for s in members])
    centroid = feat.mean(axis=0)
    shortlisted = [s.id for s in members if s.id in workspace.selected]
    return {
        "cluster_id": cluster_id,
        "cluster_name": name,
        "member_count": len(members),
        "shortlisted_ids": shortlisted,
        "centroid_percentile": round(float(centroid[0]) * 100, 1),
        "centroid_duration_frac": round(float(centroid[1]), 3),
        "centroid_concurrence": round(float(centroid[2]) * 100, 1),
        "centroid_summer_frac": round(float(centroid[3]) * 100, 1),
        "centroid_dry_spell_frac": round(float(centroid[4]), 3),
        "score_min": round(min(s.score for s in members), 2),
        "score_max": round(max(s.score for s in members), 2),
        "score_mean": round(float(np.mean([s.score for s in members])), 2),
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


# ---------------------------------------------------------------------------
# Tool 9 — Export readiness check
# ---------------------------------------------------------------------------

def check_export_readiness(workspace: Workspace) -> dict:
    """Check whether the workspace is ready to export a verified packet and
    list any blockers.  Use when the user asks 'can I export', 'what do I
    need to do before sharing' or 'is the packet ready'."""
    selected = [workspace.get(sid) for sid in workspace.selected]
    unreviewed = [s for s in selected if s.status == "unreviewed"]
    accepted = [s for s in selected
                if s.status == "accepted" and s.approved_revision == s.revision]
    rejected = [s for s in selected if s.status == "rejected"]
    stale = [s for s in selected
             if s.status == "accepted" and s.approved_revision != s.revision]
    unresolved = [c for c in workspace.conflicts if c["status"] == "unresolved"]
    blockers = []
    if unreviewed:
        blockers.append(f"{len(unreviewed)} scenario(s) not reviewed: "
                        + ", ".join(s.id for s in unreviewed))
    if stale:
        blockers.append(f"{len(stale)} scenario(s) edited since approval: "
                        + ", ".join(s.id for s in stale))
    if not accepted:
        blockers.append("No scenarios currently accepted")
    try:
        workspace.exportable()
    except ValueError as error:
        if str(error) not in blockers:
            blockers.append(str(error))
    return {
        "ready": len(blockers) == 0,
        "selected_count": len(selected),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "unreviewed_count": len(unreviewed),
        "stale_count": len(stale),
        "unresolved_conflicts": len(unresolved),
        "blockers": blockers,
        "accepted_ids": [s.id for s in accepted],
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


# ---------------------------------------------------------------------------
# Tool 10 — Data provenance
# ---------------------------------------------------------------------------

def get_data_provenance(workspace: Workspace) -> dict:
    """Get information about the data source including snapshot identity,
    stations, coverage period and quality flags.  Use when the user asks
    about the data, where it comes from, station details or NOAA coverage."""
    m = workspace.source.manifest
    quality_lookup = {q["station_id"]: q for q in m["quality"]}
    stations = []
    for s in m["stations"]:
        q = quality_lookup.get(s["id"], {})
        stations.append({
            "id": s["id"], "name": s["name"],
            "latitude": s["latitude"], "longitude": s["longitude"],
            "completeness_pct": q.get("completeness_pct"),
            "missing_days": q.get("missing_or_excluded_days"),
        })
    return {
        "source": "NOAA NCEI GHCN-Daily",
        "documentation": m["documentation"],
        "period": f"{m['start']} to {m['end']}",
        "downloaded_at": m["downloaded_at"],
        "snapshot_sha256": m["sha256"],
        "station_count": len(stations),
        "stations": stations,
    }


# ---------------------------------------------------------------------------
# Tool 11 — Find scenarios by historical year
# ---------------------------------------------------------------------------

def find_scenarios_by_year(workspace: Workspace, year: int = 2011) -> dict:
    """Find rainfall scenarios in the workspace that originate from a specific
    historical observation year (e.g. 2011, 2000, 2022). Use when the user asks
    about scenarios from a certain year or wants recent vs older candidates."""
    matched = [s for s in workspace.scenarios if s.provenance.get("source_start", "").startswith(str(year))]
    results = []
    for s in sorted(matched, key=lambda x: -x.score):
        f = s.features
        results.append({
            "id": s.id,
            "duration_days": f["duration_days"],
            "onset_month": calendar.month_name[f["onset_month"]],
            "deficit_mm": round(f["deficit_mm"], 1),
            "concurrence_pct": round(f["concurrence"] * 100, 1),
            "percentile_pct": round(f["historical_percentile"] * 100, 0),
            "score": round(s.score, 2),
            "cluster_name": getattr(s, "cluster_name", f"Group {s.cluster}"),
            "in_shortlist": s.id in workspace.selected,
            "source_start": s.provenance["source_start"],
            "source_end": s.provenance["source_end"],
        })
    return {
        "year": year,
        "total_matches": len(results),
        "total_candidates": len(workspace.scenarios),
        "scenarios": results[:8],
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


# ---------------------------------------------------------------------------
# Tool 12 — Reservoir infrastructure stress test
# ---------------------------------------------------------------------------

def test_reservoir_infrastructure(workspace: Workspace, scenario_id: str = "",
                                  year: int | None = None,
                                  rainfall_reduction_pct: float = 0.0,
                                  initial_storage_pct: float = 48.0,
                                  conservation_pct: float = 0.0,
                                  baseline_kind: str = "scenario_revision",
                                  pipeline_active: bool = True,
                                  revision: int | None = None) -> dict:
    """Save an illustrative experiment. All public percentages use 0 to 100."""
    from basin_core.simulation import SimulationSettings, percent_fraction, resolve_scenario, spectrum_view
    scenario = resolve_scenario(workspace, scenario_id, year, revision)
    reduction = percent_fraction(rainfall_reduction_pct, "Rainfall reduction")
    settings = SimulationSettings.from_percent(initial_storage_percent=initial_storage_pct,
        conservation_percent=conservation_pct,
        baseline_kind=baseline_kind, pipeline_active=pipeline_active,
        retention_percentages=((1 - reduction) * 100,))
    run = workspace.run_simulation(scenario.id, settings)
    spec = spectrum_view(run)
    row = spec["summary_table"][0]
    sim = next(iter(spec["tier_results"].values()))["df"]
    return {
        "simulation_id": run["id"], "baseline_kind": baseline_kind,
        "scenario_id": scenario.id, "scenario_revision": scenario.revision,
        "source_start": scenario.provenance["source_start"], "source_end": scenario.provenance["source_end"],
        "duration_days": spec["duration_days"], "rainfall_reduction_pct": rainfall_reduction_pct,
        "initial_pct": spec["initial_pct"], "conservation_pct": spec["conservation_pct"],
        "initial_acft": settings.initial_storage_fraction * sum(RESERVOIR_ASSUMPTIONS["capacities_acft"].values()),
        **{key: row[key] for key in ("final_pct", "final_acft", "min_pct", "min_acft", "survived_critical_20pct")},
        "day_band1_40pct": row["day_stage1_40"], "day_band2_30pct": row["day_stage2_30"],
        "day_band3_20pct": row["day_stage3_20"], "day_band4_15pct": row["day_emergency_15"],
        "total_inflow_acft": round(float(sim["inflow_acft"].sum()), 0),
        "total_evap_acft": round(float(sim["evap_acft"].sum()), 0),
        "total_demand_served_acft": round(float(sim["served_demand_acft"].sum()), 0),
        "_snapshot": workspace.source.manifest["sha256"][:12],
    }


def run_stress_spectrum(workspace: Workspace, scenario_id: str = "", year: int | None = None,
                        initial_storage_pct: float = 48.0, conservation_pct: float = 0.0,
                        baseline_kind: str = "scenario_revision", pipeline_active: bool = True,
                        revision: int | None = None) -> dict:
    """Save four additional rainfall stress tiers; public percentages are 0 to 100."""
    from basin_core.simulation import SimulationSettings, resolve_scenario, spectrum_view
    scenario = resolve_scenario(workspace, scenario_id, year, revision)
    settings = SimulationSettings.from_percent(initial_storage_percent=initial_storage_pct,
        conservation_percent=conservation_pct, baseline_kind=baseline_kind, pipeline_active=pipeline_active)
    run = workspace.run_simulation(scenario.id, settings)
    spec = spectrum_view(run)
    return {**spec, "simulation_id": run["id"], "baseline_kind": baseline_kind,
            "scenario_id": scenario.id, "scenario_revision": scenario.revision,
            "source_start": scenario.provenance["source_start"], "source_end": scenario.provenance["source_end"],
            "tiers": spec["summary_table"], "_snapshot": workspace.source.manifest["sha256"][:12]}


# ---------------------------------------------------------------------------
# Registry — maps function names to callables for the assistant loop
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = [
    describe_scenario,
    compare_scenarios,
    explain_ranking,
    query_rainfall,
    check_concurrence,
    run_sensitivity,
    summarize_evidence,
    describe_cluster,
    check_export_readiness,
    get_data_provenance,
    find_scenarios_by_year,
    test_reservoir_infrastructure,
    run_stress_spectrum,
]

TOOL_REGISTRY = {fn.__name__: fn for fn in TOOL_FUNCTIONS}

