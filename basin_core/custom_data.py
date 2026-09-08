"""Versioned local rainfall evidence; deterministic replay without original CSV bytes."""
from __future__ import annotations

import base64
from datetime import date
import hashlib
import json
import math
import re

import pandas as pd

from basin_core.uploads import RainfallPreview, preview_rainfall
from basin_core.rainfall_comparison import compare_rainfall


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def comparison_record(preview: RainfallPreview, source, station: str, relationship: str, daily: bool) -> dict:
    if station not in source.daily.columns:
        raise ValueError("Choose a station from the saved NOAA snapshot")
    values = source.select([station])[station]
    reference = {day.date(): None if pd.isna(value) else float(value) for day, value in values.items()}
    if relationship == "not_established" or not daily:
        return {"status": "blocked", "reason": "Station relationship or daily observation basis remains uncertain"}
    try:
        result = compare_rainfall(preview, reference, relationship=relationship, daily_basis_confirmed=daily)
    except ValueError as error:
        if "No dates have valid" not in str(error):
            raise
        return {"status": "blocked", "reason": "No paired valid dates"}
    return {"status": "calculated", "method": "paired-valid-calendar-days-v1",
            "rows": [[str(day), local, public] for day, local, public in result.rows],
            "paired_days": result.paired_days, "upload_total_mm": result.upload_total_mm,
            "reference_total_mm": result.reference_total_mm, "difference_mm": result.difference_mm,
            "relative_difference_pct": result.relative_difference_pct}


def build_record(raw: bytes, source, *, station: str, location: str, unit: str, provider: str,
                 observation_basis: str, reference_station: str, relationship: str,
                 daily_confirmed: bool, rationale: str, scenario_ids: list[str], supersedes: str = "") -> dict:
    preview = preview_rainfall(raw, station, location, unit)
    if any(not isinstance(v, str) or not v.strip() or len(v) > 2000 for v in (provider, observation_basis, rationale)):
        raise ValueError("Provide source/provider, observation-day basis and suitability rationale (up to 2000 characters each)")
    if relationship not in ("same_station", "regional_proxy", "not_established") or type(daily_confirmed) is not bool:
        raise ValueError("Invalid reference review declaration")
    if not scenario_ids or len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("Choose distinct scenarios to link as supporting evidence")
    normalized = [[str(day), value] for day, value in preview.observations]
    record = {"version": "custom-rainfall-1", "parser": "rainfall-csv-v1", "original_sha256": preview.original_sha256,
              "normalized_sha256": digest(normalized), "station": preview.station, "location": preview.location,
              "input_unit": unit, "normalized_unit": "mm", "provider": provider.strip(),
              "observation_basis": observation_basis.strip(), "rationale": rationale.strip(),
              "reference_station": reference_station, "relationship": relationship,
              "daily_confirmed": daily_confirmed, "snapshot_sha256": source.manifest["sha256"],
              "observations": normalized, "start": normalized[0][0], "end": normalized[-1][0],
              "expected_days": preview.expected_days, "valid_days": preview.valid_days, "missing_days": preview.missing_days,
              "scenario_ids": sorted(scenario_ids), "supersedes": supersedes,
              "role": "supporting comparison; not a numerical rainfall driver",
              "comparison": comparison_record(preview, source, reference_station, relationship, daily_confirmed)}
    record["id"] = "custom-" + digest(record)
    return record


def evidence_record(record: dict) -> dict:
    return {"id": record["id"], "title": "Custom rainfall comparison: " + record["station"],
            "publisher": record["provider"], "source_locator": "custom://" + record["id"][7:],
            "source_date": record["end"], "retrieved_at": "", "geographic_scope": record["location"],
            "kind": "derived calculation", "units": "mm", "review_status": "reviewed for this exercise",
            "description": "Original SHA-256: " + record["original_sha256"] + "; normalized SHA-256: " + record["normalized_sha256"]
                + "; reference: " + record["reference_station"] + "; relationship: " + record["relationship"]
                + "; daily basis: " + record["observation_basis"] + "; rationale/uncertainty: " + record["rationale"]
                + "; comparison: " + record["comparison"]["status"] + ". Supporting evidence only; user review is not scientific validation.",
            "private_note": ""}


