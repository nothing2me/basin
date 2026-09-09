"""BASIN analyst assistant — embedded, deterministic intent routing.

The built-in engine extracts supported intents and parameters from questions.
Read-only Python tools compute workspace results; fixed templates render them.
No model server, model download, or external inference service is used.
"""
from __future__ import annotations

import json
import logging
import math
import re
from typing import Any
from jsonschema import Draft202012Validator

from basin_core.tools import TOOL_FUNCTIONS, TOOL_REGISTRY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Response templates — every number is a named variable from tool output
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, str] = {

    "describe_scenario": """**Scenario {id}** — Rev. {revision} ({status})

| Metric | Value |
|---|---|
| Duration | {duration_days} days from {onset_month} |
| Rainfall shortfall | {deficit_mm} mm / station ({deficit_in} in) |
| Scenario rainfall | {rainfall_mm} mm vs {expected_mm} mm expected |
| Station stress | {concurrence_pct}% of eligible 30-day windows |
| How unusual vs history | {percentile_pct}th percentile (n = {benchmark_n}) |
| Rainfall reference | {benchmark_mm} mm — {exceed_text} |
| Longest dry spell | {max_dry_days} days |
| Priority score | {score} |
| Profile | {cluster_name} |
| Selection | {selection_reason} |
| Source window | {source_start} to {source_end} |

> Source: BASIN workspace · Snapshot `{_snapshot}…`
> ⚠️ Station suitability is provisional. Deficit is per-station mean, not basin water volume. Score is a ranking priority, not a probability.""",

    "compare_scenarios": """**Scenario comparison**

| Metric | {id_list} |
|---|{col_sep}|
{comparison_rows}

**Δ {id_a} vs {id_b}:** deficit {deficit_delta_mm:+.1f} mm · duration {duration_delta_days:+d} days · concurrence {concurrence_delta_pct:+.1f}%

> Source: BASIN workspace · Snapshot `{_snapshot}…`
> ⚠️ Differences show measurement deltas. A larger deficit does not imply greater real-world danger without hydrologic analysis.""",

    "explain_ranking": """**Ranking breakdown for {id}** — position {position} of {total_candidates}

| Priority | Weight | Contribution |
|---|---|---|
{component_rows}
| **Total** | **100%** | **{score}** |

Selection: {selection_reason}
Profile: {cluster_name} · {"In shortlist ✓" if in_shortlist else "Not in shortlist"}

> Source: BASIN workspace · Snapshot `{_snapshot}…`
> ⚠️ Scores are ranking priorities set by the user, not likelihoods or safety ratings.""",

    "query_rainfall": """**{station_name}** (`{station_id}`) — {start} to {end}

| Metric | Value |
|---|---|
| Calendar days | {calendar_days} |
| Valid observations | {valid_days} |
| Missing / excluded | {missing_days} |
| Total rainfall | {total_mm} mm |
| Daily mean | {mean_daily_mm} mm |
| Daily maximum | {max_daily_mm} mm |

{monthly_table}

> Source: NOAA GHCN-Daily snapshot `{_snapshot}…`
> ⚠️ These are station-point observations, not catchment-averaged precipitation.""",

    "check_concurrence": """**Station stress analysis for {id}**

Overall concurrence: **{concurrence_pct}%** of {eligible_windows} eligible 30-day windows
Interpretation: {interpretation}

{station_table}

> Source: BASIN workspace · Snapshot `{_snapshot}…`
> ⚠️ Stress is defined by exceedance of each station's 75th-percentile rolling deficit (1991-2020). It is not an official drought category.""",

    "run_sensitivity": """**Sensitivity test: weight change impact**

| Priority | Before | After |
|---|---|---|
{weight_rows}

**Top position changes:**
{mover_rows}

{shortlist_text}

> Source: BASIN workspace · Snapshot `{_snapshot}…`
> ⚠️ This is a preview only. No workspace data was modified. Priorities are illustrative.""",

    "summarize_evidence": """**Evidence for scenario {scenario_id}** — {evidence_count} record(s), {unresolved_count} unresolved conflict(s)

{evidence_table}

{conflict_text}

> Source: BASIN workspace · Snapshot `{_snapshot}…`
> ⚠️ Evidence types and applicability are analyst declarations. No automatic trust score is assigned.""",

    "describe_cluster": """**Drought profile: {cluster_name}** (Group {cluster_id})

{member_count} scenarios · {shortlist_count} in shortlist
Scores: {score_min} – {score_max} (mean {score_mean})

| Centroid feature | Value |
|---|---|
| Historical severity | {centroid_percentile}th percentile |
| Duration fraction | {centroid_duration_frac} of year |
| Station concurrence | {centroid_concurrence}% |
| Summer fraction | {centroid_summer_frac}% |
| Dry spell fraction | {centroid_dry_spell_frac} of year |

> Source: BASIN workspace · Snapshot `{_snapshot}…`
> ⚠️ KMeans groups describe feature patterns, not scientifically validated drought types.""",

    "check_export_readiness": """**Export readiness: {"✅ Ready" if ready else "❌ Not ready"}**

| Status | Count |
|---|---|
| Selected for review | {selected_count} |
| Accepted (current revision) | {accepted_count} |
| Rejected | {rejected_count} |
| Not yet reviewed | {unreviewed_count} |
| Edited since approval | {stale_count} |
| Unresolved conflicts | {unresolved_conflicts} |

{blocker_text}

> ⚠️ Export checks internal consistency. It does not certify scientific validity or professional approval.""",

    "get_data_provenance": """**Data source: {source}**

| Detail | Value |
|---|---|
| Coverage | {period} |
| Downloaded | {downloaded_at} |
| Snapshot SHA-256 | `{snapshot_sha256}` |
| Documentation | {documentation} |

**Stations ({station_count}):**
{station_table}

> ⚠️ Airport stations are provisional regional proxies. Catchment suitability and spatial aggregation require practitioner review.""",

    "find_scenarios_by_year": """**Scenarios matching year {year}** — {total_matches} found in current run

{scenario_table}

> Source: BASIN workspace · Snapshot `{_snapshot}…`
> ⚠️ Historical source dates indicate which observed physical weather sequence was resampled.""",

    "test_reservoir_infrastructure": """**Reservoir Infrastructure Stress Test: Scenario {scenario_id}** ({source_start} to {source_end})
Stress adjustment: **{rainfall_reduction_pct}% lower rainfall** · Duration: **{duration_days} days**

| Storage Metric | Combined Pool | Water Volume |
|---|---|---|
| Initial storage | {initial_pct}% | {initial_acft:,.0f} ac-ft |
| Final storage | {final_pct}% | {final_acft:,.0f} ac-ft |
| Lowest point reached | {min_pct}% | {min_acft:,.0f} ac-ft |

**Threshold breaches during scenario:**
- Stage 1 (40%): {band1_text}
- Stage 2 (30%): {band2_text}
- Stage 3 (20% Critical): {band3_text}
- Emergency (15%): {band4_text}

**Infrastructure assessment:**
{assessment_text}

> Source: BASIN reservoir experiment · Snapshot `{_snapshot}…`
> ⚠️ Illustrative two-pool simulation (Lake Corpus Christi + Choke Canyon). Not an official forecast or regulatory restriction date.""",

    "run_stress_spectrum": """**Reservoir Stress Spectrum: Scenario {scenario_id}** ({source_start} to {source_end})
Duration: **{duration_days} days** · Initial storage: **{initial_pct}%** · Conservation: **{conservation_pct}%**

| Rainfall Tier | Retention | Min Storage | Stage 1 (40%) | Stage 2 (30%) | Critical (20%) | Emergency (15%) | Infrastructure Survival |
|---|---|---|---|---|---|---|---|
{spectrum_table}

**Tipping Point Analysis:**
{tipping_point_text}

> Source: BASIN multi-tier stress spectrum · Snapshot `{_snapshot}…`
> ⚠️ Illustrative two-pool simulation across climate stress tiers. Not an official regulatory declaration.""",
}


