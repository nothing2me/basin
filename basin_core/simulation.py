"""Versioned, replayable illustrative experiments shared by every presentation path."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import TYPE_CHECKING, Literal

import pandas as pd

from basin_core.analysis import RESERVOIR_ASSUMPTIONS, simulate_stress_spectrum
from basin_core.engine import Scenario, rainfall_digest
from basin_core.evidence import public_copy

if TYPE_CHECKING:
    from basin_core.workspace import Workspace

MODEL_VERSION = RESERVOIR_ASSUMPTIONS["model_version"]
# Version 2: storage bands are inclusive like crossing days, tier labels are relative to the
# input rainfall instead of "Selected scenario", and status text no longer says
# "Survived"/"Breached". Runs saved under version 1 are refused rather than reinterpreted.
THRESHOLD_VERSION = "inclusive-daily-endpoints-with-day-zero-2"


def content_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def percent_fraction(value: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
        raise ValueError(f"{label} must be a finite percentage from 0 to 100")
    return float(value) / 100


@dataclass(frozen=True)
class SimulationSettings:
    baseline_kind: Literal["observed_window", "scenario_revision"] = "scenario_revision"
    initial_storage_fraction: float = .48
    conservation_fraction: float = 0.0
    pipeline_active: bool = True
    retention_fractions: tuple[float, ...] = (1.0, .8, .6, .4)

    def __post_init__(self) -> None:
        if self.baseline_kind not in ("observed_window", "scenario_revision"):
            raise ValueError("Choose observed_window or scenario_revision as the baseline")
        for value in (self.initial_storage_fraction, self.conservation_fraction, *self.retention_fractions):
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Internal simulation settings require finite fractions from 0 to 1")
        if type(self.pipeline_active) is not bool:
            raise ValueError("Pipeline availability must be true or false")
        if not isinstance(self.retention_fractions, tuple) or not 1 <= len(self.retention_fractions) <= 12 or len(set(self.retention_fractions)) != len(self.retention_fractions):
            raise ValueError("Choose one to twelve distinct retention fractions")

    @classmethod
    def from_percent(cls, *, initial_storage_percent: float = 48, conservation_percent: float = 0,
                     baseline_kind: str = "scenario_revision", pipeline_active: bool = True,
                     retention_percentages: tuple[float, ...] = (100, 80, 60, 40)) -> SimulationSettings:
        return cls(baseline_kind, percent_fraction(initial_storage_percent, "Initial storage"),
                   percent_fraction(conservation_percent, "Conservation"), pipeline_active,
                   tuple(percent_fraction(p, "Rainfall retention") for p in retention_percentages))


def resolve_scenario(workspace: Workspace, scenario_id: str = "", year: int | None = None,
                     revision: int | None = None) -> Scenario:
    if year is not None and (type(year) is not int or not 1 <= year <= 9999):
        raise ValueError("Year must be an integer calendar year; matching uses the source start year")
    if scenario_id:
        scenario = workspace.get(scenario_id)
        if year is not None and int(scenario.provenance["source_start"][:4]) != year:
            raise ValueError("Requested scenario and source start year disagree")
    else:
        if year is None:
            raise ValueError("Choose an exact scenario ID, or supply a source start year to find candidates")
        matches = [s for s in workspace.scenarios if int(s.provenance["source_start"][:4]) == year]
        if not matches:
            years = sorted({s.provenance["source_start"][:4] for s in workspace.scenarios})
            manifest = workspace.source.manifest
            raise ValueError(
                f"No scenario: No historical drought events found for year {year}. "
                f"The bundled NOAA record covers {str(manifest['start'])[:4]}–{str(manifest['end'])[:4]}. "
                f"Available start years: {', '.join(years)}. "
                "Choose an existing scenario or generate a suitable window explicitly."
            )
        if len(matches) != 1:
            choices = "; ".join(f"{s.id} r{s.revision}: {s.provenance['source_start']} to {s.provenance['source_end']}" for s in matches)
            raise ValueError("Multiple scenarios match; choose an exact scenario ID: " + choices)
        scenario = matches[0]
    if revision is not None and (type(revision) is not int or revision != scenario.revision):
        raise ValueError("Scenario revision changed; inspect the current revision before running")
    return scenario


def describe_input_rainfall(scenario: Scenario, baseline_kind: str = "scenario_revision",
                            revision: int | None = None) -> dict:
    """State what the 100% tier of an experiment is, for every presentation surface.

    ``observed_fraction`` is the input as a single multiple of the observed window. It is
    None when no single multiple exists (station-specific retention or a CSV replacement).
    Nothing here is stored in a saved run, so the description never changes run identity.
    """
    p = scenario.provenance
    window = f"{p['source_start']} to {p['source_end']}"
    if baseline_kind == "observed_window":
        return {"baseline_kind": baseline_kind, "scenario_id": scenario.id, "revision": None,
                "window": window, "observed_fraction": 1.0,
                "summary": f"unmodified NOAA observations for {window}",
                "hundred_percent_meaning": "100% is the unmodified observed window."}
    if baseline_kind != "scenario_revision":
        raise ValueError("Choose observed_window or scenario_revision as the baseline")
    revision = scenario.revision if revision is None else revision
    retention = {str(k): float(v) for k, v in p["retention_by_station"].items()}
    values = list(retention.values())
    if values and all(v == values[0] for v in values):
        fraction: float | None = values[0]
        steps = [f"constructed at {round(values[0] * 100, 1):g}% of observed rainfall"]
    else:
        fraction = None
        steps = ["constructed with station-specific retention ("
                 + ", ".join(f"{k} {round(v * 100, 1):g}%" for k, v in retention.items()) + ")"]
    for event in scenario.history:
        if event.get("revision", 0) > revision:
            break
        if event["action"] == "scale":
            if fraction is not None:
                fraction *= float(event["factor"])
            steps.append(f"revision {event['revision']} scaled rainfall by {float(event['factor']):g}")
        elif event["action"] == "replace":
            fraction = None
            steps.append(f"revision {event['revision']} replaced rainfall from a CSV")
    return {"baseline_kind": baseline_kind, "scenario_id": scenario.id, "revision": revision,
            "window": window, "observed_fraction": fraction,
            "summary": f"scenario {scenario.id} revision {revision}, {'; '.join(steps)} (source window {window})",
            "hundred_percent_meaning": (f"100% is scenario {scenario.id} revision {revision} rainfall, including its "
                                        "construction and edits; it is not the unmodified historical record.")}


def observed_percent(tier_multiplier: float, input_rainfall: dict) -> float | None:
    """A tier as a percentage of the observed window, when that is a single number."""
    fraction = input_rainfall.get("observed_fraction")
    return None if fraction is None else round(float(tier_multiplier) * fraction * 100, 1)


def evidence_context(workspace: Workspace, scenario: Scenario) -> dict:
    refs = sorted(workspace.evidence_refs[scenario.id])
    return public_copy({"scenario_id": scenario.id, "revision": scenario.revision, "series_sha256": scenario.digest(),
                        "evidence_refs": refs,
                        "evidence": sorted([e for e in workspace.evidence if e["id"] in refs], key=lambda e: e["id"]),
                        "conflicts": sorted([c for c in workspace.conflicts if c["left_id"] in refs or c["right_id"] in refs], key=lambda c: c["id"])})


def scenario_series_at_revision(workspace: Workspace, scenario: Scenario, revision: int) -> pd.DataFrame:
    if type(revision) is not int or not 1 <= revision <= scenario.revision:
        raise ValueError("Invalid simulation scenario revision")
    p = scenario.provenance
    observed = workspace.reference.daily.loc[p["source_start"]:p["source_end"], list(scenario.series.columns)]
    frame = observed * pd.Series(p["retention_by_station"]).reindex(observed.columns)
    for event in scenario.history:
        if event["revision"] > revision:
            break
        if event["action"] == "scale":
            frame = frame * event["factor"]
        elif event["action"] == "replace":
            frame = pd.DataFrame(event["replacement_values"], index=frame.index, columns=frame.columns)
    return frame


def calculate(series: pd.DataFrame, settings: SimulationSettings) -> dict:
    spec = simulate_stress_spectrum(series, tiers=settings.retention_fractions,
                                   initial_pct=settings.initial_storage_fraction,
                                   conservation_pct=settings.conservation_fraction,
                                   pipeline_active=settings.pipeline_active)
    reference = spec if settings.conservation_fraction == 0 else simulate_stress_spectrum(
        series, tiers=settings.retention_fractions, initial_pct=settings.initial_storage_fraction,
        conservation_pct=0, pipeline_active=settings.pipeline_active)
    comparisons = []
    for chosen, baseline in zip(spec["summary_table"], reference["summary_table"]):
        before, after = baseline["day_stage3_20"], chosen["day_stage3_20"]
        delay = after - before if before is not None and after is not None else None
        df = spec["tier_results"][chosen["tier_multiplier"]]["df"]
        comparisons.append({"retention_percent": chosen["retention_pct"], "no_conservation_day_20": before,
                            "chosen_conservation_day_20": after, "delay_days": delay,
                            "mean_evaporation_acft_per_day": float(df["evap_acft"].mean()),
                            "mean_served_demand_acft_per_day": float(df["served_demand_acft"].mean())})
    return {"summary_table": spec["summary_table"],
            "trajectories": {str(m): result["df"].to_dict("records") for m, result in spec["tier_results"].items()},
            "conservation_comparison": comparisons,
            "no_conservation_trajectories": {str(m): result["df"].to_dict("records") for m, result in reference["tier_results"].items()}}


def create_run(workspace: Workspace, scenario: Scenario, settings: SimulationSettings) -> dict:
    series = scenario.series.copy() if settings.baseline_kind == "scenario_revision" else workspace.reference.daily.reindex(scenario.series.index)[list(scenario.series.columns)]
    payload = {"schema_version": "1.0", "model_version": MODEL_VERSION, "threshold_version": THRESHOLD_VERSION,
               "snapshot_sha256": workspace.source.manifest["sha256"], "scenario_id": scenario.id,
               "scenario_revision": scenario.revision, "scenario_sha256": scenario.digest(),
               "evidence_context": evidence_context(workspace, scenario), "settings": asdict(settings),
               "assumptions": RESERVOIR_ASSUMPTIONS,
               "baseline": {"dates": series.index.strftime("%Y-%m-%d").tolist(), "stations": list(series.columns),
                            "units": "mm/day", "values": series.to_numpy().tolist(), "sha256": rainfall_digest(series)},
               "results": calculate(series, settings)}
    # JSON round-trip detaches mutable frames, tuples and assumptions from the saved record.
    payload = json.loads(json.dumps(payload, allow_nan=False))
    return {"id": "sim-" + content_hash(payload), **payload}


def settings_from_run(run: dict) -> SimulationSettings:
    return SimulationSettings(**{**run["settings"], "retention_fractions": tuple(run["settings"]["retention_fractions"])})


def validate_run(workspace: Workspace, run: dict) -> None:
    from basin_core.integrity import compare_values
    if run["id"] != "sim-" + content_hash({k: v for k, v in run.items() if k != "id"}):
        raise ValueError("Saved simulation content hash mismatch")
    if (run["schema_version"], run["model_version"], run["threshold_version"]) != ("1.0", MODEL_VERSION, THRESHOLD_VERSION):
        raise ValueError("Unsupported simulation version; do not reinterpret older results")
    if run["snapshot_sha256"] != workspace.source.manifest["sha256"] or run["assumptions"] != RESERVOIR_ASSUMPTIONS:
        raise ValueError("Simulation source or assumptions mismatch")
    scenario = workspace.get(run["scenario_id"])
    revision_series = scenario_series_at_revision(workspace, scenario, run["scenario_revision"])
    if rainfall_digest(revision_series) != run["scenario_sha256"]:
        raise ValueError("Simulation does not match the recorded scenario revision")
    settings = settings_from_run(run)
    baseline = run["baseline"]
    frame = pd.DataFrame(baseline["values"], index=pd.to_datetime(baseline["dates"]), columns=baseline["stations"])
    expected = revision_series if settings.baseline_kind == "scenario_revision" else workspace.reference.daily.reindex(revision_series.index)[list(revision_series.columns)]
    if baseline["units"] != "mm/day" or rainfall_digest(frame) != baseline["sha256"] or rainfall_digest(expected) != baseline["sha256"]:
        raise ValueError("Simulation baseline does not match its identified evidence")
    context = run["evidence_context"]
    if (context["scenario_id"], context["revision"], context["series_sha256"]) != (scenario.id, run["scenario_revision"], run["scenario_sha256"]):
        raise ValueError("Simulation evidence context identity mismatch")
    if public_copy(context) != context:
        raise ValueError("Private annotations must not be embedded in simulation evidence")
    compare_values(run["results"], calculate(frame, settings), "Simulation replay")


def is_current(workspace: Workspace, run: dict) -> bool:
    return run["evidence_context"] == evidence_context(workspace, workspace.get(run["scenario_id"]))


def spectrum_view(run: dict) -> dict:
    """Adapt saved results for existing charts without recalculating them."""
    settings = settings_from_run(run)
    return {"summary_table": run["results"]["summary_table"],
            "conservation_comparison": run["results"]["conservation_comparison"],
            "tier_results": {float(m): {"df": pd.DataFrame(rows), "metrics": next(r for r in run["results"]["summary_table"] if r["tier_multiplier"] == float(m))} for m, rows in run["results"]["trajectories"].items()},
            "duration_days": len(run["baseline"]["dates"]), "initial_pct": settings.initial_storage_fraction * 100,
            "conservation_pct": settings.conservation_fraction * 100, "pipeline_active": settings.pipeline_active}
