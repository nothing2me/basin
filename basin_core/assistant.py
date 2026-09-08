"""BASIN analyst assistant — grounded local LLM with tool calling.

The LLM (via Ollama) acts as an intent router: it selects tools and extracts
parameters.  Tools compute answers from real workspace data.  Templates render
results with fixed disclaimers.  The LLM adds brief connective prose but never
generates numbers or scientific claims.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from basin_core.tools import TOOL_FUNCTIONS, TOOL_REGISTRY

try:
    import ollama as _ollama
    _OLLAMA_AVAILABLE = True
except ImportError:
    _ollama = None  # type: ignore[assignment]
    _OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

PREFERRED_MODELS = ["qwen2.5:3b", "llama3.2:3b", "qwen2.5:7b", "llama3.1:8b", "mistral:7b"]
_OLLAMA_CACHE: dict[str, Any] = {}


def check_ollama(force_refresh: bool = False) -> dict:
    """Return availability status and installed models (cached for 30s for instant UI response)."""
    import time
    now = time.time()
    if not force_refresh and "data" in _OLLAMA_CACHE and (now - _OLLAMA_CACHE.get("timestamp", 0) < 30.0):
        return _OLLAMA_CACHE["data"]

    if not _OLLAMA_AVAILABLE:
        res = {"available": False, "reason": "ollama package not installed",
               "models": [], "selected": None}
        _OLLAMA_CACHE["data"] = res
        _OLLAMA_CACHE["timestamp"] = now
        return res
    try:
        response = _ollama.list()
        installed = [m.model for m in response.models] if response.models else []
        selected = None
        for preferred in PREFERRED_MODELS:
            for installed_name in installed:
                if installed_name.startswith(preferred.split(":")[0]):
                    selected = installed_name
                    break
            if selected:
                break
        res = {"available": True, "models": installed,
               "selected": selected or (installed[0] if installed else None)}
    except Exception as exc:
        res = {"available": False, "reason": str(exc),
               "models": [], "selected": None}
    _OLLAMA_CACHE["data"] = res
    _OLLAMA_CACHE["timestamp"] = now
    return res


def get_model() -> str:
    """Return the best available model name."""
    status = check_ollama()
    if status["selected"]:
        return status["selected"]
    raise RuntimeError("No Ollama model available. Install Ollama and pull a "
                       "model: ollama pull qwen2.5:7b")


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are BASIN's analyst assistant, helping hydrologists explore rainfall scenario data for the Coastal Bend region of Texas.

STRICT RULES — violations produce wrong answers:
1. ALWAYS call one or more tools before answering factual questions. Never generate rainfall values, percentiles, scores, dates, or statistics from your own knowledge.
2. If no tool covers the question, respond: "I don't have a tool for that. Here's what I can help with:" and list the available tools.
3. NEVER claim a scenario is "safe", "dangerous", "likely", or "unlikely". BASIN does not forecast.
4. NEVER modify, round differently, or reinterpret numbers returned by tools.
5. Refer to the three airport stations as "provisional regional proxies" — their catchment suitability is unvalidated.
6. The reservoir simulation is illustrative and excluded from evidence packets. Do not present its outputs as forecasts.
7. Keep responses concise. Hydrologists value precision over length.
8. You may add brief contextual observations between tool outputs, such as suggesting a next step or noting a relationship. Keep these to 1-2 sentences.
9. If the user asks you to modify, accept, reject, or export anything, explain that you are read-only and direct them to the appropriate BASIN page.
10. When presenting tool results, preserve all disclaimers and source citations exactly as provided.

AVAILABLE CONTEXT:
- Data source: NOAA NCEI GHCN-Daily bundled snapshot (1991-2025)
- Stations: Corpus Christi, Victoria, San Antonio airport observations
- Method: Synchronized historical window resampling with rainfall retention scaling
- AI components: KMeans clustering for drought profile grouping, weighted priority scoring
- All computations are local and deterministic
"""

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