# ---------------------------------------------------------------------------
# Template rendering helpers
# ---------------------------------------------------------------------------

def _render_describe_scenario(data: dict) -> str:
    data = dict(data)
    data["exceed_text"] = "exceeded" if data["exceeds_reference"] else "not exceeded"
    return TEMPLATES["describe_scenario"].format_map(data)


def _render_compare_scenarios(data: dict) -> str:
    scenarios = data["scenarios"]
    ids = list(scenarios.keys())
    metrics = ["duration_days", "onset", "deficit_mm", "concurrence_pct",
               "percentile_pct", "score", "cluster_name", "status", "max_dry_days"]
    labels = {"duration_days": "Duration (days)", "onset": "Onset",
              "deficit_mm": "Deficit (mm)", "concurrence_pct": "Concurrence %",
              "percentile_pct": "Percentile", "score": "Score",
              "cluster_name": "Profile", "status": "Status",
              "max_dry_days": "Max dry days"}
    rows = []
    for m in metrics:
        vals = " | ".join(str(scenarios[sid][m]) for sid in ids)
        rows.append(f"| {labels[m]} | {vals} |")
    return TEMPLATES["compare_scenarios"].format_map({
        "id_list": " | ".join(ids),
        "col_sep": " | ".join("---" for _ in ids),
        "comparison_rows": "\n".join(rows),
        "id_a": ids[0], "id_b": ids[1],
        **data["deltas"], "_snapshot": data["_snapshot"],
    })


def _render_explain_ranking(data: dict) -> str:
    rows = []
    for k in data["components"]:
        rows.append(f"| {k.title()} | {data['weight_pcts'][k]}% | {data['components'][k]} |")
    data = dict(data)
    data["component_rows"] = "\n".join(rows)
    data["in_shortlist"] = data["in_shortlist"]
    # Evaluate the conditional inline
    template = TEMPLATES["explain_ranking"]
    shortlist_text = "In shortlist ✓" if data["in_shortlist"] else "Not in shortlist"
    result = template.replace('{"In shortlist ✓" if in_shortlist else "Not in shortlist"}',
                              shortlist_text)
    return result.format_map(data)


def _render_query_rainfall(data: dict) -> str:
    monthly = data["monthly_totals"]
    if monthly:
        header = "| Month | Total mm |\n|---|---|"
        rows = "\n".join(f"| {k} | {v} |" for k, v in monthly.items())
        table = header + "\n" + rows
    else:
        table = "No monthly data available."
    data = dict(data)
    data["monthly_table"] = table
    return TEMPLATES["query_rainfall"].format_map(data)


