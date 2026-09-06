"""Small, versioned evidence contract shared by sessions, UI and exports."""
from __future__ import annotations

import re
from urllib.parse import urlparse

KINDS = ("observation", "derived calculation", "user assumption", "policy statement")
STATUSES = ("unreviewed", "reviewed for this exercise", "provisional")


def initial_evidence(source):
    manifest = source.manifest
    common = {"source_date": manifest["end"], "retrieved_at": manifest["downloaded_at"],
              "geographic_scope": "Corpus Christi, Victoria and San Antonio station locations; catchments unvalidated",
              "review_status": "provisional", "private_note": ""}
    definitions = [
        ("noaa-snapshot", "NOAA daily precipitation snapshot", "NOAA NCEI", manifest["documentation"], "observation", "mm/day",
         f"1991–2025 PRCP observations. Version: {manifest['dataset_version'].strip()}. Snapshot SHA-256: {manifest['sha256']}. " + manifest["policy"]),
        ("station-suitability", "Provisional station suitability", "BASIN team", "docs/methodology.md", "user assumption", "",
         "Airport observations demonstrate the workflow. No catchment mapping, area weighting or practitioner suitability approval is established."),
        ("rainfall-method", "Constructed rainfall and measured deficit", "BASIN implementation", "docs/methodology.md", "derived calculation", "mm per station",
         "Synchronized complete whole historical windows; station rainfall is multiplied by retained fractions. Net station deficits are clipped at zero and averaged equally. This is not streamflow scaling."),
        ("matched-reference", "Matched rainfall reference and concurrence", "BASIN implementation", "docs/methodology.md", "derived calculation", "mm; fraction",
         "1991–2020 monthly mean daily climatology; matched onset/duration/stations with windows ending by 2015 and n>=5. Empirical percentile is not probability. Concurrence counts eligible 30-day windows; one station measures stress frequency."),
        ("ranking-assumption", "Illustrative ranking priorities", "BASIN team", "docs/methodology.md", "user assumption", "normalized weights",
         "Severity, duration, station stress and June–September timing use user weights. Presets are illustrative; no named provider endorsement or measured summer demand curve is established."),
    ]
    return [{**common, "id": i, "title": title, "publisher": publisher, "source_locator": locator,
             "kind": kind, "units": units, "description": description} for i, title, publisher, locator, kind, units, description in definitions]


def validate_evidence(records, references, conflicts, scenario_ids):
    if not isinstance(records, list) or not isinstance(conflicts, list) or not isinstance(references, dict):
        raise ValueError("Evidence, references and conflicts have invalid types")
    ids = set()
    fields = ("id", "title", "publisher", "source_locator", "source_date", "retrieved_at", "geographic_scope", "kind", "units", "description", "review_status")
    for record in records:
        if not isinstance(record, dict) or any(not isinstance(record.get(k), str) for k in fields):
            raise ValueError("Evidence record is missing required text fields")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", record["id"]) or record["id"] in ids:
            raise ValueError("Evidence IDs must be distinct and use letters, numbers, dots, underscores or hyphens")
        ids.add(record["id"])
        if any(not record[k].strip() for k in ("title", "publisher", "source_locator", "geographic_scope", "description")):
            raise ValueError("Evidence title, publisher, source, geography and description are required")
        locator = record["source_locator"]
        url = urlparse(locator)
        if not ((url.scheme in ("https", "http") and url.netloc) or re.fullmatch(r"docs/[A-Za-z0-9_-]+\.md", locator)):
            raise ValueError("Evidence source must be an HTTP(S) URL or a docs/*.md reference")
        if record["kind"] not in KINDS or record["review_status"] not in STATUSES:
            raise ValueError("Unsupported evidence kind or review status")
        if not isinstance(record.get("private_note", ""), str):
            raise ValueError("Private annotation must be text")
    if set(references) != set(scenario_ids):
        raise ValueError("Evidence references must cover exactly the scenario IDs")
    for refs in references.values():
        if not isinstance(refs, list) or not refs or any(not isinstance(i, str) for i in refs) or len(refs) != len(set(refs)) or not set(refs) <= ids:
            raise ValueError("Scenario evidence links must identify distinct existing records")
    conflict_ids = set()
    for conflict in conflicts:
        if not isinstance(conflict, dict) or any(not isinstance(conflict.get(k), str) for k in
                ("id", "left_id", "right_id", "disagreement", "comparability", "status", "resolution")):
            raise ValueError("Conflict is missing required text fields")
        if not conflict["id"] or conflict["id"] in conflict_ids:
            raise ValueError("Duplicate or empty conflict ID")
        conflict_ids.add(conflict["id"])
        if conflict["left_id"] == conflict["right_id"] or not {conflict["left_id"], conflict["right_id"]} <= ids:
            raise ValueError("A conflict must link two different existing evidence records")
        if not conflict["disagreement"].strip() or not conflict["comparability"].strip():
            raise ValueError("Describe the disagreement and comparability limits")
        if conflict["status"] not in ("unresolved", "resolved") or (conflict["status"] == "resolved" and not conflict["resolution"].strip()):
            raise ValueError("Resolved conflicts require a recorded human disposition")
        if not isinstance(conflict.get("private_note", ""), str):
            raise ValueError("Private annotation must be text")


def public_copy(value, include_notes=False):
    if isinstance(value, dict):
        return {k: public_copy(v, include_notes) for k, v in value.items()
                if include_notes or k not in ("private_note", "provider_notes")}
    if isinstance(value, list):
        return [public_copy(v, include_notes) for v in value]
    return value
