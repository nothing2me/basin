from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import platform
import time
import uuid

import pandas as pd
import psutil

from basin_core.analysis import DEFAULT_WEIGHTS, ScenarioClusterer, WeightedSumRanking, shortlist
from basin_core.data import CachedSource, ROOT
from basin_core.engine import Reference, Scenario, ScenarioGenerator, ScenarioParams, utc_now


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
        elapsed = time.perf_counter() - wall
        self.footprint = {"wall_seconds": elapsed, "cpu_seconds": time.process_time() - cpu,
                          "process_rss_mb_at_end": psutil.Process().memory_info().rss / 1024**2,
                          "scenario_pipeline_network_calls": 0, "cloud_inference_calls": 0,
                          "energy_wh_range": [elapsed * 15 / 3600, elapsed * 65 / 3600],
                          "energy_method": "Illustrative whole-laptop 15–65 W × elapsed seconds / 3600; not a power measurement; excludes idle, setup, development and embodied impacts.",
                          "water_footprint": "Not quantified; electricity supply and embodied water data unavailable.",
                          "python": platform.python_version()}
        self.notes = ""

    def get(self, identifier):
        return next(s for s in self.scenarios if s.id == identifier)

    def rerank(self, weights: dict):
        WeightedSumRanking().apply(self.scenarios, weights)
        self.weights = dict(weights)

    def rebuild_shortlist(self):
        self.selected = shortlist([s for s in self.scenarios if s.status != "rejected"], min(len(self.selected), sum(s.status != "rejected" for s in self.scenarios)))
        self.selection_history.append({"at": utc_now(), "action": "rebuild", "weights": self.weights.copy(), "selected": self.selected.copy()})

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

    def record(self, include_notes=False, include_series=False):
        result = {"schema_version": "1.0", "id": self.id, "created_at": self.created_at,
                  "snapshot_sha256": self.source.manifest["sha256"], "params": asdict(self.params),
                  "weights": self.weights, "selected": self.selected, "generation": self.generation,
                  "clustering": self.clustering, "footprint": self.footprint, "selection_history": self.selection_history,
                  "scenarios": [s.record(include_notes, include_series) for s in self.scenarios]}
        if include_notes:
            result["provider_notes"] = self.notes
        return result

    def save(self, directory=ROOT / "local"):
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"session-{self.id}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.record(True, True), allow_nan=False), encoding="utf-8")
        temporary.replace(target)
        # Append-only event snapshots avoid silently erasing review history between saves.
        audit = directory / f"audit-{self.id}.jsonl"
        with audit.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"at": utc_now(), "selected": self.selected, "weights": self.weights,
                                     "review": [s.record(True) for s in self.scenarios if s.history]}, allow_nan=False) + "\n")
        return target

    @classmethod
    def load(cls, source, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data["schema_version"] != "1.0" or data["snapshot_sha256"] != source.manifest["sha256"]:
            raise ValueError("Saved session uses a different snapshot or schema")
        obj = cls.__new__(cls)
        obj.source = source
        obj.params = ScenarioParams(**{**data["params"], "stations": tuple(data["params"]["stations"]),
                                      "months": tuple(data["params"]["months"]), "durations": tuple(data["params"]["durations"])})
        obj.params.validate()
        obj.reference = Reference(source, list(obj.params.stations))
        for field in ["id", "created_at", "weights", "selected", "generation", "clustering", "footprint", "selection_history"]:
            setattr(obj, field, data[field])
        obj.notes = data.get("provider_notes", "")
        obj.scenarios = []
        for record in data["scenarios"]:
            frame = pd.DataFrame(record["values"], index=pd.to_datetime(record["dates"]), columns=record["stations"])
            s = Scenario(record["id"], frame, record["provenance"], obj.reference)
            if s.digest() != record["series_sha256"]:
                raise ValueError("Saved rainfall checksum mismatch")
            for field in ["revision", "status", "approved_revision", "history", "cluster"]:
                setattr(s, field, record[field])
            s.cluster_name = record.get("cluster_name", f"Group {s.cluster}")
            obj.scenarios.append(s)
        obj.rerank(obj.weights)
        return obj
