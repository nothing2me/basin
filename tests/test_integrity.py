import io
import json
import hashlib
import zipfile

import numpy as np
import pandas as pd
import pytest

from basin_core.exporter import export_bundle, verify_bundle
from basin_core.workspace import Workspace


def rewrite_bundle(payload, mutate):
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    mutate(files)
    manifest = json.loads(files["bundle_manifest.json"])
    manifest["files"] = {name: hashlib.sha256(files[name]).hexdigest() for name in manifest["files"]}
    files["bundle_manifest.json"] = json.dumps(manifest).encode()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items(): archive.writestr(name, data)
    return output.getvalue()


@pytest.fixture
def approved(workspace):
    for identifier in workspace.selected:
        workspace.get(identifier).review(True)
    return workspace


@pytest.mark.parametrize("case", ["missing audit", "duplicate audit", "approval digest", "approval missing", "revision sequence", "selected mismatch", "snapshot mismatch", "score", "components", "duplicate accepted", "schema", "evidence link", "private note"])
def test_rehashed_inconsistent_audit_is_rejected(approved, case):
    payload = export_bundle(approved)
    def mutate(files):
        audit = json.loads(files["audit.json"])
        manifest = json.loads(files["bundle_manifest.json"])
        record = next(s for s in audit["scenarios"] if s["id"] == approved.selected[0])
        if case == "missing audit": audit["scenarios"].remove(record)
        elif case == "duplicate audit": audit["scenarios"].append(record)
        elif case == "approval digest": record["history"][-1]["series_sha256"] = "0" * 64
        elif case == "approval missing": record["history"] = []
        elif case == "revision sequence": record["history"][-1]["revision"] += 1
        elif case == "selected mismatch": audit["selected"] = audit["selected"][1:]
        elif case == "snapshot mismatch": audit["snapshot_sha256"] = "0" * 64
        elif case == "score": record["score"] = -999
        elif case == "components": record["components"]["severity"] = -999
        elif case == "duplicate accepted": manifest["accepted_ids"].append(manifest["accepted_ids"][0])
        elif case == "schema": manifest["schema_version"] = "1.0"
        elif case == "evidence link": audit["evidence_refs"][record["id"]].append("missing-evidence")
        elif case == "private note": audit["evidence"][0]["private_note"] = "SECRET"
        files["audit.json"] = json.dumps(audit).encode()
        files["bundle_manifest.json"] = json.dumps(manifest).encode()
    with pytest.raises(ValueError):
        verify_bundle(rewrite_bundle(payload, mutate))


