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
Rainfall used: **{retention_text}% of that input** ({rainfall_reduction_pct:g}% reduction from that input){observed_text} · Duration: **{duration_days} days**

| Storage Metric | Combined Pool | Water Volume |
|---|---|---|
| Initial storage | {initial_pct:g}% | {initial_acft:,.0f} ac-ft |
| Final storage | {final_pct}% | {final_acft:,.0f} ac-ft |
| Lowest point reached | {min_pct}% | {min_acft:,.0f} ac-ft |

**First day at or below each assumed storage band:**
{band_rows}

**Result for this window:**
{assessment_text}

> Source: BASIN reservoir experiment `{simulation_id}` · Snapshot `{_snapshot}…`
> ⚠️ Illustrative simulation of **{water_system_name}**. Bands are experiment assumptions, not adopted restriction stages. Not an official forecast or regulatory restriction date.""",

    "run_stress_spectrum": """**Reservoir Stress Spectrum: Scenario {scenario_id} revision {scenario_revision}** ({source_start} to {source_end})
Duration: **{duration_days} days** · Initial storage: **{initial_pct:g}%** · Conservation: **{conservation_pct:g}%**
Rainfall input (100% tier): {input_summary}. {input_meaning} Each tier multiplies that input.

| Rainfall tier | ≈ % of observed | Lowest storage | {band_headers} | Critical band in window |
|---|---|---|{band_separators}|---|
{spectrum_table}

**Evaluated tier outcomes:**
{tipping_point_text}

