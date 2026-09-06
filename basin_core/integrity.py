"""Reconstruct scenario content and review transitions from the source snapshot."""
from __future__ import annotations

import hashlib
import math

import numpy as np
import pandas as pd

from basin_core.analysis import WeightedSumRanking
from basin_core.engine import Reference, Scenario, ScenarioParams, rainfall_digest
from basin_core.evidence import validate_evidence


def compare_values(actual, expected, label):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError(f"{label}: field mismatch")
        for key in expected:
            compare_values(actual[key], expected[key], f"{label}.{key}")
    elif isinstance(expected, bool):
        if not isinstance(actual, (bool, np.bool_)) or actual != expected:
            raise ValueError(f"{label}: boolean mismatch")
    elif isinstance(expected, (int, float, np.number)):
        if isinstance(actual, bool) or not isinstance(actual, (int, float, np.number)) or not math.isfinite(float(actual)) or not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-8):
            raise ValueError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise ValueError(f"{label}: value mismatch")


def check_digest(stored, frame, label, legacy=False):
    digests = {rainfall_digest(frame)}
    if legacy:
        digests.add(hashlib.sha256(frame.rename_axis(None).to_csv(float_format="%.12g", lineterminator="\n").encode()).hexdigest())
    if stored not in digests:
        raise ValueError(f"{label}: rainfall digest mismatch")


def reconstruct_record(record, reference, legacy=False):
    p = record["provenance"]
    if p["method"] != "synchronized-season-matched-whole-window-v1":
        raise ValueError("Unsupported rainfall transformation method")
    start, end = pd.Timestamp(p["source_start"]), pd.Timestamp(p["source_end"])
    duration = p["source_window_days"]
    if start.day != 1 or type(duration) is not int or not 30 <= duration <= 365 or end != start + pd.Timedelta(days=duration - 1):
        raise ValueError("Source window dates or duration mismatch")
    if set(p["retention_by_station"]) != set(reference.stations):
        raise ValueError("Source station identities mismatch")
    factors = pd.Series(p["retention_by_station"], dtype=float).reindex(reference.stations)
    if not np.isfinite(factors).all() or not factors.between(0, 1).all():
        raise ValueError("Invalid original rainfall retention")
    original = reference.daily.reindex(pd.date_range(start, end))[reference.stations]
    if original.isna().any().any():
        raise ValueError("Source window contains missing observations")
    frame = original * factors
    scenario = Scenario(record["id"], frame, p, reference)
    revision, status, approval = 1, "unreviewed", None
    history = []
    for raw_event in record["history"]:
        event = dict(raw_event)
        action = event["action"]
        if not isinstance(event.get("at"), str) or not event["at"]:
            raise ValueError("Audit event timestamp missing")
        if action in ("scale", "replace"):
            check_digest(event["previous_sha256"], frame, "Previous revision", legacy)
            event["previous_sha256"] = rainfall_digest(frame)
            if action == "scale":
                factor = event["factor"]
                if isinstance(factor, bool) or not isinstance(factor, (int, float)) or not np.isfinite(factor) or not 0 <= factor <= 2:
                    raise ValueError("Invalid edit factor")
                frame = frame * factor
            else:
                frame = pd.DataFrame(event["replacement_values"], index=frame.index, columns=reference.stations)
            reference.features(frame)
            revision += 1
            status, approval = "unreviewed", None
        elif action in ("accepted", "rejected"):
            status = action
            approval = revision if action == "accepted" else None
        else:
            raise ValueError("Unknown review action")
        if event["revision"] != revision:
            raise ValueError("Audit revision sequence mismatch")
        check_digest(event["series_sha256"], frame, "Review event", legacy)
        event["series_sha256"] = rainfall_digest(frame)
        history.append(event)
    if (record["revision"], record["status"], record["approved_revision"]) != (revision, status, approval):
        raise ValueError("Current approval or revision disagrees with audit history")
    check_digest(record["series_sha256"], frame, "Current revision", legacy)
    scenario.series = frame
    scenario.features = reference.features(frame)
    compare_values(record["features"], scenario.features, "Scenario features")
    scenario.revision, scenario.status, scenario.approved_revision = revision, status, approval
    scenario.history = history
    scenario.cluster = record["cluster"]
    scenario.cluster_name = record.get("cluster_name", f"Group {scenario.cluster}")
    return scenario


def reconstruct_audit(source, audit, legacy=False, require_export=False):
    if audit["snapshot_sha256"] != source.manifest["sha256"]:
        raise ValueError("Audit source snapshot identity mismatch")
    params = ScenarioParams(**{**audit["params"], **{k: tuple(audit["params"][k]) for k in ("stations", "durations", "months")}})
    params.validate()
    reference = Reference(source, list(params.stations))
    records = audit["scenarios"]
    if not isinstance(records, list) or not records:
        raise ValueError("Missing scenario audit records")
    ids = [r["id"] for r in records]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("Duplicate or invalid scenario audit IDs")
    selected = audit["selected"]
    if not isinstance(selected, list) or not selected or len(selected) != len(set(selected)) or not set(selected) <= set(ids):
        raise ValueError("Selected scenario IDs must be distinct existing audit records")
    scenarios = [reconstruct_record(r, reference, legacy) for r in records]
    WeightedSumRanking().apply(scenarios, audit["weights"])
    for scenario, record in zip(scenarios, records):
        compare_values(record["score"], scenario.score, "Priority score")
        compare_values(record["components"], scenario.components, "Score components")
    if not legacy:
        validate_evidence(audit["evidence"], audit["evidence_refs"], audit["conflicts"], ids)
    if require_export:
        chosen = [s for s in scenarios if s.id in selected]
        if any(s.status == "unreviewed" for s in chosen) or not any(s.status == "accepted" for s in chosen):
            raise ValueError("Shortlist must be fully reviewed with an accepted scenario")
    return params, reference, scenarios
