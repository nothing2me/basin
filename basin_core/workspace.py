from __future__ import annotations

from dataclasses import asdict
import json
import base64
import os
from pathlib import Path
import platform
import time
import uuid

import pandas as pd
import psutil

from basin_core.analysis import DEFAULT_WEIGHTS, ScenarioClusterer, WeightedSumRanking, shortlist
from basin_core.data import CachedSource, ROOT
from basin_core.engine import Reference, Scenario, ScenarioGenerator, ScenarioParams, utc_now
from basin_core.evidence import initial_evidence, public_copy, validate_evidence
from basin_core.integrity import reconstruct_audit, check_digest
from basin_core.custom_data import build_record, evidence_record, validate_records, validate_links


SESSION_DIR_ENV = "BASIN_SESSION_DIR"


def session_dir() -> Path:
    """Directory holding saved analyses.

    Redirectable through BASIN_SESSION_DIR so tests never read or write the real
    ``local/`` sessions on a developer's machine.
    """
    override = os.environ.get(SESSION_DIR_ENV)
    return Path(override) if override else ROOT / "local"


class Workspace:
    def __init__(self, source: CachedSource, params: ScenarioParams, size=6):
        wall, cpu = time.perf_counter(), time.process_time()
        self.id = uuid.uuid4().hex[:12]
        self.created_at = utc_now()
        self.source = source
        self.params = params
        generator = ScenarioGenerator(source, params)
        self.reference = generator.reference
        self.scenarios, self.generation = generator.generate()
        self.weights = dict(DEFAULT_WEIGHTS)
        self.clustering = ScenarioClusterer().fit(self.scenarios, size)
        WeightedSumRanking().apply(self.scenarios, self.weights)
        self.selected = shortlist(self.scenarios, min(size, len(self.scenarios)))
        self.selection_history = [{"at": utc_now(), "action": "initial", "selected": self.selected.copy(), "weights": self.weights.copy()}]
        self.selection_history[0]["reasons"] = self._selection_reasons()
        self.evidence = initial_evidence(source)
        self.evidence_refs = {s.id: [e["id"] for e in self.evidence] for s in self.scenarios}
        self.conflicts = []
        self.evidence_history = []
        self.comparisons = []
        self.custom_uploads = []
        self.custom_originals = {}
        elapsed = time.perf_counter() - wall
        self.footprint = {"wall_seconds": elapsed, "cpu_seconds": time.process_time() - cpu,
                          "process_rss_mib_at_end": psutil.Process().memory_info().rss / 1024**2,
                          "network_policy": "No network calls in the pipeline implementation; offline rehearsal separately blocks Python sockets. This is not network instrumentation.",
                          "energy_wh_range": [elapsed * 15 / 3600, elapsed * 65 / 3600],
                          "energy_method": "Illustrative whole-laptop 15–65 W × elapsed seconds / 3600; not a power measurement; excludes idle, setup, development and embodied impacts.",
                          "water_footprint": "Not quantified; electricity supply and embodied water data unavailable.",
                          "python": platform.python_version()}
        self.notes = ""

    def get(self, identifier):
        for scenario in self.scenarios:
            if scenario.id == identifier:
                return scenario
        raise ValueError(f"Unknown scenario: {identifier}")

    def rerank(self, weights: dict):
        previous = self.weights.copy()
        WeightedSumRanking().apply(self.scenarios, weights)
        self.weights = dict(weights)
        if previous != self.weights:
            self.selection_history.append({"at": utc_now(), "action": "weights changed", "before": previous,
                                           "after": self.weights.copy(), "selected": self.selected.copy()})

    def add_evidence(self, record, scenario_ids):
        records = self.evidence + [dict(record)]
        refs = {k: v.copy() for k, v in self.evidence_refs.items()}
        if not scenario_ids or not set(scenario_ids) <= set(refs):
            raise ValueError("Choose existing scenarios to attach the evidence")
        for identifier in scenario_ids:
            refs[identifier].append(record["id"])
        validate_evidence(records, refs, self.conflicts, refs)
        self.evidence, self.evidence_refs = records, refs
        self.evidence_history.append({"at": utc_now(), "action": "add evidence", "record": dict(record), "scenario_ids": list(scenario_ids)})

    def save_custom_upload(self, raw: bytes, *, reviewed: bool, **metadata):
        if reviewed is not True:
            raise ValueError("Confirm review and local storage before saving")
        record = build_record(raw, self.source, **metadata)
        if record["id"] in {r["id"] for r in self.custom_uploads}:
            raise ValueError("This exact reviewed upload is already saved")
        records = self.custom_uploads + [record]
        originals = {**self.custom_originals, record["id"]: base64.b64encode(raw).decode("ascii")}
        if sum(len(value) for value in originals.values()) > 40_000_000:
            raise ValueError("Saved originals exceed this analysis's 30 MB storage budget")
        if len(json.dumps(records, allow_nan=False)) > 40_000_000:
            raise ValueError("Normalized upload evidence exceeds the 40 MB analysis budget")
        validate_records(records, self.source, originals)
        refs = {k: v.copy() for k, v in self.evidence_refs.items()}
        for identifier in record["scenario_ids"]:
            self.get(identifier)
            if record["supersedes"]:
                refs[identifier].remove(record["supersedes"])
            refs[identifier].append(record["id"])
        evidence = self.evidence + [evidence_record(record)]
        validate_evidence(evidence, refs, self.conflicts, refs)
        self.custom_uploads, self.custom_originals = records, originals
        self.evidence, self.evidence_refs = evidence, refs
        for identifier in record["scenario_ids"]:
            scenario = self.get(identifier)
            scenario.revision += 1
            scenario.status, scenario.approved_revision = "unreviewed", None
            scenario.history.append({"at": utc_now(), "action": "custom evidence changed",
                                     "revision": scenario.revision, "series_sha256": scenario.digest(),
                                     "custom_ids": sorted(i for i in refs[identifier] if i.startswith("custom-"))})
        self.evidence_history.append({"at": utc_now(), "action": "save custom upload", "id": record["id"], "supersedes": record["supersedes"]})
        return record["id"]

    def add_conflict(self, left_id, right_id, disagreement, comparability, private_note=""):
        conflict = {"id": "conflict-" + uuid.uuid4().hex[:12], "left_id": left_id, "right_id": right_id,
                    "disagreement": disagreement, "comparability": comparability,
                    "status": "unresolved", "resolution": "", "private_note": private_note}
        validate_evidence(self.evidence, self.evidence_refs, self.conflicts + [conflict], self.evidence_refs)
        self.conflicts.append(conflict)
        self.evidence_history.append({"at": utc_now(), "action": "add conflict", "record": conflict.copy()})
        return conflict["id"]

    def resolve_conflict(self, identifier, resolution, resolved=False):
        matches = [c for c in self.conflicts if c["id"] == identifier]
        if not matches or not resolution.strip():
            raise ValueError("Choose a conflict and enter a public disposition")
        previous = matches[0].copy()
        updated = {**previous, "resolution": resolution, "status": "resolved" if resolved else "unresolved"}
        conflicts = [updated if c["id"] == identifier else c for c in self.conflicts]
        validate_evidence(self.evidence, self.evidence_refs, conflicts, self.evidence_refs)
        self.conflicts = conflicts
        self.evidence_history.append({"at": utc_now(), "action": "conflict disposition", "before": previous, "after": updated.copy()})

    def compare_weights(self, weights, save_result=False):
        from copy import copy
        candidates = [copy(s) for s in self.scenarios if s.status != "rejected"]
        WeightedSumRanking().apply(candidates, weights)
        current = sorted(candidates, key=lambda s: (-self.get(s.id).score, s.id))
        alternate = sorted(candidates, key=lambda s: (-s.score, s.id))
        positions = {s.id: i + 1 for i, s in enumerate(current)}
        alternate_ids = shortlist(candidates, min(len(self.selected), len(candidates))) if candidates else []
        result = {"at": utc_now(), "weights_before": self.weights.copy(), "weights_after": dict(weights),
                  "selected_before": self.selected.copy(), "suggested_after": alternate_ids,
                  "pool": {s.id: {"revision": s.revision, "series_sha256": s.digest()} for s in candidates},
                  "rows": [{"id": s.id, "rank_before": positions[s.id], "rank_after": i + 1,
                            "score_before": self.get(s.id).score, "score_after": s.score,
                            "selected_before": s.id in self.selected, "suggested_after": s.id in alternate_ids}
                           for i, s in enumerate(alternate)]}
        if save_result:
            self.comparisons.append(result)
        return result

    def rebuild_shortlist(self):
        self.selected = shortlist([s for s in self.scenarios if s.status != "rejected"], min(len(self.selected), sum(s.status != "rejected" for s in self.scenarios)))
        self.selection_history.append({"at": utc_now(), "action": "rebuild", "weights": self.weights.copy(), "selected": self.selected.copy(), "reasons": self._selection_reasons()})

    def _selection_reasons(self):
        eligible = sorted([s for s in self.scenarios if s.status != "rejected"], key=lambda s: (-s.score, s.id))
        leaders = {}
        for s in eligible:
            leaders.setdefault(s.cluster, s.id)
        return {i: ("Group representative at selection" if i in leaders.values() else "Global score fill at selection") for i in self.selected}

    def selection_reason(self, identifier):
        if identifier not in self.selected:
            return "Outside current shortlist"
        for event in reversed(self.selection_history):
            if event["action"] == "manual swap" and event["new"] == identifier:
                return "Manual choice replacing " + event["old"]
            if event["action"] in ("initial", "rebuild"):
                return event.get("reasons", {}).get(identifier, "Saved selection; original rationale unavailable")
        return "Original rationale unavailable"

    def swap(self, old: str, new: str):
        if old not in self.selected or new in self.selected or self.get(new).status == "rejected":
            raise ValueError("Choose an eligible candidate outside the shortlist")
        self.selected[self.selected.index(old)] = new
        self.selection_history.append({"at": utc_now(), "action": "manual swap", "old": old, "new": new, "selected": self.selected.copy()})

    def edit(self, identifier, note, factor=None, replacement=None):
        self.get(identifier).edit(self.reference, note, factor, replacement)
        self.clustering = ScenarioClusterer().fit(self.scenarios, self.clustering["groups"])
        self.rerank(self.weights)

    def exportable(self):
        validate_records(self.custom_uploads, self.source)
        validate_links(self.custom_uploads, self.evidence_refs, self.evidence, self.scenarios)
        if len(self.selected) != len(set(self.selected)):
            raise ValueError("Duplicate shortlist entries")
        chosen = [self.get(i) for i in self.selected]
        accepted = [s for s in chosen if s.status == "accepted" and s.approved_revision == s.revision]
        if not chosen or any(s.status == "unreviewed" or (s.status == "accepted" and s.approved_revision != s.revision) for s in chosen):
            raise ValueError("Review every shortlisted revision before exporting")
        if not accepted:
            raise ValueError("Accept at least one scenario before exporting")
        for s in accepted:
            self.reference.features(s.series)
            approvals = [e for e in s.history if e["action"] == "accepted"]
            if not approvals or approvals[-1]["series_sha256"] != s.digest():
                raise ValueError("Approved rainfall changed; review the current revision again")
        return accepted

    def record(self, include_notes=False, include_series=False, include_custom=False):
        validate_evidence(self.evidence, self.evidence_refs, self.conflicts, [s.id for s in self.scenarios])
        if self.custom_uploads and not include_custom:
            raise ValueError("Explicit consent is required to include custom numerical data and source metadata")
        validate_records(self.custom_uploads, self.source)
        validate_links(self.custom_uploads, self.evidence_refs, self.evidence, self.scenarios)
        result = {"schema_version": "2.1" if self.custom_uploads else "2.0", "id": self.id, "created_at": self.created_at,
                  "snapshot_sha256": self.source.manifest["sha256"], "params": asdict(self.params),
                  "weights": self.weights, "selected": self.selected, "generation": self.generation,
                  "clustering": self.clustering, "footprint": self.footprint, "selection_history": self.selection_history,
                  "scenarios": [s.record(include_notes, include_series) for s in self.scenarios]}
        result.update(evidence=self.evidence, evidence_refs=self.evidence_refs, conflicts=self.conflicts,
                      evidence_history=self.evidence_history, comparisons=self.comparisons)
        if self.custom_uploads:
            result["custom_uploads"] = self.custom_uploads
        if include_notes:
            result["provider_notes"] = self.notes
        return public_copy(result, include_notes)

    def save(self, directory=None):
        directory = Path(directory) if directory is not None else session_dir()
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"session-{self.id}.json"
        temporary = target.with_suffix(".tmp")
        record = self.record(True, True, include_custom=True)
        if self.custom_uploads:
            validate_records(self.custom_uploads, self.source, self.custom_originals)
            record["custom_originals"] = self.custom_originals
        temporary.write_text(json.dumps(record, allow_nan=False), encoding="utf-8")
        # Append-only event snapshots avoid silently erasing review history between saves.
        audit = directory / f"audit-{self.id}.jsonl"
        with audit.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"at": utc_now(), "selected": self.selected, "weights": self.weights,
                                     "review": [s.record(True) for s in self.scenarios if s.history]}, allow_nan=False) + "\n")
        # Publish the session only after the audit append succeeds. A failed
        # append must not replace the last successfully saved analysis.
        temporary.replace(target)
        return target

    @classmethod
    def load(cls, source, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data["schema_version"] not in ("1.0", "2.0", "2.1") or data["snapshot_sha256"] != source.manifest["sha256"]:
            raise ValueError("Saved session uses a different snapshot or schema")
        obj = cls.__new__(cls)
        obj.source = source
        legacy = data["schema_version"] == "1.0"
        obj.params, obj.reference, obj.scenarios = reconstruct_audit(source, data, legacy=legacy)
        for field in ["id", "created_at", "weights", "selected", "generation", "clustering", "footprint", "selection_history"]:
            setattr(obj, field, data[field])
        obj.custom_uploads = data.get("custom_uploads", [])
        obj.custom_originals = data.get("custom_originals", {})
        validate_records(obj.custom_uploads, source, obj.custom_originals)
        obj.notes = data.get("provider_notes", "")
        for record, scenario in zip(data["scenarios"], obj.scenarios):
            frame = pd.DataFrame(record["values"], index=pd.to_datetime(record["dates"]), columns=record["stations"])
            if list(frame.columns) != obj.reference.stations or not frame.index.equals(scenario.series.index):
                raise ValueError("Saved dates or stations disagree with source history")
            check_digest(record["series_sha256"], frame, "Saved rainfall", legacy)
        obj.evidence = data["evidence"] if not legacy else initial_evidence(source)
        obj.evidence_refs = data["evidence_refs"] if not legacy else {s.id: [e["id"] for e in obj.evidence] for s in obj.scenarios}
        obj.conflicts = data.get("conflicts", [])
        obj.evidence_history = data.get("evidence_history", [])
        obj.comparisons = data.get("comparisons", [])
        if legacy:
            obj.clustering = ScenarioClusterer().fit(obj.scenarios, obj.clustering["groups"])
            obj.evidence_history.append({"at": utc_now(), "action": "migrate session 1.0 to 2.0", "review_status": "New evidence remains provisional"})
        return obj
