"""BASIN assistant: optional embedded intent selection with deterministic answers.

Model output is untrusted. Only validated read-only tool results are rendered;
unsupported or unavailable model responses use the deterministic fallback.
"""
from __future__ import annotations

import json
import logging
import math
import re
from typing import Any
from jsonschema import Draft202012Validator

from basin_core.tools import TOOL_FUNCTIONS, TOOL_REGISTRY

try:
    import ollama as _ollama
    _OLLAMA_AVAILABLE = True
except ImportError:
    _ollama = None  # type: ignore[assignment]
    _OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional Ollama client configuration (preserved for dependency/egress audits)
# ---------------------------------------------------------------------------

PREFERRED_MODELS = ["qwen2.5:3b", "llama3.2:3b", "qwen2.5:7b", "llama3.1:8b", "mistral:7b"]
_OLLAMA_CACHE: dict[str, Any] = {}


def local_client():
    """Ignore remote host/proxy configuration; never follow HTTP redirects."""
    if not _OLLAMA_AVAILABLE:
        raise RuntimeError("Ollama is not installed; use direct tools.")
    return _ollama.Client(host="http://127.0.0.1:11434", trust_env=False,
                          follow_redirects=False, timeout=30.0)


def local_model(name):
    """Name screening only; eligibility also requires raw inventory metadata."""
    return (isinstance(name, str) and bool(name.strip()) and name == name.strip()
            and "cloud" not in name.lower())


def eligible_local_model(record):
    """Reject remote/ambiguous entries before typed parsing can discard fields.

    Local GGUF metadata is a daemon assertion, not proof of daemon egress policy.
    Missing remote fields are normal (Ollama omits empty values), but unsupported
    formats and incomplete local-weight metadata do not qualify for chat.
    """
    if not isinstance(record, dict):
        return False
    name = record.get("model")
    if not local_model(name) or record.get("name", name) != name:
        return False
    if any(record.get(key, "") != "" for key in ("remote_host", "remote_model")):
        return False
    details = record.get("details")
    digest = record.get("digest")
    return (isinstance(details, dict) and details.get("format") == "gguf"
            and type(record.get("size")) is int and record["size"] > 0
            and isinstance(digest, str) and re.fullmatch(r"[0-9a-fA-F]{64}", digest) is not None)


def local_model_inventory():
    """Read untyped /api/tags using the pinned client's restricted transport.

    The private raw method is intentional: Client.list() loses remote metadata.
    Real-client regression tests pin this dependency on ollama==0.6.2.
    """
    client = local_client()
    try:
        payload = client._request_raw("GET", "/api/tags").json()
        if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
            raise ValueError("Unrecognized model inventory; local model eligibility is unknown")
        records = payload["models"]
        # Conflicting duplicate entries must not qualify via their benign copy.
        rejected = {r.get("model") for r in records if isinstance(r, dict)
                    and isinstance(r.get("model"), str) and not eligible_local_model(r)}
        return list(dict.fromkeys(r["model"] for r in records
                                  if eligible_local_model(r) and r["model"] not in rejected))
    finally:
        client._client.close()


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
        installed = local_model_inventory()
        selected = None
        for preferred in PREFERRED_MODELS:
            for installed_name in installed:
                if installed_name == preferred:
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