def validate_records(records: list, source, originals: dict | None = None) -> None:
    if not isinstance(records, list) or len(records) > 20:
        raise ValueError("At most 20 saved upload versions per analysis")
    if originals is not None and set(originals) != {r["id"] for r in records}:
        raise ValueError("Original upload inventory mismatch")
    seen = {}
    replaced = set()
    required = {"version", "parser", "original_sha256", "normalized_sha256", "station", "location", "input_unit", "normalized_unit", "provider", "observation_basis", "rationale", "reference_station", "relationship", "daily_confirmed", "snapshot_sha256", "observations", "start", "end", "expected_days", "valid_days", "missing_days", "scenario_ids", "supersedes", "role", "comparison", "id"}
    for record in records:
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError("Custom evidence fields mismatch")
        if record["input_unit"] not in ("mm", "inches") or record["relationship"] not in ("same_station", "regional_proxy", "not_established") or type(record["daily_confirmed"]) is not bool:
            raise ValueError("Invalid custom unit or review declaration")
        if any(not isinstance(record[k], str) or not record[k].strip() or len(record[k]) > 2000 for k in ("station", "location", "provider", "observation_basis", "rationale")):
            raise ValueError("Invalid custom source metadata")
        if record["role"] != "supporting comparison; not a numerical rainfall driver":
            raise ValueError("Unsupported custom data role")
        if not isinstance(record["scenario_ids"], list) or not record["scenario_ids"] or any(not isinstance(i, str) for i in record["scenario_ids"]) or record["scenario_ids"] != sorted(set(record["scenario_ids"])):
            raise ValueError("Invalid custom scenario links")
        if record.get("version") != "custom-rainfall-1" or record.get("parser") != "rainfall-csv-v1":
            raise ValueError("Unsupported custom rainfall version")
        if record["snapshot_sha256"] != source.manifest["sha256"] or record["normalized_unit"] != "mm":
            raise ValueError("Custom reference snapshot or unit mismatch")
        if not re.fullmatch(r"[0-9a-f]{64}", record["original_sha256"]):
            raise ValueError("Invalid original byte hash")
        observations = record["observations"]
        if not observations or len(observations) > 250000:
            raise ValueError("Invalid normalized observations")
        if any(not isinstance(row, list) or len(row) != 2 or not isinstance(row[0], str) for row in observations):
            raise ValueError("Invalid normalized row")
        days = [date.fromisoformat(row[0]) for row in observations]
        if (days[-1] - days[0]).days >= 250000 or all(row[1] is None for row in observations):
            raise ValueError("Invalid normalized date span or empty observations")
        if any(row[0] != day.isoformat() for row, day in zip(observations, days)):
            raise ValueError("Custom dates must use YYYY-MM-DD")
        if days != sorted(set(days)):
            raise ValueError("Custom dates must be distinct and chronological")
        for row in observations:
            if len(row) != 2 or (row[1] is not None and (type(row[1]) not in (float, int) or not math.isfinite(row[1]) or row[1] < 0)):
                raise ValueError("Invalid normalized precipitation")
        preview = RainfallPreview(record["station"], record["location"], record["input_unit"], record["original_sha256"], tuple((d, row[1]) for d, row in zip(days, observations)))
        expected = {**record, "normalized_sha256": digest(observations), "start": str(days[0]), "end": str(days[-1]),
                    "expected_days": preview.expected_days, "valid_days": preview.valid_days, "missing_days": preview.missing_days,
                    "comparison": comparison_record(preview, source, record["reference_station"], record["relationship"], record["daily_confirmed"])}
        expected.pop("id")
        if record != {**expected, "id": "custom-" + digest(expected)} or record["id"] in seen:
            raise ValueError("Custom evidence hash or replay mismatch")
        previous = record["supersedes"]
        if previous and (previous not in seen or previous in replaced or seen[previous]["scenario_ids"] != record["scenario_ids"]):
            raise ValueError("Invalid custom evidence version chain")
        if previous:
            replaced.add(previous)
        if originals is not None:
            try:
                raw = base64.b64decode(originals[record["id"]], validate=True)
            except (ValueError, TypeError) as error:
                raise ValueError("Invalid saved original bytes") from error
            parsed = preview_rainfall(raw, record["station"], record["location"], record["input_unit"])
            if parsed != preview:
                raise ValueError("Original bytes disagree with normalized upload")
        seen[record["id"]] = record


def active_ids(records: list) -> set[str]:
    replaced = {r["supersedes"] for r in records}
    return {r["id"] for r in records if r["id"] not in replaced}


def validate_links(records, refs, evidence, scenarios) -> None:
    active = active_ids(records)
    registry = {r["id"]: r for r in records}
    evidence_by_id = {e["id"]: e for e in evidence}
    for record in records:
        if not set(record["scenario_ids"]) <= set(refs):
            raise ValueError("Custom upload links unknown scenarios")
        actual = dict(evidence_by_id.get(record["id"], {}))
        actual.setdefault("private_note", "")
        if actual != evidence_record(record):
            raise ValueError("Custom evidence description differs from saved data")
    for scenario in scenarios:
        wanted = sorted(i for i in active if scenario.id in registry[i]["scenario_ids"])
        actual = sorted(i for i in refs[scenario.id] if i.startswith("custom-"))
        if actual != wanted:
            raise ValueError("Custom scenario evidence links mismatch")
        events = [e for e in scenario.history if e["action"] == "custom evidence changed"]
        prior = set()
        for event in events:
            ids = event["custom_ids"]
            if ids != sorted(set(ids)) or any(i not in registry or scenario.id not in registry[i]["scenario_ids"] for i in ids):
                raise ValueError("Custom evidence audit references mismatch")
            added = set(ids) - prior
            removed = prior - set(ids)
            if len(added) != 1:
                raise ValueError("Custom evidence audit must add exactly one reviewed version")
            added_record = registry[next(iter(added))]
            expected_removed = {added_record["supersedes"]} if added_record["supersedes"] else set()
            if removed != expected_removed or (expected_removed and not expected_removed <= prior):
                raise ValueError("Custom evidence audit version transition mismatch")
            prior = set(ids)
        if wanted and (not events or events[-1]["custom_ids"] != wanted):
            raise ValueError("Custom evidence changed without invalidating review")