> Source: BASIN multi-tier stress spectrum `{simulation_id}` · Snapshot `{_snapshot}…`
> ⚠️ Illustrative simulation of **{water_system_name}** across rainfall multipliers. Band days are the first day at or below each assumed band; day 0 means at or below at the start. Not an official regulatory declaration.""",
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
    data["observed_text"] = (f" ≈ {observed:g}% of observed rainfall ({round(100 - observed, 1):g}% reduction from observed)" if observed is not None
                             else " · not a single multiple of the observations")
    data["retention_text"] = f"{data.get('retention_pct', 100 - data['rainfall_reduction_pct']):g}"
    band_keys = ("day_band1_40pct", "day_band2_30pct", "day_band3_20pct", "day_band4_15pct")
    bands = data.get("stage_bands_pct", [40, 30, 20, 15])
    critical_pct = bands[2] if len(bands) >= 3 else 20
    data.setdefault("water_system_name", "configured water system")
    band_rows = []
    for number, (band, key) in enumerate(zip(bands, band_keys), 1):
        data[f"band{number}_text"] = threshold_day_label(data[key])
        band_rows.append(f"- {band:g}% band: {data[f'band{number}_text']}")
    data["band_rows"] = "\n".join(band_rows)
    day_20 = data["day_band3_20pct"]
    if data["survived_critical_20pct"]:
        data["assessment_text"] = (
            f"Combined storage stayed above the assumed {critical_pct:g}% band for all {data['duration_days']} days of this window, "
            f"with a lowest value of **{data['min_pct']}%** ({data['min_acft']:,.0f} ac-ft). "
            "This describes these assumed inputs only."
        )
    elif day_20 == 0:
        data["assessment_text"] = (
            f"Combined storage was already at or below the assumed {critical_pct:g}% band at the start (day 0); "
            f"its lowest value was **{data['min_pct']}%** ({data['min_acft']:,.0f} ac-ft)."
        )
    else:
        data["assessment_text"] = (
            f"Combined storage reached the assumed {critical_pct:g}% band on **day {day_20}** and fell to "
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
    bands = data.get("stage_bands_pct", [40, 30, 20, 15])
    critical_pct = bands[2] if len(bands) >= 3 else 20
    data.setdefault("water_system_name", "configured water system")
    data["band_headers"] = " | ".join(f"{band:g}% band" for band in bands)
    data["band_separators"] = "|".join("---" for _ in bands)
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
            f"Storage stayed above the assumed {critical_pct:g}% band down to **{lowest_stayed['retention_pct']:g}% of input rainfall** ({lowest_stayed['reduction_pct']:g}% reduction) "
            f"and reached it at **{highest_reached['retention_pct']:g}% of input rainfall** ({highest_reached['reduction_pct']:g}% reduction) ({threshold_day_label(highest_reached['day_stage3_20'])}). "
            "Only these tested tiers are compared."
        )
    elif not reached:
        lowest = min(table, key=lambda r: r["retention_pct"])
        data["tipping_point_text"] = (
            f"No tested tier reached the assumed {critical_pct:g}% band within this {data['duration_days']}-day window, "
            f"down to {lowest['retention_pct']:g}% of input rainfall ({lowest['reduction_pct']:g}% reduction)."
        )
    else:
        highest = max(reached, key=lambda r: r["retention_pct"])
        data["tipping_point_text"] = (
            f"Every tested tier reached the assumed {critical_pct:g}% band within this window; the {highest['retention_pct']:g}% of input rainfall tier ({highest['reduction_pct']:g}% reduction) "
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
                    "pipeline_active": {
                        "type": "boolean",
                        "description": "Whether to assume pipeline supply is available; false means unavailable"
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
                    "pipeline_active": {
                        "type": "boolean",
                        "description": "Whether to assume pipeline supply is available; false means unavailable"
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
        if type(value) in (float, int) and not math.isfinite(value):
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


DOMAIN_TOPICS: dict[str, str] = {
    "concurrence": (
        "**Hydrologic Concept: Multi-Station Concurrence**\n\n"
        "In BASIN, **station stress concurrence** is the share of eligible 30-day windows in which all selected precipitation stations "
        "exceed their own rainfall-stress thresholds together. The threshold is based on each station's historical rolling-deficit comparison.\n\n"
        "### How to use it\n"
        "- **Low concurrence** means the selected gauges seldom cross their thresholds at the same time.\n"
        "- **High concurrence** identifies scenarios with geographically shared rainfall stress and may justify asking a hydrologist to examine runoff, inflow, and storage effects.\n"
        "- **Selection matters**: the result applies only to the gauges and observation period in this run. Review station coverage before using it.\n\n"
        "> Rainfall-gauge concurrence does not establish streamflow, reservoir inflow, water-right curtailment, or system failure."
    ),
    "storage_35pct": (
        "**35% Combined Storage in BASIN**\n\n"
        "BASIN offers **35% of modeled combined capacity** as an illustrative starting value for sensitivity testing. It is not encoded as a regulatory trigger or a prediction of available supply.\n\n"
        "The current City of Corpus Christi drought plan identifies **below 20% combined storage** as the Stage 3 threshold. Other providers may use different adopted plans, contracts, measurements, or response rules, so verify the rule that governs the selected community.\n\n"
        "Use the 35% case to compare otherwise identical assumptions, then report the configured demand, pipeline case, rainfall input, modeled bands, and time window with the result. BASIN does not determine mandatory restrictions or days of supply."
    ),
    "dead_pool": (
        "**Inactive Storage (Dead Pool) and the 75,000 ac-ft Assumption**\n\n"
        "Inactive storage generally means water below a reservoir's lowest usable outlet or intake elevation. The usable amount depends on current infrastructure, elevations, water quality, and operating rules.\n\n"
        "BASIN's **75,000 acre-foot reserve is a configurable experiment assumption** used to test sensitivity. The project has not established that value as the verified physical dead pool of the combined Choke Canyon–Lake Corpus Christi system, and the model does not simulate intake hydraulics, pumps, sediment, or treatment limits.\n\n"
        "For formal work, replace the assumption with reviewed reservoir elevation-storage tables, intake elevations, operating constraints, and an engineer-approved definition of usable storage."
    ),
    "mary_rhodes": (
        "**Mary Rhodes Pipeline Context**\n\n"
        "The Mary Rhodes Pipeline brings external raw water toward Corpus Christi from the Lake Texana and Colorado River systems. The City reported operation in the **72–79 million-gallon-per-day range in March 2025**; that dated figure is context, not a guaranteed delivery rate.\n\n"
        "BASIN's pipeline control compares two configured demand cases. It does not reproduce pipeline hydraulics, pumping availability, permits, contracts, outages, or how every delivered gallon changes withdrawals from each reservoir. Treat the difference between cases as an illustrative sensitivity result to carry into formal modeling."
    ),
    "kmeans_diversity": (
        "**Statistical Methodology: K-Means Diversity vs. Top-Deficit Clones**\n\n"
        "Sorting only by rainfall shortfall can return overlapping windows from the same dry episode; BASIN calls this **the clone problem**. BASIN clusters candidates across severity, duration, station concurrence, summer timing, and dry-spell persistence, then selects a high-scoring representative from each cluster.\n\n"
        "This aims to give reviewers a less repetitive shortlist. Cluster labels describe statistical feature profiles; they are not meteorological drought classes, and the shortlist still requires human review for station suitability and decision relevance."
    ),
    "rural_councils": (
        "**Using BASIN with Rural Councils and Small Utilities**\n\n"
        "Use the shortlist to organize questions before commissioning formal analysis:\n"
        "1. **Confirm the service area and supply relationship** recorded in the run.\n"
        "2. **Review station coverage** with the provider or hydrologist and identify missing source-area gauges or streamflow records.\n"
        "3. **Check the provider's current drought plan and wholesale contract** for its actual triggers, allocations, notice periods, and responsibilities.\n"
        "4. **Compare a small set of explicit sensitivity cases** for rainfall, demand, initial storage, and pipeline availability; do not treat them as forecasts.\n"
        "5. **Export the audit packet** with assumptions, source periods, limitations, and rejected scenarios so a professional can reproduce and challenge the shortlist.\n\n"
        "> BASIN does not prescribe restrictions, certify infrastructure, or replace the selected provider's adopted plan."
    ),
    "scenarios_vs_forecasts": (
        "**Scientific Boundary: Synthetic Scenarios vs. Predictive Forecasts**\n\n"
        "BASIN is an **exploratory vulnerability workbench**, not a weather forecasting service.\n\n"
        "- **Weather forecasts** estimate future atmospheric conditions from forecast models and observations.\n"
        "- **BASIN scenarios** resample and transform recorded precipitation windows to ask how a chosen rainfall pattern ranks under stated priorities.\n"
        "- **Reservoir experiments** apply visible, simplified assumptions for comparison; they are not calibrated forecasts of storage or restriction dates.\n\n"
        "> Use BASIN to select and document cases that deserve formal hydrologic modeling."
    ),
    "deficit_vs_volume": (
        "**Station Rainfall Shortfall (mm) vs. Reservoir Volume (ac-ft)**\n\n"
        "- **Point rainfall shortfall** measures missing precipitation depth at a gauge relative to the run's comparison baseline.\n"
        "- **Reservoir inflow and storage** are volumes shaped by catchment rainfall, antecedent soil moisture, runoff, stream routing, diversions, evaporation, withdrawals, and operating rules.\n"
        "- A **runoff coefficient** is one part of converting catchment rainfall to runoff, but it is not constant through a drought or storm sequence.\n\n"
        "BASIN does not calibrate that conversion. A station shortfall must not be directly translated into acre-feet or a reservoir-level change without an expert-approved catchment and operations model."
    ),
    "summer_evaporation": (
        "**Summer Timing, Evaporation, and Demand**\n\n"
        "A summer-onset rainfall shortfall may coincide with higher evaporation and water demand, which makes timing useful for scenario screening. BASIN includes a visible seasonality feature in ranking so users can choose how much that timing affects the shortlist.\n\n"
        "The rainfall workflow does not calculate lake evaporation or municipal demand. The optional storage experiment uses configured assumptions and does not prove that one seasonal scenario depletes storage at a particular multiple of another. Quantifying that effect requires current evaporation, demand, inflow, and operating data in a calibrated model."
    ),
    "greetings": (
        "**Hello! I am your BASIN Hydrologist Assistant.**\n\n"
        "I am an embedded decision-support specialist designed to help municipal planners and rural-serving water providers evaluate drought vulnerability.\n\n"
        "### How I can help you:\n"
        "- **Learn how to use BASIN**: Ask `How do I use this tool?` or `Explain Step 2`.\n"
        "- **Understand hydrologic concepts**: Ask `What is concurrence?`, `What is KBDI?`, or `Is this a forecast?`.\n"
        "- **Analyze scenarios**: Ask `Tell me about scenario B-001`, `Compare B-001 and B-002`, or `Explain ranking for B-001`.\n"
        "- **Test reservoir sensitivity**: Ask `Test reservoir at 38% storage with 15% conservation`.\n"
        "- **Check data & export**: Ask `Where does this data come from?` or `Check export readiness`.\n\n"
        "💡 *Tip: If you are new to the workspace, click **'Tour'** in the top navigation bar for an interactive tour, or click any of the quick-action buttons above!*"
    ),
    "workflow_guide": (
        "### 🧭 Welcome to BASIN: How to Explore & Navigate the Platform\n\n"
        "BASIN (**Basin Analysis and Scenario Intelligence Navigator**) is an engineering decision-support tool for water providers and regional authorities to screen drought scenarios, test reservoir storage drawdown, and prepare verified hydrologic handoffs.\n\n"
        "Here are the best ways to get oriented and figure out the application:\n\n"
        "#### 1. 🎓 Take the Interactive Walkthrough Tour\n"
        "- On **Step 1: Data Dashboard**, click the **'Start tutorial'** button in the top banner.\n"
        "- The tutorial will step you through every key element of the interface with live visual anchors (map, metrics, scenario generator, and export gates).\n\n"
        "#### 2. 🧪 Explore with a Prepared Demonstration Run\n"
        "- Want to see immediate results without configuring parameters? On **Step 1: Data Dashboard**:\n"
        "  - Click **'Try an example'** to instantly load 6 diverse drought candidate scenarios (Seed 22).\n"
        "  - Click **'Load 2026 crisis demo'** to explore an illustrative storage stress test from an actual 7.7% reservoir drought context.\n\n"
        "#### 3. 🗺️ The 4-Stage Workflow (Top Navigation Stepper)\n"
        "- **Step 1: Data Dashboard** — Verify 35 years of NOAA index precipitation data (1991–2025), inspect paired station anomaly heatmaps, and set your decision context.\n"
        "- **Step 2: Scenario Builder** — Choose community priority presets (e.g., *Crop stress*, *Chronic drought*), configure drought reduction percentages, and generate candidate profiles.\n"
        "- **Step 3: Review Selections** — Examine shortlisted scenario deficit envelopes, simulate combined reservoir drawdown (Choke Canyon + Lake Corpus Christi), and log your Accept/Reject determinations.\n"
        "- **Step 4: Export** — Build verifiable SHA-256 audit bundles (`.zip`) and printable Executive Technical Briefs (`.pdf`).\n\n"
        "#### 4. 💬 What You Can Ask Me\n"
        "- Ask about specific scenarios: *\"Tell me about B-042\"*\n"
        "- Compare options: *\"Compare B-012 and B-087\"*\n"
        "- Understand concepts: *\"What is station stress concurrence?\"* or *\"Why is 35% storage critical?\"*\n"
        "- Check progress: *\"Can I export yet?\"*"
    ),
    "step_1_guide": (
        "### 📊 Guide to Step 1: Data Dashboard\n\n"
        "The Data Dashboard is where you establish your empirical observation baseline:\n"
        "- **Continuous NOAA Records**: View synchronized daily precipitation spanning 1991–2025 across regional NOAA stations.\n"
        "- **Custom Local Gauges**: In the bottom metadata expander (*Upload Custom Catchment CSV*), upload daily precipitation records for local rain gauges.\n"
        "- **Analysis Focus**: Select your primary decision objective (*Storage Stress*, *Agronomics*, *Regulatory Handoff*, or *Comparison*) to tailor metrics across subsequent steps.\n"
        "- **Saved Runs**: Reopen saved workspace runs or restore from a verified `.zip` bundle.\n\n"
        "👉 *Next step: When your baseline is ready, click **'Step 2: Scenarios'** in the top navigation.*"
    ),
    "step_2_guide": (
        "### 🌧️ Guide to Step 2: Scenarios & Shortlist Generation\n\n"
        "Step 2 generates and shortlists drought candidates based on your priorities:\n"
        "- **Community Priority Presets & Weights**: Select an operational preset (*Crop stress*, *Reservoir risk*, *Chronic drought*, *Widespread deficit*) or adjust slider weights (Severity, Duration, Concurrence, Seasonality). These rank candidates directly into your shortlist.\n"
        "- **Generation Modes**:\n"
        "  - *Variations of Historical Window*: Scales precipitation downwards within a specific historical interval (e.g. 2024 drought sequence).\n"
        "  - *Multi-Year Historical Search*: Empirically screens multi-season dry periods across distinct years (1991–2025) and onset months.\n"
        "- **Clustering (K-Means)**: Groups candidate sequences by statistical features to deliver a diverse shortlist without duplicate 'clones'.\n\n"
        "👉 *Next step: Click **'Create rainfall scenarios'**, then proceed to **'Step 3: Review'**.*"
    ),
    "step_3_guide": (
        "### 🔍 Guide to Step 3: Scenario Review\n\n"
        "Step 3 is where you evaluate candidates and build an audit trail:\n"
        "- **Inspect Shortlisted Scenarios**: Review candidate shortfall, duration, station concurrence, and historical percentile.\n"
        "- **Key Charts**:\n"
        "  - *Rainfall Deficit Curve*: Cumulative shortfall vs. historical average.\n"
        "  - *Combined Storage Simulation*: Illustrative mass-balance trajectory showing response band crossings (Stage 1 @ 40%, Stage 2 @ 30%, Stage 3 @ 20%).\n"
        "  - *Crop Water Deficit*: Net atmospheric irrigation deficit for regional sorghum and cotton.\n"
        "- **Decision Trail**: Record engineering reviewer notes and mark each candidate as **Accepted** or **Rejected**. A completed review is required before export.\n\n"
        "👉 *Next step: Once all candidates are reviewed, proceed to **'Step 4: Exports'**.*"
    ),
    "step_4_guide": (
        "### 📦 Guide to Step 4: Exports & Deliverables\n\n"
        "Step 4 compiles the verified handoff packet for hydrologists and councils:\n"
        "- **Readiness Checklist**: Confirms that all shortlisted scenarios have an approved or rejected decision with notes.\n"
        "- **Privacy & Local Data Consent**: If local rain gauge data is used, check the consent box to include it in the portable export bundle.\n"
        "- **Deliverables**:\n"
        "  - **Executive Technical Brief (PDF)**: Clean, publication-ready summary with decision rationale, figures, and limitations.\n"
        "  - **Verified Data Bundle (ZIP)**: Replayable archive with exact raw CSV data, scenario definitions, review decisions, and SHA-256 manifest.\n"
        "  - **Excel Audit Workbook (XLSX)**: Complete tabular data for external modeling (HEC-HMS, WAM, spreadsheets)."
    ),
    "kbdi_faq": (
        "### 🔥 Hydrologic Index: Keetch-Byram Drought Index (KBDI)\n\n"
        "- **What it is**: KBDI is a continuous mathematical index measuring soil moisture deficit and deep organic matter dryness, ranging from 0 (saturated) to 800 (extreme drought).\n"
        "- **Illustrative Stress Marker (≥600)**: In South Texas, KBDI ≥ 600 indicates severe fuel dryness where wildfire danger escalates and county burn bans are commonly considered.\n"
        "- **Crossing vs. Peak Day**: BASIN identifies both the **first day** the sequence crosses 600 and the **peak day** of maximum dry-spell intensity.\n"
        "- **Official Authority**: BASIN calculates KBDI under fixed reference temperature assumptions for screening. Official burn bans and ratings are declared exclusively by county authorities and the **Texas A&M Forest Service**."
    ),
    "crop_deficit_faq": (
        "### 🌾 Agronomic Metric: Illustrative Crop Water Deficit\n\n"
        "- **What it calculates**: Estimates net atmospheric irrigation shortfall: \\(\\text{Deficit} = \\text{ET}_c - P\\), where \\(\\text{ET}_c\\) is crop evapotranspiration under standard reference demand and \\(P\\) is scenario rainfall.\n"
        "- **Regional Crops**: Evaluates dominant South Texas crops (grain sorghum and upland cotton) during warm-season growth stages.\n"
        "- **No Yield Guarantees**: This is an illustrative atmospheric demand calculation, not a safe-yield guarantee or a scheduled farm irrigation prescription."
    )
}

def _render_workspace_summary(workspace) -> str:
    """Render a comprehensive overview of the loaded run and shortlisted scenarios."""
    import calendar
    scenarios = getattr(workspace, "scenarios", [])
    selected_ids = getattr(workspace, "selected", [])
    if not scenarios:
        return "⚠️ **No scenarios in workspace**: Generate or load scenarios first."

    total_candidates = len(scenarios)
    shortlist_count = len(selected_ids)
    sys_obj = getattr(getattr(workspace, "water_system_selection", None), "config", None)
    sys_desc = f"{sys_obj.name} ({sys_obj.total_capacity_acft:,.0f} ac-ft)" if sys_obj else "Region N Reservoir System"

    shortlisted = [workspace.get(sid) for sid in selected_ids if any(s.id == sid for s in scenarios)]
    pool = shortlisted or scenarios

    peak_deficit_s = max(pool, key=lambda s: s.features.get("deficit_mm", 0.0))
    longest_s = max(pool, key=lambda s: s.features.get("duration_days", 0))
    highest_concur_s = max(pool, key=lambda s: s.features.get("concurrence", 0.0))

    header = "| Scenario | Duration | Shortfall (mm) | Shortfall (in) | Concurrence | Percentile | Profile | Status |\n|---|---|---|---|---|---|---|---|"
    rows = []
    for s in shortlisted:
        f = s.features
        def_mm = f.get("deficit_mm", 0.0)
        def_in = def_mm / 25.4
        conc_pct = f.get("concurrence", 0.0) * 100
        p_pct = f.get("historical_percentile", 0.0) * 100
        prof = getattr(s, "cluster_name", f"Group {s.cluster}")
        status_symbol = "✓ Accepted" if s.status == "accepted" else ("✗ Rejected" if s.status == "rejected" else "Unreviewed")
        rows.append(f"| **{s.id}** | {f.get('duration_days', 0)} d | {def_mm:.1f} mm | {def_in:.2f} in | {conc_pct:.1f}% | {p_pct:.0f}th | {prof} | {status_symbol} |")

    table_md = header + "\n" + "\n".join(rows)
    snapshot = getattr(getattr(workspace, "source", None), "manifest", {}).get("sha256", "provisional")[:12]

    return (
        f"**Workspace Run & Shortlist Overview** (Run `{getattr(workspace, 'id', 'current')}`)\n\n"
        f"Generated **{total_candidates} candidates**; **{shortlist_count} scenarios shortlisted** for hydrologic review.\n"
        f"Active Water System: **{sys_desc}**.\n\n"
        f"{table_md}\n\n"
        f"**Key Run Findings:**\n"
        f"- **Peak Rainfall Shortfall**: **{peak_deficit_s.id}** with {peak_deficit_s.features['deficit_mm']:.1f} mm ({peak_deficit_s.features['deficit_mm']/25.4:.2f} in) deficit over {peak_deficit_s.features['duration_days']} days.\n"
        f"- **Longest Multi-Season Drought**: **{longest_s.id}** spanning {longest_s.features['duration_days']} days ({calendar.month_name[longest_s.features['onset_month']]} onset).\n"
        f"- **Highest Selected-Station Concurrence**: **{highest_concur_s.id}** with {highest_concur_s.features['concurrence']*100:.1f}% multi-station concurrence across Region N.\n\n"
        f"> Source: BASIN workspace · Snapshot `{snapshot}…`\n"
        f"> 💡 *To inspect an individual scenario, ask `Tell me about {selected_ids[0] if selected_ids else 'B-001'}`. "
        f"To compare candidates, ask `Compare {selected_ids[0]} and {selected_ids[1] if len(selected_ids) > 1 else selected_ids[0]}`. "
        f"To test reservoir survival, ask `Can reservoir survive {selected_ids[0]} with 20% lower rainfall?`.*"
    )


def _render_rank_comparison(workspace, id_a: str, id_b: str) -> str:
    """Compare the multi-criteria ranking components and score differences between two scenarios."""
    s1 = workspace.get(id_a)
    s2 = workspace.get(id_b)
    w = workspace.weights
    c1, c2 = s1.components, s2.components

    header = f"| Priority Component | Weight | {id_a} Contribution | {id_b} Contribution | Delta ({id_a} − {id_b}) |\n|---|---|---|---|---|"
    rows = []
    keys = ["severity", "duration", "concurrence", "season"]
    labels = {"severity": "Severity", "duration": "Duration", "concurrence": "Concurrence", "season": "Seasonality"}
    advantages = {}
    for k in keys:
        contrib_a = c1.get(k, 0.0)
        contrib_b = c2.get(k, 0.0)
        delta = contrib_a - contrib_b
        weight_val = w.get(k, 0.0)
        weight_str = f"{weight_val:.0f}%" if weight_val > 1.0 else f"{weight_val*100:.0f}%"
        rows.append(f"| {labels[k]} | {weight_str} | {contrib_a:.2f} | {contrib_b:.2f} | {delta:+.2f} |")
        advantages[k] = delta

    total_delta = s1.score - s2.score
    rows.append(f"| **Total Priority Score** | **100%** | **{s1.score:.2f}** | **{s2.score:.2f}** | **{total_delta:+.2f}** |")
    table_md = header + "\n" + "\n".join(rows)

    winner, loser = (id_a, id_b) if total_delta >= 0 else (id_b, id_a)
    win_s, lose_s = (s1, s2) if total_delta >= 0 else (s2, s1)

    adv_for_winner = {k: (c1[k] - c2[k] if total_delta >= 0 else c2[k] - c1[k]) for k in keys}
    top_comp = max(adv_for_winner, key=adv_for_winner.get)
    top_margin = adv_for_winner[top_comp]

    w_sev = w['severity'] if w['severity'] > 1.0 else w['severity'] * 100
    explanation = (
        f"**Why {winner} ranked higher than {loser}:**\n"
        f"Under your active ranking weights, **{winner}** earned **{top_margin:+.2f} more points** from **{labels[top_comp]}** than {loser}. "
    )
    if win_s.features['duration_days'] != lose_s.features['duration_days']:
        explanation += (
            f"Even though {loser} had a longer duration ({lose_s.features['duration_days']} d vs {win_s.features['duration_days']} d), "
            f"the {w_sev:.0f}% severity weight prioritized {winner}'s deeper rainfall shortfall "
            f"({win_s.features['deficit_mm']:.1f} mm vs {lose_s.features['deficit_mm']:.1f} mm)."
        )

    snapshot = getattr(getattr(workspace, "source", None), "manifest", {}).get("sha256", "provisional")[:12]
    return (
        f"**Ranking Comparison: {id_a} vs {id_b}**\n\n"
        f"{table_md}\n\n"
        f"{explanation}\n\n"
        f"> Source: BASIN workspace · Snapshot `{snapshot}…`\n"
        f"> ⚠️ Scores are ranking priorities calculated from your weight settings, not probabilities or physical safety ratings."
    )


def semantic_query_route(workspace, prompt: str) -> str:
    """Deterministic Semantic Entity & Synonym Graph intent router.

    Parses natural language queries, extracts scenario IDs, station codes,
    years, and parameter thresholds, executes verified local tools, and renders
    standard templates completely offline with zero LLM dependency.
    """
    import calendar
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

    if any(q in p for k in [
        "should council", "should the city", "declare stage", "mandate stage",
        "should we declare", "declare an emergency", "mandate cuts"
    ] for q in [k]):
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

    # 5. Workspace Run & Shortlist Overview
    is_summary_query = (
        not id_matches and any(k in p for k in [
            "scenarios ive just run", "scenarios i've just run", "scenarios i just ran", "scenarios ive run",
            "scenarios in this run", "scenarios in my run", "scenarios run",
            "summarize scenarios", "summarise scenarios", "summarize the scenarios", "summarise the scenarios",
            "summarize my scenarios", "summarise my scenarios",
            "overview of scenarios", "overview of the run", "run overview", "run summary", "workspace summary",
            "summarize my shortlist", "summarize the shortlist", "shortlist overview", "shortlist summary",
            "what scenarios did i run", "what scenarios have i run", "what scenarios are in", "what are my scenarios",
            "show my scenarios", "show me my scenarios", "list my scenarios", "my scenarios",
            "tell me about the scenarios", "describe the scenarios"
        ])
    )
    if is_summary_query:
        return _render_workspace_summary(workspace)

    # 6. Auto-identify worst / longest / top scenarios when requested without explicit ID
    is_worst_query = (
        not id_matches and any(k in p for k in [
            "worst scenario", "worst drought", "most severe scenario", "most severe drought",
            "highest deficit scenario", "largest deficit scenario", "biggest deficit scenario",
            "which scenario is the worst", "what is the worst scenario", "which is the worst"
        ])
    )
    if is_worst_query and getattr(workspace, "scenarios", None):
        candidates = getattr(workspace, "selected", []) or [s.id for s in workspace.scenarios]
        target_id = max(candidates, key=lambda sid: workspace.get(sid).features.get("deficit_mm", 0.0))
        target_s = workspace.get(target_id)
        intro = f"**Worst Scenario by Deficit: {target_id}** ({target_s.features['deficit_mm']:.1f} mm / {target_s.features['deficit_mm']/25.4:.2f} in shortfall over {target_s.features['duration_days']} days)\n\n"
        return intro + render_tool_result("describe_scenario", describe_scenario(workspace, target_id))

    is_longest_query = (
        not id_matches and any(k in p for k in [
            "longest scenario", "longest drought", "longest duration scenario", "maximum duration scenario",
            "which scenario is the longest", "what is the longest scenario"
        ])
    )
    if is_longest_query and getattr(workspace, "scenarios", None):
        candidates = getattr(workspace, "selected", []) or [s.id for s in workspace.scenarios]
        target_id = max(candidates, key=lambda sid: workspace.get(sid).features.get("duration_days", 0))
        target_s = workspace.get(target_id)
        intro = f"**Longest Drought Scenario: {target_id}** ({target_s.features['duration_days']} days duration, {calendar.month_name[target_s.features['onset_month']]} onset)\n\n"
        return intro + render_tool_result("describe_scenario", describe_scenario(workspace, target_id))

    is_top_query = (
        not id_matches and any(k in p for k in [
            "top scenario", "top-ranked scenario", "top ranked scenario", "#1 scenario",
            "number one scenario", "headline scenario", "highest ranked scenario"
        ])
    )
    if is_top_query and getattr(workspace, "scenarios", None):
        target_id = workspace.selected[0] if getattr(workspace, "selected", None) else workspace.scenarios[0].id
        target_s = workspace.get(target_id)
        intro = f"**Top-Ranked Scenario: {target_id}** (Priority Score: {target_s.score:.2f}, Profile: {getattr(target_s, 'cluster_name', f'Group {target_s.cluster}')})\n\n"
        return intro + render_tool_result("describe_scenario", describe_scenario(workspace, target_id))

    # 7. Comparative ranking explanation between 2 scenarios
    if len(id_matches) >= 2 and any(k in p for k in [
        "why did", "higher than", "better than", "ahead of", "beat", "rank higher",
        "ranked higher", "rank vs", "compare ranking", "compare score", "why is"
    ]):
        return _render_rank_comparison(workspace, id_matches[0], id_matches[1])

    # 8. Compare top 2 without explicit IDs
    if len(id_matches) < 2 and any(k in p for k in ["top two", "top 2", "first two", "first 2", "compare shortlisted"]):
        if len(getattr(workspace, "selected", [])) >= 2:
            res = compare_scenarios(workspace, workspace.selected[0], workspace.selected[1])
            return render_tool_result("compare_scenarios", res)

    # 9. Conversational, Workflow & Educational Guides
    is_greeting = (
        not id_matches
        and any(p == k or p.startswith(k + " ") or p.endswith(" " + k) or p == k + "!" or p == k + "?" for k in [
            "hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening",
            "who are you", "what can you do", "introduce yourself", "help me"
        ])
        and not any(k in p for k in ["scenario", "rainfall", "storage", "station", "deficit"])
    )
    if is_greeting:
        return DOMAIN_TOPICS["greetings"]

    # Step-specific guides
    if not id_matches and any(k in p for k in ["step 1", "step one", "data dashboard", "load data", "custom gauge", "upload csv", "how to load data"]):
        return DOMAIN_TOPICS["step_1_guide"]

    if not id_matches and any(k in p for k in ["step 2", "step two", "how to build scenarios", "how to generate scenarios", "how to create scenarios", "how do i build scenarios", "priority weights", "how to make scenarios"]):
        return DOMAIN_TOPICS["step_2_guide"]

    if not id_matches and any(k in p for k in ["step 3", "step three", "review tab", "how to review", "how do i review", "review process", "reviewing scenarios", "how to accept", "how to reject"]):
        return DOMAIN_TOPICS["step_3_guide"]

    if not id_matches and any(k in p for k in ["step 4", "step four", "export tab", "how to export", "export bundle", "export packet", "how do i export", "download pdf", "download zip", "export deliverables"]):
        return DOMAIN_TOPICS["step_4_guide"]

    # General Workflow, Getting Started, Website Orientation, or "Confused"
    is_workflow_guide = (
        not id_matches
        and (
            any(k in p for k in [
                "how do i use", "how to use", "how does this work", "how does basin work",
                "getting started", "where do i start", "what do i do", "walkthrough", "tutorial",
                "confused", "i am lost", "i'm lost", "help with this tool", "explain the tool",
                "workflow", "how the tool works", "user guide", "instructions", "overview of basin",
                "how is the user supposed to learn", "how do users learn", "figure out",
                "understand the website", "figure out the website", "navigate", "orientation",
                "show me around", "what is this site", "what is this tool", "what can i do here",
                "how do i begin", "help me learn", "how to operate", "how do i navigate",
                "what should i do", "where should i start", "where do we start", "how do we start"
            ])
            or (
                any(w in p for w in ["website", "site", "webpage", "web page", "app", "application", "tool", "platform", "interface"])
                and any(w in p for w in ["help", "figure out", "guide", "learn", "how", "what", "navigate", "start", "understand", "use", "explore", "tour", "tutorial", "work"])
            )
            or (
                "what can i do" in p and not any(k in p for k in ["scenario", "rainfall", "storage", "station", "deficit"])
            )
        )
    )
    if is_workflow_guide:
        return DOMAIN_TOPICS["workflow_guide"]

    # KBDI Wildfire Index
    if not id_matches and any(k in p for k in ["kbdi", "keetch-byram", "keetch byram", "burn ban", "fire danger", "wildfire"]):
        return DOMAIN_TOPICS["kbdi_faq"]

    # Crop Water Deficit
    if not id_matches and any(k in p for k in ["crop deficit", "crop water", "irrigation deficit", "crop demand"]):
        return DOMAIN_TOPICS["crop_deficit_faq"]

    # 10. Domain Hydrologic & Rural Council FAQ
    is_concurrence_faq = (
        any(k in p for k in [
            "what is concurrence", "what does concurrence mean", "explain concurrence",
            "define concurrence", "meaning of concurrence", "why does concurrence matter",
            "why is concurrence important", "concurrence in plain english", "plain english concurrence"
        ]) or (not id_matches and "concurrence" in p and any(k in p for k in ["what", "how", "mean", "concept", "explain", "define", "meaning", "plain english", "understand", "why"]))
    )
    if is_concurrence_faq:
        return DOMAIN_TOPICS["concurrence"]

    is_storage_35_faq = (
        not any(k in p for k in ["spectrum", "initial storage", "run simulation", "test reservoir"])
        and any(k in p for k in [
            "what happens at 35", "why 35", "explain 35", "what is 35", "35% threshold",
            "35 percent threshold", "35% storage", "35 percent storage", "stage 3 critical",
            "what is stage 3", "stage 3 shortage", "35% combined storage", "35 percent combined storage",
            "thirty-five percent", "critical shortage", "critical storage"
        ])
    )
    if is_storage_35_faq:
        return DOMAIN_TOPICS["storage_35pct"]

    if any(k in p for k in ["dead pool", "inactive storage", "dead storage", "75,000", "75000", "cavitation", "pump cavitation", "lowest outlet", "intake sill"]):
        return DOMAIN_TOPICS["dead_pool"]

    if any(k in p for k in ["mary rhodes", "pipeline buffer", "lake texana", "colorado river pipeline", "72 mgd", "interbasin transfer", "external supply"]):
        return DOMAIN_TOPICS["mary_rhodes"]

    if (
        any(k in p for k in ["kmeans", "k-means"]) and any(k in p for k in ["why", "cluster", "clustering", "purpose", "top 6", "top-6", "clone", "diversity"])
    ) or any(k in p for k in ["why kmeans", "why k-means", "why cluster", "why clustering", "why not top 6", "clone problem", "diversity vs clones", "kmeans clustering"]):
        return DOMAIN_TOPICS["kmeans_diversity"]

    if any(k in p for k in [
        "rural council", "rural councils", "small utility", "small utilities", "small water",
        "water board", "water boards", "small town", "municipal utility district", "mud", "wsc",
        "councils prepare", "utilities do", "advice for rural", "rural water"
    ]):
        return DOMAIN_TOPICS["rural_councils"]

    if (
        ("forecast" in p and any(k in p for k in ["difference", "scenario", "predict", "versus", "vs"]))
        or any(k in p for k in ["is this a forecast", "predict rainfall", "are these predictions", "predictive model", "scenario vs forecast", "forecast vs scenario"])
    ):
        return DOMAIN_TOPICS["scenarios_vs_forecasts"]

    if (
        ("mm" in p and "acre-feet" in p)
        or any(k in p for k in ["deficit in mm vs acre-feet", "convert mm to acre feet", "runoff coefficient", "why mm not acre feet", "point deficit vs reservoir volume", "station deficit vs storage"])
    ):
        return DOMAIN_TOPICS["deficit_vs_volume"]

    if any(k in p for k in [
        "summer evaporation", "summer onset", "summer drought", "summer droughts", "evaporation role",
        "pan evaporation", "summer vs winter", "lake evaporation", "evaporation affect", "evaporative loss"
    ]):
        return DOMAIN_TOPICS["summer_evaporation"]

    try:
        spectrum_request = any(k in p for k in ["spectrum", "stress spectrum", "multi-tier", "tiers", "tipping point", "sweep", "countdown", "days to breach", "days-to-breach"])
        reservoir_request = any(k in p for k in ["survive", "survival", "infrastructure", "reservoir", "drawdown", "capacity", "storage", "restriction", "lake corpus christi", "choke canyon"])

        # Routes 1-2: illustrative storage experiments with explicitly labelled settings
        if spectrum_request or reservoir_request:
            if len(id_matches) > 1:
                return clarify("name one scenario ID for this experiment; several were given: " + ", ".join(id_matches) + ".")
            arguments = parse_experiment_arguments(p, spectrum_request)
            if not id_matches and year is None:
                target_id = workspace.selected[0] if getattr(workspace, "selected", None) else (workspace.scenarios[0].id if getattr(workspace, "scenarios", None) else "")
            else:
                target_id = id_matches[0] if id_matches else ""
            arguments.update(scenario_id=target_id, year=year)
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
        if id_matches or ("scenario" in p and any(k in p for k in ["tell me about", "describe", "profile", "metrics", "details"])):
            if not id_matches:
                return need_ids(1, "describe")
            res = describe_scenario(workspace, id_matches[0])
            return render_tool_result("describe_scenario", res)

        return (
            "**BASIN Analyst Assistant**\n\n"
            "I am a read-only decision-support tool focused on rainfall scenario analysis, "
            "reservoir stress testing, and guiding you through the BASIN workflow.\n\n"
            "💡 **Looking to learn the application?**\n"
            "- Ask me: *\"How do I use this website?\"* or *\"Show me around the workflow\"*\n"
            "- Click **'Start tutorial'** on Step 1: Data Dashboard for a step-by-step interactive tour.\n"
            "- Click **'Try an example'** on Step 1 to load pre-computed scenarios and explore immediately.\n\n"
            "I can also help you with verified calculations for this workspace:\n\n"
            f"{TOOL_LIST_HELP}"
        )
    except ValueError as err:
        return f"⚠️ **Analysis Boundary**: {err}"
    except Exception as ex:
        return f"⚠️ **Query Processing Error**: {ex}"


def select_candidate_tools(query: str, max_tools: int = 3) -> list[dict[str, Any]]:
    """Select the most query-relevant tool schemas to keep prompt size small and fast on CPU."""
    q = query.lower()

    # Informational, workflow, or greeting queries do not require tool calls
    if any(k in q for k in [
        "how to", "how do i", "how does", "what is basin", "getting started", "where do i start",
        "what do i do", "walkthrough", "tutorial", "confused", "i am lost", "i'm lost",
        "help", "guide", "workflow", "step 1", "step 2", "step 3", "step 4",
        "data dashboard", "review tab", "export tab", "how to review", "how to export",
        "hello", "hi", "hey", "who are you", "what can you do", "introduce yourself"
    ]):
        return []

    matches = []

    keywords = {
        "describe_scenario": ["scenario", "profile", "b-", "cand"],
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

    if not matches:
        return []

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