def get_model() -> str | None:
    """Recheck eligibility immediately before sending any user/workspace content."""
    status = check_ollama(force_refresh=True)
    if status["selected"]:
        return status["selected"]
    return None

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

    "test_reservoir_infrastructure": """**Reservoir Infrastructure Stress Test: Scenario {scenario_id} revision {scenario_revision}** ({source_start} to {source_end})
Rainfall input (100%): {input_summary}. {input_meaning}
Rainfall used: **{retention_text}% of that input** ({rainfall_reduction_pct:g}% lower){observed_text} · Duration: **{duration_days} days**

| Storage Metric | Combined Pool | Water Volume |
|---|---|---|
| Initial storage | {initial_pct:g}% | {initial_acft:,.0f} ac-ft |
| Final storage | {final_pct}% | {final_acft:,.0f} ac-ft |
| Lowest point reached | {min_pct}% | {min_acft:,.0f} ac-ft |

**First day at or below each assumed storage band:**
- 40% band: {band1_text}
- 30% band: {band2_text}
- 20% band: {band3_text}
- 15% band: {band4_text}

**Result for this window:**
{assessment_text}

> Source: BASIN reservoir experiment `{simulation_id}` · Snapshot `{_snapshot}…`
> ⚠️ Illustrative two-pool simulation (Lake Corpus Christi + Choke Canyon). Bands are experiment assumptions, not adopted restriction stages. Not an official forecast or regulatory restriction date.""",

    "run_stress_spectrum": """**Reservoir Stress Spectrum: Scenario {scenario_id} revision {scenario_revision}** ({source_start} to {source_end})
Duration: **{duration_days} days** · Initial storage: **{initial_pct:g}%** · Conservation: **{conservation_pct:g}%**
Rainfall input (100% tier): {input_summary}. {input_meaning} Each tier multiplies that input.

| Rainfall tier | ≈ % of observed | Lowest storage | 40% band | 30% band | 20% band | 15% band | 20% band in window |
|---|---|---|---|---|---|---|---|
{spectrum_table}

**Evaluated tier outcomes:**
{tipping_point_text}

> Source: BASIN multi-tier stress spectrum `{simulation_id}` · Snapshot `{_snapshot}…`
> ⚠️ Illustrative two-pool simulation across rainfall multipliers. Band days are the first day at or below each assumed band; day 0 means at or below at the start. Not an official regulatory declaration.""",
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
        years = ", ".join(str(y) for y in data.get("available_start_years", [])) or "none"
        table = (f"No scenarios in the current candidate pool have a source window starting in {data['year']}. "
                 f"No other year was substituted. Start years present: {years}."
                 + (f" The bundled record covers {data['record_period']}." if data.get("record_period") else ""))
    data = dict(data)
    data["scenario_table"] = table
    return TEMPLATES["find_scenarios_by_year"].format_map(data)


def _input_rainfall_text(data: dict) -> tuple[str, str]:
    """What the 100% rainfall input was, stated by every reservoir answer."""
    info = data.get("input_rainfall") or {}
    return (info.get("summary", "not recorded for this result"),
            info.get("hundred_percent_meaning", "The meaning of 100% was not recorded for this result."))


def _render_test_reservoir_infrastructure(data: dict) -> str:
    from basin_core.analysis import threshold_day_label
    data = dict(data)
    data["input_summary"], data["input_meaning"] = _input_rainfall_text(data)
    observed = data.get("observed_pct")
    data["observed_text"] = (f" ≈ {observed:g}% of observed rainfall" if observed is not None
                             else " · not a single multiple of the observations")
    data["retention_text"] = f"{data.get('retention_pct', 100 - data['rainfall_reduction_pct']):g}"
    for number, key in ((1, "day_band1_40pct"), (2, "day_band2_30pct"), (3, "day_band3_20pct"), (4, "day_band4_15pct")):
        data[f"band{number}_text"] = threshold_day_label(data[key])
    day_20 = data["day_band3_20pct"]
    if data["survived_critical_20pct"]:
        data["assessment_text"] = (
            f"Combined storage stayed above the assumed 20% band for all {data['duration_days']} days of this window, "
            f"with a lowest value of **{data['min_pct']}%** ({data['min_acft']:,.0f} ac-ft). "
            "This describes these assumed inputs only."
        )
    elif day_20 == 0:
        data["assessment_text"] = (
            f"Combined storage was already at or below the assumed 20% band at the start (day 0); "
            f"its lowest value was **{data['min_pct']}%** ({data['min_acft']:,.0f} ac-ft)."
        )
    else:
        data["assessment_text"] = (
            f"Combined storage reached the assumed 20% band on **day {day_20}** and fell to "
            f"**{data['min_pct']}%** ({data['min_acft']:,.0f} ac-ft)."
        )
    return TEMPLATES["test_reservoir_infrastructure"].format_map(data)