def _render_check_concurrence(data: dict) -> str:
    header = "| Station | Stressed windows | Total | Stress % | Deficit mm |\n|---|---|---|---|---|"
    rows = []
    for sid, info in data["stations"].items():
        rows.append(f"| {sid} | {info['stressed_windows']} | {info['total_windows']} "
                    f"| {info['stress_pct']}% | {info['deficit_mm']} |")
    data = dict(data)
    data["station_table"] = header + "\n" + "\n".join(rows)
    return TEMPLATES["check_concurrence"].format_map(data)


def _render_run_sensitivity(data: dict) -> str:
    weight_rows = []
    for k in data["weights_before"]:
        weight_rows.append(f"| {k.title()} | {data['weights_before'][k]} | {data['weights_after'][k]} |")
    mover_rows = []
    for m in data["top_movers"]:
        arrow = "↑" if m["change"] > 0 else "↓"
        mover_rows.append(f"- **{m['id']}**: #{m['rank_before']} → #{m['rank_after']} "
                          f"({arrow}{abs(m['change'])}) · score {m['score_before']} → {m['score_after']}")
    if not mover_rows:
        mover_rows = ["- No position changes with these weights."]
    impact = data["shortlist_impact"]
    if impact:
        entering = [c["id"] for c in impact if c["would_enter_shortlist"]]
        leaving = [c["id"] for c in impact if c["would_leave_shortlist"]]
        parts = []
        if entering:
            parts.append(f"Would enter shortlist: {', '.join(entering)}")
        if leaving:
            parts.append(f"Would leave shortlist: {', '.join(leaving)}")
        shortlist_text = "\n".join(parts)
    else:
        shortlist_text = "No shortlist membership changes."
    return TEMPLATES["run_sensitivity"].format_map({
        "weight_rows": "\n".join(weight_rows),
        "mover_rows": "\n".join(mover_rows),
        "shortlist_text": shortlist_text,
        "_snapshot": data["_snapshot"],
    })


def _render_summarize_evidence(data: dict) -> str:
    if data["evidence"]:
        header = "| ID | Title | Kind | Status |\n|---|---|---|---|"
        rows = "\n".join(f"| {e['id']} | {e['title']} | {e['kind']} | {e['review_status']} |"
                         for e in data["evidence"])
        table = header + "\n" + rows
    else:
        table = "No evidence records attached."
    if data["conflicts"]:
        parts = ["**Conflicts:**"]
        for c in data["conflicts"]:
            parts.append(f"- [{c['status']}] {c['left']} vs {c['right']}: "
                         f"{c['disagreement']} — {c['resolution']}")
        conflict_text = "\n".join(parts)
    else:
        conflict_text = "No evidence disagreements recorded."
    data = dict(data)
    data["evidence_table"] = table
    data["conflict_text"] = conflict_text
    return TEMPLATES["summarize_evidence"].format_map(data)


def _render_describe_cluster(data: dict) -> str:
    data = dict(data)
    data["shortlist_count"] = len(data["shortlisted_ids"])
    return TEMPLATES["describe_cluster"].format_map(data)


def _render_check_export_readiness(data: dict) -> str:
    data = dict(data)
    if data["blockers"]:
        data["blocker_text"] = "**Blockers:**\n" + "\n".join(
            f"- ❌ {b}" for b in data["blockers"])
    else:
        data["blocker_text"] = "✅ All requirements met. Ready to build the export packet."
    ready_text = "✅ Ready" if data["ready"] else "❌ Not ready"
    template = TEMPLATES["check_export_readiness"].replace(
        '{"✅ Ready" if ready else "❌ Not ready"}', ready_text)
    return template.format_map(data)


def _render_get_data_provenance(data: dict) -> str:
    header = "| Station | ID | Lat | Lon | Complete % | Missing days |\n|---|---|---|---|---|---|"
    rows = []
    for s in data["stations"]:
        rows.append(f"| {s['name']} | {s['id']} | {s['latitude']} | {s['longitude']} "
                    f"| {s['completeness_pct']} | {s['missing_days']} |")
    data = dict(data)
    data["station_table"] = header + "\n" + "\n".join(rows)
    return TEMPLATES["get_data_provenance"].format_map(data)


def _render_find_scenarios_by_year(data: dict) -> str:
    scenarios = data.get("scenarios", [])
    if scenarios:
        header = "| ID | Duration | Deficit mm | Concurrence % | Score | Shortlist | Source Dates |\n|---|---|---|---|---|---|---|"
        rows = []
        for s in scenarios:
            shortlist_mark = "✓" if s["in_shortlist"] else "—"
            rows.append(f"| **{s['id']}** | {s['duration_days']}d | {s['deficit_mm']} | "
                        f"{s['concurrence_pct']}% | {s['score']} | {shortlist_mark} | "
                        f"{s['source_start']} to {s['source_end']} |")
        table = header + "\n" + "\n".join(rows)
    else:
        table = f"No scenarios in the current candidate pool originated in year {data['year']}."
    data = dict(data)
    data["scenario_table"] = table
    return TEMPLATES["find_scenarios_by_year"].format_map(data)