def run_assistant(workspace, user_message: str,
                  history: list[dict]) -> tuple[str, list[dict]]:
    """Execute the LLM → tool → template → response loop.

    Returns (response_text, updated_history).
    """
    model = get_model()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # Step 1: LLM selects tools
    response = _ollama.chat(
        model=model,
        messages=messages,
        tools=TOOL_SCHEMAS,
    )

    # Step 2: No tool calls — direct response (abstention or clarification)
    if not response.message.tool_calls:
        reply = response.message.content or "I'm not sure how to help with that."
        updated = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply},
        ]
        return reply, updated

    # Step 3: Execute each tool call and render the template
    tool_messages = []
    rendered_parts = []
    for call in response.message.tool_calls:
        fn_name = call.function.name
        fn_args = dict(call.function.arguments or {})

        if fn_name not in TOOL_REGISTRY:
            error_msg = f"Unknown tool: {fn_name}. {TOOL_LIST_HELP}"
            rendered_parts.append(error_msg)
            tool_messages.append({"role": "tool", "content": error_msg})
            continue

        # Fill sensible defaults if the model missed required arguments
        sid_default = workspace.selected[0] if workspace.selected else (workspace.scenarios[0].id if workspace.scenarios else "B-001")
        if fn_name in ("describe_scenario", "explain_ranking", "check_concurrence", "summarize_evidence"):
            if not fn_args.get("scenario_id"):
                fn_args["scenario_id"] = sid_default
        elif fn_name == "compare_scenarios":
            if not fn_args.get("scenario_id_1"):
                fn_args["scenario_id_1"] = sid_default
            if not fn_args.get("scenario_id_2"):
                fn_args["scenario_id_2"] = workspace.selected[1] if len(workspace.selected) > 1 else (workspace.scenarios[1].id if len(workspace.scenarios) > 1 else sid_default)
        elif fn_name == "describe_cluster":
            if "cluster_id" not in fn_args:
                fn_args["cluster_id"] = 0
            else:
                try:
                    fn_args["cluster_id"] = int(fn_args["cluster_id"])
                except Exception:
                    fn_args["cluster_id"] = 0
        elif fn_name == "find_scenarios_by_year":
            if "year" not in fn_args:
                fn_args["year"] = 2011
            else:
                try:
                    fn_args["year"] = int(fn_args["year"])
                except Exception:
                    fn_args["year"] = 2011
        elif fn_name == "test_reservoir_infrastructure":
            if "year" in fn_args:
                try:
                    fn_args["year"] = int(fn_args["year"])
                except Exception:
                    fn_args["year"] = 2011
            if "rainfall_reduction_pct" in fn_args:
                try:
                    fn_args["rainfall_reduction_pct"] = float(fn_args["rainfall_reduction_pct"])
                except Exception:
                    fn_args["rainfall_reduction_pct"] = 0.0
        elif fn_name == "run_stress_spectrum":
            if "year" in fn_args:
                try:
                    fn_args["year"] = int(fn_args["year"])
                except Exception:
                    fn_args["year"] = 2011
            if "initial_storage_pct" in fn_args:
                try:
                    fn_args["initial_storage_pct"] = float(fn_args["initial_storage_pct"])
                except Exception:
                    fn_args["initial_storage_pct"] = 0.48
            if "conservation_pct" in fn_args:
                try:
                    fn_args["conservation_pct"] = float(fn_args["conservation_pct"])
                except Exception:
                    fn_args["conservation_pct"] = 0.0

        try:
            # Inject workspace as first argument
            result = TOOL_REGISTRY[fn_name](workspace, **fn_args)
            rendered = render_tool_result(fn_name, result)
            rendered_parts.append(rendered)
            tool_messages.append({"role": "tool", "content": rendered})
        except (ValueError, KeyError, TypeError) as exc:
            error_msg = f"Tool error ({fn_name}): {exc}"
            rendered_parts.append(f"⚠️ {error_msg}")
            tool_messages.append({"role": "tool", "content": error_msg})

    # Step 4: Send tool results back for connective prose
    followup_messages = messages + [response.message] + tool_messages
    followup_messages.append({
        "role": "system",
        "content": ("The tool results above contain verified computed data. "
                    "Present them to the user. You may add 1-2 sentences of "
                    "context or suggest a next step, but do NOT modify, "
                    "re-round, or reinterpret any numbers from the tool output. "
                    "Do NOT repeat the tables — reference them briefly."),
    })

    try:
        final = _ollama.chat(model=model, messages=followup_messages)
        commentary = final.message.content or ""
    except Exception:
        commentary = ""

    # Combine: tool output first (ground truth), then brief LLM commentary
    full_response = "\n\n".join(rendered_parts)
    if commentary.strip():
        full_response += "\n\n---\n" + commentary.strip()

    updated = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": full_response},
    ]
    return full_response, updated


def run_tool_directly(workspace, tool_name: str,
                      args: dict) -> str:
    """Execute a single tool without the LLM — for manual/fallback mode."""
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    result = TOOL_REGISTRY[tool_name](workspace, **args)
    return render_tool_result(tool_name, result)