def _render_run_stress_spectrum(data: dict) -> str:
    from basin_core.analysis import threshold_day_label
    from basin_core.simulation import observed_percent
    data = dict(data)
    data["input_summary"], data["input_meaning"] = _input_rainfall_text(data)
    info = data.get("input_rainfall") or {}
    table = data.get("summary_table", [])
    rows = []
    for r in table:
        observed = observed_percent(r["tier_multiplier"], info) if info else None
        observed_text = f"{observed:g}%" if observed is not None else "n/a"
        days = " | ".join(threshold_day_label(r[key]) for key in
                          ("day_stage1_40", "day_stage2_30", "day_stage3_20", "day_emergency_15"))
        rows.append(f"| {r['tier_label']} | {observed_text} | {r['min_pct']}% ({r['min_acft']:,.0f} ac-ft) | {days} | {r['status']} |")
    data["spectrum_table"] = "\n".join(rows)

    stayed = [r for r in table if r["survived_critical_20pct"]]
    reached = [r for r in table if not r["survived_critical_20pct"]]
    if not table:
        data["tipping_point_text"] = "No rainfall tiers were computed."
    elif stayed and reached:
        lowest_stayed = min(stayed, key=lambda r: r["retention_pct"])
        highest_reached = max(reached, key=lambda r: r["retention_pct"])
        data["tipping_point_text"] = (
            f"Storage stayed above the assumed 20% band down to **{lowest_stayed['retention_pct']:g}% of input rainfall** "
            f"and reached it at **{highest_reached['retention_pct']:g}%** ({threshold_day_label(highest_reached['day_stage3_20'])}). "
            "Only these tested tiers are compared."
        )
    elif not reached:
        lowest = min(table, key=lambda r: r["retention_pct"])
        data["tipping_point_text"] = (
            f"No tested tier reached the assumed 20% band within this {data['duration_days']}-day window, "
            f"down to {lowest['retention_pct']:g}% of input rainfall."
        )
    else:
        highest = max(reached, key=lambda r: r["retention_pct"])
        data["tipping_point_text"] = (
            f"Every tested tier reached the assumed 20% band within this window; the {highest['retention_pct']:g}% tier "
            f"(the highest tested) did so at {threshold_day_label(highest['day_stage3_20'])}."
        )

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
            "description": "Describe one unsupervised drought profile group, by the group number shown in the app (groups are numbered from 1), and its centroid characteristics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cluster_id": {"type": "integer", "description": "Group number as shown in the app, starting at 1"}
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
            "description": "Find candidate drought scenarios whose historical source window starts in a specific calendar year (e.g. 2011, 2000, 1996, 2018).",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "The 4-digit source start year requested by the user; never assume one"
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
                        "description": "Exact scenario ID named by the user, e.g. 'B-016'"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Optional check that the scenario's source window starts in this year"
                    },
                    "rainfall_reduction_pct": {
                        "type": "number",
                        "description": "Rainfall reduction relative to the selected scenario revision, in percentage points (e.g. 20 for 20% lower)"
                    },
                    "initial_storage_pct": {
                        "type": "number",
                        "description": "Initial combined storage in percentage points (e.g. 48 for 48%); never a fraction"
                    },
                    "conservation_pct": {
                        "type": "number",
                        "description": "Demand reduction in percentage points (e.g. 15 for 15%)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_stress_spectrum",
            "description": "Run an illustrative storage sweep at 100%, 80%, 60% and 40% of the selected scenario revision's rainfall and report the first day each assumed storage band is reached.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_id": {
                        "type": "string",
                        "description": "Exact scenario ID named by the user, e.g. 'B-016'"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Optional check that the scenario's source window starts in this year"
                    },
                    "initial_storage_pct": {
                        "type": "number",
                        "description": "Initial combined storage in percentage points (e.g. 48 for 48%); never a fraction"
                    },
                    "conservation_pct": {
                        "type": "number",
                        "description": "Demand reduction in percentage points (e.g. 15 for 15%)"
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
    manifest = getattr(getattr(workspace, "source", None), "manifest", None) or {}
    first_year, last_year = int(str(manifest.get("start", "1991"))[:4]), int(str(manifest.get("end", "2025"))[:4])
    for key, value in args.items():
        if isinstance(value, (float, int)) and (isinstance(value, bool) or not math.isfinite(value)):
            raise ValueError("Numeric arguments must be finite numbers.")
        if key.startswith("scenario_id"):
            workspace.get(value)
        if key in {"severity", "duration", "concurrence", "season", "rainfall_reduction_pct"} and not 0 <= value <= 100:
            raise ValueError("Percentage/weight outside 0–100.")
        # Tools read every storage and conservation value as percentage points. A value
        # from 0 to 1 could be a fraction (0.48 meaning 48%), so it is refused, not guessed.
        if key == "initial_storage_pct" and not (value == 0 or 1 < value <= 100):
            raise ValueError("Initial storage must be percentage points greater than 1 up to 100, or zero; fractional inputs such as 0.48 are ambiguous.")
        if key == "conservation_pct" and not (value == 0 or 1 < value <= 50):
            raise ValueError("Conservation must be explicit percentage points greater than 1 up to 50, or zero; fractional inputs are ambiguous.")
        if key == "year" and not first_year <= value <= last_year:
            raise ValueError(f"Year is outside the bundled observation period ({first_year}–{last_year}).")
    if name in {"test_reservoir_infrastructure", "run_stress_spectrum"}:
        if not args.get("scenario_id"):
            raise ValueError("Specify an exact scenario_id for this illustrative experiment.")
        if "year" in args and int(workspace.get(args["scenario_id"]).provenance["source_start"][:4]) != args["year"]:
            raise ValueError("Scenario and requested year disagree.")
    return dict(args)


_DEFAULT_TIER_PERCENTS = {100.0, 80.0, 60.0, 40.0}


def parse_experiment_arguments(prompt: str, spectrum_request: bool) -> dict:
    """Read explicitly labelled experiment settings from a question.

    Every percentage must say what it is. An unlabelled or repeated value raises
    ValueError so the caller asks for clarification instead of guessing its meaning.
    Listing the standard 100/80/60/40% tiers in a spectrum request is not a setting.
    """
    p = prompt.lower()
    arguments: dict[str, Any] = {}
    unlabelled: list[float] = []
    for match in re.finditer(r"[+-]?\d+(?:\.\d+)?\s*%", p):
        after = p[match.end():match.end() + 24].strip()
        before = p[max(0, match.start() - 28):match.start()].strip()
        value = float(match.group().replace("%", "").strip())
        if re.match(r"(?:conservation|mandate|cut|demand reduction)", after) or re.search(r"(?:conservation|demand reduction)(?: of| at| to)?$", before):
            key = "conservation_pct"
        elif re.match(r"(?:(?:initial|starting) )?storage", after) or re.search(r"(?:initial|starting) storage(?: of| at| to)?$", before):
            key = "initial_storage_pct"
        elif not spectrum_request and re.match(r"(?:lower|less|reduction|drier)", after):
            key = "rainfall_reduction_pct"
        else:
            unlabelled.append(value)
            continue
        if key in arguments:
            raise ValueError("Multiple values supplied for " + key + "; choose one")
        arguments[key] = value
    if unlabelled and not (spectrum_request and "tier" in p and set(unlabelled) <= _DEFAULT_TIER_PERCENTS):
        raise ValueError("Label each percentage explicitly: initial storage, conservation, or lower rainfall. Use the simulation form for custom tiers.")
    if "observed window" in p or "original observations" in p:
        arguments["baseline_kind"] = "observed_window"
    if "no pipeline" in p or "pipeline unavailable" in p:
        arguments["pipeline_active"] = False
    return arguments


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

    # 1. Scenario IDs named in the question. Scenario-specific answers require one; the
    # first shortlisted or generated scenario is never substituted for a missing ID.
    id_matches: list[str] = []
    for found in re.findall(r"\b[bB]-\d+\b", prompt):
        if found.upper() not in id_matches:
            id_matches.append(found.upper())
    for s in getattr(workspace, "scenarios", []):
        if s.id.lower() in p and s.id not in id_matches:
            id_matches.append(s.id)
    shortlist_text = ", ".join(list(getattr(workspace, "selected", []))[:8]) or "none"

    def clarify(message: str) -> str:
        return f"⚠️ **Please clarify**: {message}"

    def need_ids(count: int, action: str) -> str:
        wanted = "a scenario ID" if count == 1 else f"{count} scenario IDs"
        return clarify(f"name {wanted} to {action}. Current shortlist: {shortlist_text}.")

    # 2. Year, only when written
    year_match = re.search(r"\b(19\d\d|20\d\d)\b", p)
    year = int(year_match.group(1)) if year_match else None

    # 3. Station, only when named
    manifest = getattr(getattr(workspace, "source", None), "manifest", None) or {}
    manifest_stations = manifest.get("stations", [])
    known_stations = [stn["id"] for stn in manifest_stations]
    station_id = next((stn["id"] for stn in manifest_stations
                       if stn.get("id", "").lower() in p or (stn.get("name") and stn["name"].lower() in p)), None)
    if station_id is None:
        for candidate, pattern in (("USW00012924", r"\bcorpus\b|\bcrp\b|12924"),
                                   ("USW00012912", r"\bvictoria\b|\bvct\b|12912"),
                                   ("USW00012921", r"\bsan antonio\b|\bsat\b|12921")):
            if candidate in known_stations and re.search(pattern, p):
                station_id = candidate
                break

    # 4. Dates, only when written
    date_matches = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", p)

    try:
        spectrum_request = any(k in p for k in ["spectrum", "stress spectrum", "multi-tier", "tiers", "tipping point", "sweep", "countdown", "days to breach", "days-to-breach"])
        reservoir_request = any(k in p for k in ["survive", "survival", "infrastructure", "reservoir", "drawdown", "capacity", "storage", "restriction", "lake corpus christi", "choke canyon"])

        # Routes 1-2: illustrative storage experiments with explicitly labelled settings
        if spectrum_request or reservoir_request:
            if len(id_matches) > 1:
                return clarify("name one scenario ID for this experiment; several were given: " + ", ".join(id_matches) + ".")
            arguments = parse_experiment_arguments(p, spectrum_request)
            arguments.update(scenario_id=id_matches[0] if id_matches else "", year=year)
            if spectrum_request:
                return render_tool_result("run_stress_spectrum", run_stress_spectrum(workspace, **arguments))
            return render_tool_result("test_reservoir_infrastructure", test_reservoir_infrastructure(workspace, **arguments))

        # Route 3: Query station point rainfall
        if (
            any(k in p for k in ["rainfall at", "rain at", "daily rainfall", "observations for", "observed rain", "precipitation at", "station record", "station query", "weather observations"])
            or ("station" in p and any(k in p for k in ["rain", "precipitation", "observations", "records", "daily", "recorded"]))
            or (any(k in p for k in ["usw000", "12924", "12912", "12921"]) and any(k in p for k in ["rain", "precipitation", "recorded", "observations"]))
        ):
            if station_id is None:
                return clarify("name a station (" + ", ".join(known_stations) + ") and a date range or year.")
            if len(date_matches) >= 2:
                start_date, end_date = date_matches[0], date_matches[1]
            elif len(date_matches) == 1:
                start_date = end_date = date_matches[0]
            elif year is not None:
                start_date, end_date = f"{year}-01-01", f"{year}-12-31"
            else:
                return clarify(f"give a date range (YYYY-MM-DD to YYYY-MM-DD) or a year for {station_id}; no period is assumed.")
            res = query_rainfall(workspace, station_id=station_id, start_date=start_date, end_date=end_date)
            return render_tool_result("query_rainfall", res)

        # Route 4: Find scenarios by year
        year_words = any(k in p for k in ["recent", "modern", "years", "from 20", "from 19"])
        if (year is not None and (not id_matches or any(k in p for k in ["scenarios", "find", "list", "show", "search", "events", "years"]))) or year_words:
            if year is None:
                years = sorted({s.provenance["source_start"][:4] for s in workspace.scenarios})
                return clarify("give a four-digit source start year; none is assumed. Start years in this workspace: " + ", ".join(years) + ".")
            res = find_scenarios_by_year(workspace, year=year)
            return render_tool_result("find_scenarios_by_year", res)

        # Route 5: Export readiness check
        if any(k in p for k in ["readiness", "export ready", "can i export", "blocker", "export check", "ready to export", "ready for export"]):
            res = check_export_readiness(workspace)
            return render_tool_result("check_export_readiness", res)

        # Route 6: Compare scenarios
        if any(k in p for k in ["compare", "versus", "difference"]) or re.search(r"\bvs\b", p):
            if len(id_matches) < 2:
                return need_ids(2, "compare")
            res = compare_scenarios(workspace, id_matches[0], id_matches[1], id_matches[2] if len(id_matches) >= 3 else "")
            return render_tool_result("compare_scenarios", res)

        # Route 7: Station stress concurrence
        if any(k in p for k in ["stress", "concurrence", "simultaneous", "station stress", "concurrence in", "concurrent"]):
            if not id_matches:
                return need_ids(1, "analyse station stress")
            res = check_concurrence(workspace, id_matches[0])
            return render_tool_result("check_concurrence", res)

        # Route 8: Run sensitivity test with explicitly requested weights
        if any(k in p for k in ["sensitivity", "what if", "doubled the", "half the weight"]) or ("weight" in p and any(k in p for k in ["change", "impact", "sensitivity", "double", "half", "test", "ranking weights"])):
            changes: dict[str, float] = {}
            for weight_name in ("severity", "duration", "concurrence", "season"):
                explicit = re.search(rf"\b{weight_name}\b(?:\s+weight)?\s*(?:to|=|of|at|is|was)\s*(\d+(?:\.\d+)?)\b", p)
                if explicit:
                    changes[weight_name] = float(explicit.group(1))
                elif re.search(rf"\b{weight_name}\b", p) and re.search(r"\bdoubl", p):
                    changes[weight_name] = workspace.weights[weight_name] * 2
                elif re.search(rf"\b{weight_name}\b", p) and re.search(r"\bhal(?:f|ve)", p):
                    changes[weight_name] = workspace.weights[weight_name] / 2
            if not changes:
                return clarify("say which weight to change and to what value, for example 'what if the duration weight is 40?'. "
                               "Current weights: " + ", ".join(f"{k} {v:g}" for k, v in workspace.weights.items()) + ".")
            res = run_sensitivity(workspace, **changes)
            return render_tool_result("run_sensitivity", res)

        # Route 9: Explain ranking / score
        if any(k in p for k in ["rank", "score", "why did", "position", "scoring"]):
            if not id_matches:
                return need_ids(1, "explain its ranking")
            res = explain_ranking(workspace, id_matches[0])
            return render_tool_result("explain_ranking", res)

        # Route 10: Summarize evidence / citations / conflicts. "source" alone is provenance.
        if any(k in p for k in ["evidence", "conflict", "disagreement", "citation", "citations", "notes on", "note", "justification"]) or ("source" in p and id_matches):
            if not id_matches:
                return need_ids(1, "summarise its evidence")
            res = summarize_evidence(workspace, id_matches[0])
            return render_tool_result("summarize_evidence", res)

        # Route 11: Describe drought cluster / profile, only for a named group number
        group_match = re.search(r"(?:group|cluster)\s*(\d+)", p)
        if group_match or (not id_matches and any(k in p for k in ["cluster", "profile", "group", "kmeans", "centroid"])):
            if not group_match:
                groups = sorted({s.cluster for s in workspace.scenarios})
                return clarify("name a drought profile group number. Groups in this workspace: " + ", ".join(str(g) for g in groups) + ".")
            res = describe_cluster(workspace, int(group_match.group(1)))
            return render_tool_result("describe_cluster", res)

        # Route 12: Data provenance & NOAA metadata
        if any(k in p for k in ["provenance", "noaa", "data source", "station", "manifest", "data come from", "where does this data", "snapshot sha", "ghcn"]):
            res = get_data_provenance(workspace)
            return render_tool_result("get_data_provenance", res)

        # Route 13: Describe scenario
        if any(k in p for k in ["scenario", "tell me about", "deficit", "describe", "profile"]) or id_matches:
            if not id_matches:
                return need_ids(1, "describe")
            res = describe_scenario(workspace, id_matches[0])
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


def select_candidate_tools(query: str, max_tools: int = 3) -> list[dict[str, Any]]:
    """Select the most query-relevant tool schemas to keep prompt size small and fast on CPU."""
    q = query.lower()
    matches = []

    keywords = {
        "describe_scenario": ["scenario", "profile", "tell me about", "describe", "b-", "cand"],
        "compare_scenarios": ["compare", "difference", "vs", "versus", "between"],
        "explain_ranking": ["rank", "score", "why is", "position", "leader", "order"],
        "check_concurrence": ["concurrence", "stress", "spatial", "simultaneous", "all stations"],
        "run_sensitivity": ["sensitiv", "weight", "priority"],
        "check_export_readiness": ["export", "ready", "readiness", "package", "deliverable"],
        "describe_cluster": ["cluster", "group", "k-means", "diversity"],
        "query_rainfall": ["rain", "precipitation", "station", "gauge", "history"],
        "calculate_crop_water_deficit": ["crop", "irrigation", "etc", "eto", "evapotranspiration", "agronomic", "agriculture"],
        "calculate_kbdi": ["kbdi", "fire", "burn", "wildfire", "danger"],
    }

    for tool in TOOL_SCHEMAS:
        name = tool["function"]["name"]
        words = keywords.get(name, [])
        score = sum(1 for w in words if w in q)
        if score > 0:
            matches.append((score, tool))

    matches.sort(key=lambda x: x[0], reverse=True)
    selected = [t for _, t in matches[:max_tools]]

    names_present = {t["function"]["name"] for t in selected}
    for default_name in ("describe_scenario", "compare_scenarios", "explain_ranking"):
        if len(selected) >= max_tools:
            break
        if default_name not in names_present:
            found = next((t for t in TOOL_SCHEMAS if t["function"]["name"] == default_name), None)
            if found:
                selected.append(found)
                names_present.add(default_name)

    return selected


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

                candidate_tools = select_candidate_tools(user_message, max_tools=3)
                resp = client.generate(messages, tools=candidate_tools, temperature=0.1, max_tokens=256, timeout=25.0)
                tool_calls = resp.get("tool_calls")
                # Reject the entire batch before executing any work if malformed,
                # cancelled, or over budget. Never display ungrounded model prose.
                if resp.get("cancelled"):
                    raise ValueError("Model generation was cancelled")
                if tool_calls:
                    if not isinstance(tool_calls, list) or len(tool_calls) > 3:
                        raise ValueError("Model tool-call budget exceeded")
                    validated = []
                    for call in tool_calls:
                        if not isinstance(call, dict) or not isinstance(call.get("function"), dict):
                            raise ValueError("Malformed model tool call")
                        function = call["function"]
                        fn_name = function.get("name")
                        if not isinstance(fn_name, str) or fn_name not in TOOL_REGISTRY:
                            raise ValueError("Unknown model tool")
                        raw_args = function.get("arguments", {})
                        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        validated.append((fn_name, validate_tool_args(workspace, fn_name, args)))
                    tool_results_md = []
                    for fn_name, args in validated:
                        res = TOOL_REGISTRY[fn_name](workspace, **args)
                        tool_results_md.append(render_tool_result(fn_name, res))
                    reply = "\n\n".join(tool_results_md)

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