def _render_test_reservoir_infrastructure(data: dict) -> str:
    data = dict(data)
    data["band1_text"] = f"Day {data['day_band1_40pct']}" if data["day_band1_40pct"] is not None else "Not reached ✓"
    data["band2_text"] = f"Day {data['day_band2_30pct']}" if data["day_band2_30pct"] is not None else "Not reached ✓"
    data["band3_text"] = f"Day {data['day_band3_20pct']}" if data["day_band3_20pct"] is not None else "Not reached ✓"
    data["band4_text"] = f"Day {data['day_band4_15pct']}" if data["day_band4_15pct"] is not None else "Not reached ✓"

    if data["survived_critical_20pct"]:
        data["assessment_text"] = (
            f"✅ **System survives critical threshold**: Combined storage remained above 20% throughout "
            f"the {data['duration_days']}-day scenario, bottoming at **{data['min_pct']}%** ({data['min_acft']:,.0f} ac-ft)."
        )
    else:
        data["assessment_text"] = (
            f"⚠️ **Severe infrastructure deficit**: Combined storage dropped to **{data['min_pct']}%** "
            f"({data['min_acft']:,.0f} ac-ft), breaching the 20% critical threshold on **Day {data['day_band3_20pct']}**."
        )
    return TEMPLATES["test_reservoir_infrastructure"].format_map(data)


def _render_run_stress_spectrum(data: dict) -> str:
    data = dict(data)
    rows = []
    for r in data.get("summary_table", []):
        d1 = f"Day {r['day_stage1_40']}" if r["day_stage1_40"] else "Not reached ✓"
        d2 = f"Day {r['day_stage2_30']}" if r["day_stage2_30"] else "Not reached ✓"
        d3 = f"Day {r['day_stage3_20']}" if r["day_stage3_20"] else "Not reached ✓"
        d4 = f"Day {r['day_emergency_15']}" if r["day_emergency_15"] else "Not reached ✓"
        rows.append(
            f"| {r['tier_label']} | {r['retention_pct']}% | {r['min_pct']}% ({r['min_acft']:,.0f} ac-ft) | {d1} | {d2} | {d3} | {d4} | {r['status']} |"
        )
    data["spectrum_table"] = "\n".join(rows)

    st = data.get("summary_table", [])
    safe_tiers = [r for r in st if r["survived_critical_20pct"]]
    breached_tiers = [r for r in st if not r["survived_critical_20pct"]]
    if safe_tiers and breached_tiers:
        highest_fail = breached_tiers[0]
        lowest_pass = safe_tiers[-1]
        data["tipping_point_text"] = (
            f"The critical breaking point occurs between **{lowest_pass['retention_pct']}% rainfall** ({lowest_pass['status']}) "
            f"and **{highest_fail['retention_pct']}% rainfall** (critical 20% breached on Day {highest_fail['day_stage3_20']})."
        )
    elif not breached_tiers:
        data["tipping_point_text"] = "✅ **System resilient across all evaluated tiers**: Storage remains above 20% critical reserve even under catastrophic 40% rainfall."
    else:
        data["tipping_point_text"] = f"⚠️ **System vulnerable across all tiers**: Even at 100% historical baseline, critical 20% threshold is breached on Day {breached_tiers[0]['day_stage3_20']}."

    return TEMPLATES["run_stress_spectrum"].format_map(data)


RENDERERS = {
    "describe_scenario": _render_describe_scenario,
    "compare_scenarios": _render_compare_scenarios,
    "explain_ranking": _render_explain_ranking,
    "query_rainfall": _render_query_rainfall,
    "check_concurrence": _render_check_concurrence,
    "run_sensitivity": _render_run_sensitivity,
    "summarize_evidence": _render_summarize_evidence,
    "describe_cluster": _render_describe_cluster,
    "check_export_readiness": _render_check_export_readiness,
    "get_data_provenance": _render_get_data_provenance,
    "find_scenarios_by_year": _render_find_scenarios_by_year,
    "test_reservoir_infrastructure": _render_test_reservoir_infrastructure,
    "run_stress_spectrum": _render_run_stress_spectrum,
}


def render_tool_result(tool_name: str, data: dict) -> str:
    """Render a tool's computed dict into a grounded markdown response."""
    renderer = RENDERERS.get(tool_name)
    if renderer is None:
        return f"Tool `{tool_name}` returned:\n```json\n{json.dumps(data, indent=2, default=str)}\n```"
    try:
        return renderer(data)
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning("Template rendering failed for %s: %s", tool_name, exc)
        return f"Tool `{tool_name}` returned:\n```json\n{json.dumps(data, indent=2, default=str)}\n```"


# ---------------------------------------------------------------------------
# Conversation loop
# ---------------------------------------------------------------------------