@pytest.mark.parametrize("case", ["summary", "date", "station", "units", "rainfall", "brief"])
def test_rehashed_csv_and_brief_inconsistency(approved, case):
    def mutate(files):
        if case == "brief":
            files["Hydrologist_Handoff_Brief.md"] += b"\nUnsupported additional claim"
            return
        name = "shortlist.csv" if case == "summary" else "daily_rainfall.csv"
        frame = pd.read_csv(io.BytesIO(files[name]))
        if case == "summary": frame["priority_score"] = -999
        elif case == "date": frame["date"] = (pd.to_datetime(frame.date) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
        elif case == "station": frame["station_id"] = "other-station"
        elif case == "units": frame["units"] = "in/day"
        elif case == "rainfall": frame.loc[0, "precip_mm"] += 1
        files[name] = frame.to_csv(index=False).encode()
    with pytest.raises(ValueError):
        verify_bundle(rewrite_bundle(export_bundle(approved), mutate))


def test_complete_history_evidence_privacy_and_roundtrip(workspace, tmp_path):
    s = workspace.get(workspace.selected[0])
    workspace.edit(s.id, "PRIVATE-SENTINEL", factor=.8)
    workspace.edit(s.id, "PRIVATE-SENTINEL", replacement=s.series * .9)
    record = {**workspace.evidence[1], "id": "alternative-assumption", "title": "Reviewer question",
              "description": "A competing assumption for this exercise; no source endorsement.", "private_note": "PRIVATE-SENTINEL"}
    workspace.add_evidence(record, [s.id])
    conflict = workspace.add_conflict("station-suitability", record["id"], "Suitability remains unknown", "No common spatial weighting or validation", "PRIVATE-SENTINEL")
    workspace.resolve_conflict(conflict, "Ask the recipient to assess geographic suitability", resolved=False)
    workspace.rerank({"severity": 80, "duration": 80, "concurrence": 10, "season": 10})
    for i in workspace.selected: workspace.get(i).review(True, "PRIVATE-SENTINEL")
    workspace.get(workspace.selected[-1]).review(False, "PRIVATE-SENTINEL")
    workspace.compare_weights({"severity": 1, "duration": 0, "concurrence": 0, "season": 0}, save_result=True)
    restored = Workspace.load(workspace.source, workspace.save(tmp_path))
    assert restored.conflicts == workspace.conflicts
    assert restored.evidence_history == workspace.evidence_history
    assert restored.comparisons == workspace.comparisons
    payload = export_bundle(restored)
    report = verify_bundle(payload)
    assert report["scenarios_replayed"] == 2
    assert report["audit_records_replayed"] == len(workspace.scenarios)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        assert all(b"PRIVATE-SENTINEL" not in z.read(n) for n in z.namelist())
        brief = z.read("Hydrologist_Handoff_Brief.md").decode()
        assert "unresolved" in brief and "Ask the recipient" in brief
        assert "44.4% (raw weight 80)" in brief
    with zipfile.ZipFile(io.BytesIO(export_bundle(restored, True))) as z:
        assert b"PRIVATE-SENTINEL" in z.read("audit.json")


@pytest.mark.parametrize("mutation", ["missing field", "invalid URL", "missing link", "invalid resolved", "unsupported schema"])
def test_invalid_saved_evidence_rejected(workspace, tmp_path, mutation):
    path = workspace.save(tmp_path)
    saved = json.loads(path.read_text())
    if mutation == "missing field": del saved["evidence"][0]["publisher"]
    elif mutation == "invalid URL": saved["evidence"][0]["source_locator"] = "javascript:alert(1)"
    elif mutation == "missing link": saved["evidence_refs"][workspace.selected[0]] = ["unknown"]
    elif mutation == "invalid resolved":
        saved["conflicts"] = [{"id": "c", "left_id": "station-suitability", "right_id": "ranking-assumption", "disagreement": "test", "comparability": "test", "status": "resolved", "resolution": ""}]
    else: saved["schema_version"] = "999"
    path.write_text(json.dumps(saved))
    with pytest.raises(ValueError): Workspace.load(workspace.source, path)


def test_legacy_session_migration_preserves_reviews(approved, tmp_path):
    data = approved.record(True, True)
    data["schema_version"] = "1.0"
    for field in ("evidence", "evidence_refs", "conflicts", "evidence_history", "comparisons"): data.pop(field)
    # Legacy saves used the caller's index name in the rainfall hash.
    for record in data["scenarios"]:
        frame = approved.get(record["id"]).series.rename_axis(None)
        digest = hashlib.sha256(frame.to_csv(float_format="%.12g", lineterminator="\n").encode()).hexdigest()
        record["series_sha256"] = digest
        for event in record["history"]: event["series_sha256"] = digest
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(data))
    restored = Workspace.load(approved.source, path)
    assert restored.record()["schema_version"] == "2.0"
    assert verify_bundle(export_bundle(restored))["verified"]


def test_weight_preview_preserves_reviewed_pool(approved, tmp_path):
    before = [(s.id, s.digest(), s.score, s.cluster, s.status) for s in approved.scenarios]
    selected = approved.selected.copy()
    weights = approved.weights.copy()
    rejected = next(s for s in approved.scenarios if s.id not in selected)
    rejected.review(False, "Exclude from preview")
    before = [(s.id, s.digest(), s.score, s.cluster, s.status) for s in approved.scenarios]
    result = approved.compare_weights({"severity": 0, "duration": 100, "concurrence": 0, "season": 0}, True)
    assert rejected.id not in result["pool"]
    assert before == [(s.id, s.digest(), s.score, s.cluster, s.status) for s in approved.scenarios]
    assert approved.selected == selected and approved.weights == weights
    approved.rerank({"severity": 0, "duration": 100, "concurrence": 0, "season": 0})
    event = approved.selection_history[-1]
    assert event["before"] == weights and event["after"] == approved.weights
    assert approved.selected == selected
    assert Workspace.load(approved.source, approved.save(tmp_path)).comparisons == approved.comparisons