TOOL_LIST_HELP = """I can help you with these queries:

1. **Describe a scenario** — "Tell me about B-042"
2. **Compare scenarios** — "Compare B-012 and B-087"
3. **Explain ranking** — "Why did B-042 rank #3?"
4. **Query rainfall** — "What was rainfall at USW00012924 in 2011?"
5. **Check station stress** — "How concurrent is the stress in B-042?"
6. **Sensitivity test** — "What if I doubled the duration weight?"
7. **Evidence summary** — "What evidence supports B-042?"
8. **Describe a profile** — "What defines drought group 3?"
9. **Export readiness** — "Can I export now?"
10. **Data provenance** — "Where does the data come from?"
11. **Find scenarios by year** — "Show me drought events from 2011"
12. **Reservoir stress test** — "Can infrastructure survive a 2011 event if rainfall is 20% lower?"
13. **Multi-tier stress spectrum** — "Run stress spectrum on B-016" or "Test 100%, 80%, 60%, 40% rainfall tiers"
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "describe_scenario",
            "description": "Get complete metrics for a specific drought scenario ID (e.g. B-001, B-016) including duration, deficit, station stress, and provenance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string", "description": "The scenario ID, e.g. 'B-001', 'B-016'"}
                },
                "required": ["scenario_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_scenarios",
            "description": "Compare 2 or 3 candidate drought scenarios side-by-side with pairwise delta calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id_1": {"type": "string", "description": "First scenario ID, e.g. 'B-001'"},
                    "scenario_id_2": {"type": "string", "description": "Second scenario ID, e.g. 'B-009'"},
                    "scenario_id_3": {"type": "string", "description": "Optional third scenario ID"}
                },
                "required": ["scenario_id_1", "scenario_id_2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_ranking",
            "description": "Explain how a scenario's priority score was calculated from scoring weights and normalized features.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string", "description": "The scenario ID to explain, e.g. 'B-001'"}
                },
                "required": ["scenario_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_rainfall",
            "description": "Query observed daily rainfall records for a specific NOAA station over a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_id": {"type": "string", "description": "Station ID such as 'USW00012925' or 'USW00012924'"},
                    "start_date": {"type": "string", "description": "Start date in 'YYYY-MM-DD' format"},
                    "end_date": {"type": "string", "description": "End date in 'YYYY-MM-DD' format"}
                },
                "required": ["station_id", "start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_concurrence",
            "description": "Check multi-station drought concurrence to see how many stations experienced simultaneous rolling deficit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string", "description": "The scenario ID to check, e.g. 'B-001'"}
                },
                "required": ["scenario_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_sensitivity",
            "description": "Preview how changes to scoring weights (severity, duration, concurrence, season) would change scenario rankings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "number", "description": "Weight for deficit severity (0-100)"},
                    "duration": {"type": "number", "description": "Weight for event duration (0-100)"},
                    "concurrence": {"type": "number", "description": "Weight for multi-station concurrence (0-100)"},
                    "season": {"type": "number", "description": "Weight for summer timing preference (0-100)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_evidence",
            "description": "Summarize analyst review decisions, evidence, citations, and notes attached to a scenario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string", "description": "The scenario ID, e.g. 'B-001'"}
                },
                "required": ["scenario_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "describe_cluster",
            "description": "Describe an unsupervised drought profile cluster/group (0, 1, 2, or 3) and its centroid characteristics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster_id": {"type": "integer", "description": "Cluster group index (0, 1, 2, or 3)"}
                },
                "required": ["cluster_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_export_readiness",
            "description": "Check whether the scenario package meets all consistency requirements for export.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_provenance",
            "description": "Retrieve full data provenance including NOAA source, time coverage, download timestamp, and cryptographic hash.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_scenarios_by_year",
            "description": "Find candidate drought scenarios that occurred in a specific calendar year (e.g. 2011, 2000, 1996, 2018).",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "The 4-digit calendar year (e.g. 2011, 2000, 1996)"
                    }
                },
                "required": ["year"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "test_reservoir_infrastructure",
            "description": "Run an illustrative reservoir storage drawdown simulation on a drought scenario to test if water supply infrastructure survives under drought conditions, including optional reduced rainfall (e.g. 20% lower).",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id": {
                        "type": "string",
                        "description": "Specific scenario ID (optional, e.g. 'B-016')"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Calendar year of historical drought to test (e.g. 2011 or 2000)"
                    },
                    "rainfall_reduction_pct": {
                        "type": "number",
                        "description": "Percentage reduction in rainfall to stress test (e.g. 20.0 for 20% lower rainfall)"
                    },
                    "initial_storage_pct": {
                        "type": "number",
                        "description": "Initial combined storage as a fraction (e.g. 0.48 for 48%)"
                    },
                    "conservation_pct": {
                        "type": "number",
                        "description": "Mandatory conservation demand reduction percentage"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_stress_spectrum",
            "description": "Run a multi-tier stress spectrum sweep across 4 rainfall retention tiers (100%, 80%, 60%, 40%) simultaneously on a drought scenario to identify critical tipping points and calculate days-to-breach countdowns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id": {
                        "type": "string",
                        "description": "Specific scenario ID (optional, e.g. 'B-016')"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Calendar year of historical drought (default: 2011)"
                    },
                    "initial_storage_pct": {
                        "type": "number",
                        "description": "Initial combined storage as a fraction (default: 0.48 for 48%)"
                    },
                    "conservation_pct": {
                        "type": "number",
                        "description": "Mandatory conservation demand reduction percentage (e.g. 15.0 for 15%)"
                    }
                }
            }
        }
    }
]


def validate_tool_args(workspace, name, args):
    """Reject malformed routing rather than silently selecting different data."""
    if name not in TOOL_REGISTRY:
        raise ValueError("Unsupported read-only tool")
    schema = next(t["function"]["parameters"] for t in TOOL_SCHEMAS
                  if t["function"]["name"] == name)
    schema = {**schema, "additionalProperties": False}
    if list(Draft202012Validator(schema).iter_errors(args)):
        raise ValueError("Invalid or missing tool arguments; specify the requested fields explicitly.")
    for key, value in args.items():
        if isinstance(value, (float, int)) and (isinstance(value, bool) or not math.isfinite(value)):
            raise ValueError("Numeric arguments must be finite numbers.")
        if key.startswith("scenario_id"):
            workspace.get(value)
        if key in {"severity", "duration", "concurrence", "season", "rainfall_reduction_pct"} and not 0 <= value <= 100:
            raise ValueError("Percentage/weight outside 0–100.")
        if key == "initial_storage_pct" and not 0.05 <= value <= 1:
            raise ValueError("Initial storage must be a fraction from 0.05 to 1.")
        if key == "conservation_pct" and not (value == 0 or 1 < value <= 50):
            raise ValueError("Conservation must be explicit percentage points greater than 1 up to 50, or zero; fractional inputs are ambiguous.")
        if key == "year" and not 1991 <= value <= 2025:
            raise ValueError("Year is outside the bundled observation period.")
    if name in {"test_reservoir_infrastructure", "run_stress_spectrum"}:
        if not args.get("scenario_id"):
            raise ValueError("Specify an exact scenario_id for this illustrative experiment.")
        if "year" in args and not workspace.get(args["scenario_id"]).provenance["source_start"].startswith(str(args["year"])):
            raise ValueError("Scenario and requested year disagree.")
    return dict(args)


def semantic_query_route(workspace, prompt: str) -> str:
    """Deterministic Semantic Entity & Synonym Graph intent router.

    Parses natural language queries, extracts scenario IDs, station codes,
    years, and parameter thresholds, executes verified local tools, and renders
    standard templates completely offline with zero LLM dependency.
    """
    from basin_core.tools import (
        check_concurrence,
        check_export_readiness,
        compare_scenarios,
        describe_cluster,
        describe_scenario,
        explain_ranking,
        find_scenarios_by_year,
        get_data_provenance,
        query_rainfall,
        run_sensitivity,
        run_stress_spectrum,
        summarize_evidence,
        test_reservoir_infrastructure,
    )

    p = prompt.lower().strip()

    # Adversarial & Non-Predictive Advisory Guardrails
    if any(q in p for q in [
        "when will water run out", "when will the reservoir run out",
        "will water run out", "exact date of breach", "forecast reservoir levels",
        "what date will", "what date will choke canyon", "when do we run out"
    ]):
        return (
            "⚠️ **Analysis Boundary (Non-Predictive Advisory)**: BASIN does not generate calendar-date forecasts "
            "or operational water-supply predictions. The bundled reservoir experiment is an illustrative, "
            "uncalibrated mass-balance sensitivity model using historical rainfall proxies, not a delivery forecast."
        )

    if any(q in p for q in [
        "should council", "should the city", "declare stage", "mandate stage",
        "should we declare", "declare an emergency", "mandate cuts"
    ]):
        return (
            "⚠️ **Analysis Boundary (Policy Governance)**: BASIN is an analytical rainfall scenario workbench, "
            "not a regulatory decision authority. Official drought stages are declared exclusively by municipal and regional "
            "authorities pursuant to the City of Corpus Christi Drought Contingency Plan."
        )

    # 1. Extract Scenario IDs
    id_matches = re.findall(r"\b[bB]-\d+\b", prompt)
    for s in getattr(workspace, "scenarios", []):
        if s.id.lower() in p and s.id not in id_matches:
            id_matches.append(s.id)

    default_id = id_matches[0] if id_matches else (
        workspace.selected[0] if getattr(workspace, "selected", None) else (
            workspace.scenarios[0].id if getattr(workspace, "scenarios", None) else "B-001"
        )
    )

    # 2. Extract Year
    year_match = re.search(r"\b(19\d\d|20\d\d)\b", p)
    year = int(year_match.group(1)) if year_match else None

    # 3. Extract Percentages
    conservation_pct = 0.0
    cons_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:conservation|mandate|cut|demand)", p)
    if cons_match:
        conservation_pct = float(cons_match.group(1))
    elif any(k in p for k in ["conservation", "mandate", "cut"]):
        gen_pct = re.search(r"(\d+(?:\.\d+)?)\s*%", p)
        if gen_pct:
            conservation_pct = float(gen_pct.group(1))

    rainfall_reduction_pct = 0.0
    red_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:lower|less|reduction|drier|dry|deficit)", p)
    if red_match:
        rainfall_reduction_pct = float(red_match.group(1))

    initial_storage_pct = 0.48
    store_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:initial|starting|storage|capacity|pool)", p)
    if store_match:
        val = float(store_match.group(1))
        initial_storage_pct = val / 100.0 if val > 1.0 else val

    # 4. Extract Station
    station_id = None
    if any(k in p for k in ["corpus", "crp", "12924"]):
        station_id = "USW00012924"
    elif any(k in p for k in ["victoria", "vct", "12912"]):
        station_id = "USW00012912"
    elif any(k in p for k in ["san antonio", "sat", "12921"]):
        station_id = "USW00012921"
    else:
        stations = getattr(workspace, "source", None)
        manifest_stations = workspace.source.manifest.get("stations", []) if (stations and hasattr(workspace.source, "manifest")) else []
        for stn in manifest_stations:
            if stn.get("id", "").lower() in p or stn.get("name", "").lower() in p:
                station_id = stn["id"]
                break
        if not station_id and manifest_stations:
            station_id = manifest_stations[0]["id"]
        elif not station_id:
            station_id = "USW00012924"

    # 5. Extract Dates for rainfall queries
    date_matches = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", p)
    if len(date_matches) >= 2:
        start_date, end_date = date_matches[0], date_matches[1]
    elif len(date_matches) == 1:
        start_date = date_matches[0]
        end_date = f"{int(start_date[:4])}-12-31"
    elif year is not None:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    else:
        start_date = "2011-01-01"
        end_date = "2011-12-31"

    try:
        # Route 1: Multi-tier stress spectrum sweep
        if any(k in p for k in ["spectrum", "stress spectrum", "multi-tier", "tiers", "tipping point", "sweep", "countdown", "days to breach", "days-to-breach"]):
            res = run_stress_spectrum(
                workspace,
                scenario_id=default_id if id_matches else "",
                year=year if year is not None else 2011,
                initial_storage_pct=initial_storage_pct,
                conservation_pct=conservation_pct,
            )
            return render_tool_result("run_stress_spectrum", res)

        # Route 2: Reservoir infrastructure survival check
        if any(k in p for k in ["survive", "survival", "infrastructure", "reservoir", "drawdown", "capacity", "storage", "restriction", "lake corpus christi", "choke canyon"]):
            res = test_reservoir_infrastructure(
                workspace,
                scenario_id=default_id if id_matches else "",
                year=year if year is not None else 2011,
                rainfall_reduction_pct=rainfall_reduction_pct,
                initial_storage_pct=initial_storage_pct,
                conservation_pct=conservation_pct,
            )
            return render_tool_result("test_reservoir_infrastructure", res)

        # Route 3: Query station point rainfall
        if (
            any(k in p for k in ["rainfall at", "rain at", "daily rainfall", "observations for", "observed rain", "precipitation at", "station record", "station query", "weather observations"])
            or ("station" in p and any(k in p for k in ["rain", "precipitation", "observations", "records", "daily", "recorded"]))
            or (any(k in p for k in ["usw000", "12924", "12912", "12921"]) and any(k in p for k in ["rain", "precipitation", "recorded", "observations"]))
        ):
            res = query_rainfall(workspace, station_id=station_id, start_date=start_date, end_date=end_date)
            return render_tool_result("query_rainfall", res)

        # Route 4: Find scenarios by year
        if (year is not None and (not id_matches or any(k in p for k in ["scenarios", "find", "list", "show", "search", "events", "years"]))) or any(k in p for k in ["recent", "modern", "years", "from 20", "from 19"]):
            res = find_scenarios_by_year(workspace, year=year if year is not None else 2011)
            return render_tool_result("find_scenarios_by_year", res)

        # Route 5: Export readiness check
        if any(k in p for k in ["readiness", "export ready", "can i export", "blocker", "export check", "ready to export", "ready for export"]):
            res = check_export_readiness(workspace)
            return render_tool_result("check_export_readiness", res)

        # Route 6: Compare scenarios
        if any(k in p for k in ["compare", "vs", "versus", "difference"]):
            if len(id_matches) >= 2:
                id1, id2 = id_matches[0], id_matches[1]
            elif len(workspace.selected) >= 2:
                id1, id2 = workspace.selected[0], workspace.selected[1]
            else:
                id1 = workspace.scenarios[0].id if workspace.scenarios else "B-001"
                id2 = workspace.scenarios[1].id if len(workspace.scenarios) > 1 else id1
            id3 = id_matches[2] if len(id_matches) >= 3 else ""
            res = compare_scenarios(workspace, id1, id2, id3)
            return render_tool_result("compare_scenarios", res)

        # Route 7: Station stress concurrence
        if any(k in p for k in ["stress", "concurrence", "simultaneous", "station stress", "concurrence in", "concurrent"]):
            res = check_concurrence(workspace, default_id)
            return render_tool_result("check_concurrence", res)

        # Route 8: Run sensitivity test
        if any(k in p for k in ["sensitivity", "what if", "doubled the", "half the weight"]) or ("weight" in p and any(k in p for k in ["change", "impact", "sensitivity", "double", "half", "test", "ranking weights"])):
            dur_val = 25
            if "double" in p and "duration" in p:
                dur_val = 50
            elif "half" in p and "duration" in p:
                dur_val = 12
            res = run_sensitivity(workspace, duration=dur_val)
            return render_tool_result("run_sensitivity", res)

        # Route 9: Explain ranking / score
        if any(k in p for k in ["rank", "score", "why did", "position", "scoring"]):
            res = explain_ranking(workspace, default_id)
            return render_tool_result("explain_ranking", res)

        # Route 10: Summarize evidence / citations / conflicts
        if any(k in p for k in ["evidence", "conflict", "source", "disagreement", "citation", "citations", "notes on", "note", "justification"]):
            res = summarize_evidence(workspace, default_id)
            return render_tool_result("summarize_evidence", res)

        # Route 11: Describe drought cluster / profile
        if any(k in p for k in ["cluster", "profile", "group", "kmeans", "centroid"]):
            cid = 0
            digit_match = re.search(r"group\s*(\d+)|cluster\s*(\d+)", p)
            if digit_match:
                cid = int(digit_match.group(1) or digit_match.group(2))
            res = describe_cluster(workspace, cid)
            return render_tool_result("describe_cluster", res)

        # Route 12: Data provenance & NOAA metadata
        if any(k in p for k in ["provenance", "noaa", "data source", "station", "manifest", "data come from", "where does this data", "snapshot sha", "ghcn"]):
            res = get_data_provenance(workspace)
            return render_tool_result("get_data_provenance", res)

        # Route 13: Describe scenario (default if scenario ID mentioned or general request)
        if any(k in p for k in ["scenario", "tell me about", "deficit", "describe"]) or id_matches:
            res = describe_scenario(workspace, default_id)
            return render_tool_result("describe_scenario", res)

        return (
            "**BASIN Analyst Assistant**\n\n"
            "I am a read-only decision-support tool. I only answer questions using verified, "
            "deterministic workspace calculations, and cannot provide speculative commentary or forecasts.\n\n"
            f"{TOOL_LIST_HELP}"
        )
    except ValueError as err:
        return f"⚠️ **Analysis Boundary**: {err}"
    except Exception as ex:
        return f"⚠️ **Query Processing Error**: {ex}"


def run_assistant(workspace, user_message: str,
                  history: list[dict],
                  use_qwen: bool = True) -> tuple[str, list[dict]]:
    """Answer user questions using real embedded Qwen inference with tool grounding.

    When the bundled Qwen runtime is initialized and ready, natural language queries
    are processed by the local Qwen2.5-3B-Instruct model with structured tool calling
    to verified local hydrologic calculators. If the model is not yet loaded, unavailable,
    or encounters an error, falls back gracefully to the deterministic intent router.
    """
    if not isinstance(user_message, str) or len(user_message) > 20000:
        raise ValueError("Question must contain at most 20,000 characters.")
    if not user_message.strip():
        raise ValueError("Enter a question about the workspace.")

    reply: str | None = None

    if use_qwen:
        try:
            from basin_core.qwen_runtime import get_qwen_client
            client = get_qwen_client()
            if client.status == "ready":
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are the BASIN Hydrologist Assistant — an embedded, decision-support specialist "
                            "for municipal water supply planning and drought resilience.\n\n"
                            "CRITICAL OPERATIONAL RULES:\n"
                            "1. Base all numerical claims, drought severity, durations, and storage metrics on verified tool results.\n"
                            "2. When asked about a scenario, comparison, station rainfall, ranking, reservoir stress test, or drought concurrence, call the appropriate tool.\n"
                            "3. Explain hydrologic principles clearly, professionally, and concisely.\n"
                            "4. Never invent numbers or hallucinate metrics."
                        ),
                    }
                ]
                for m in history[-6:]:
                    if isinstance(m, dict) and m.get("role") in {"user", "assistant"} and isinstance(m.get("content"), str):
                        messages.append({"role": m["role"], "content": m["content"][:4000]})

                messages.append({"role": "user", "content": user_message})

                resp = client.generate(messages, tools=TOOL_SCHEMAS, temperature=0.1, max_tokens=512)
                tool_calls = resp.get("tool_calls")
                raw_content = resp.get("content") or ""

                if tool_calls:
                    tool_results_md = []
                    for call in tool_calls:
                        fn_name = call.get("function", {}).get("name")
                        raw_args = call.get("function", {}).get("arguments", {})
                        args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                        if fn_name in TOOL_REGISTRY:
                            try:
                                val_args = validate_tool_args(workspace, fn_name, args)
                                res = TOOL_REGISTRY[fn_name](workspace, **val_args)
                                tool_results_md.append(render_tool_result(fn_name, res))
                            except Exception as tool_err:
                                tool_results_md.append(f"⚠️ Tool `{fn_name}` notice: {tool_err}")

                    clean_text = re.sub(r"<tool_call>.*?</tool_call>", "", raw_content, flags=re.DOTALL).strip()
                    if tool_results_md:
                        joined_tools = "\n\n".join(tool_results_md)
                        if clean_text:
                            reply = f"{clean_text}\n\n{joined_tools}"
                        else:
                            reply = joined_tools
                    elif clean_text:
                        reply = clean_text
                else:
                    clean_text = re.sub(r"<tool_call>.*?</tool_call>", "", raw_content, flags=re.DOTALL).strip()
                    if clean_text:
                        reply = clean_text

        except Exception as ex:
            logger.warning("Qwen inference error, falling back to deterministic router: %s", ex)

    if reply is None:
        reply = semantic_query_route(workspace, user_message)

    previous = [
        {"role": m["role"], "content": m["content"][:20000]}
        for m in history[-10:]
        if isinstance(m, dict) and m.get("role") in {"user", "assistant"}
        and isinstance(m.get("content"), str)
    ]
    updated = previous + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]
    return reply, updated


def run_tool_directly(workspace, tool_name: str,
                      args: dict) -> str:
    """Execute a validated read-only tool selected directly by the user."""
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    args = validate_tool_args(workspace, tool_name, args)
    result = TOOL_REGISTRY[tool_name](workspace, **args)
    return render_tool_result(tool_name, result)
