from copy import deepcopy
import json
import base64
import hashlib
import io
import zipfile

import pytest

from basin_core.custom_data import digest, validate_records
from basin_core.workspace import Workspace
from basin_core.exporter import export_bundle, verify_bundle

RAW = b"date,precipitation\n2024-01-01,1\n2024-01-02,2\n2024-01-04,\n"


def attach(w, raw=RAW, **changes):
    values = dict(reviewed=True, station="Local gauge", location="Example town", unit="mm",
                  provider="Example provider", observation_basis="Daily window uncertain",
                  reference_station="USW00012924", relationship="regional_proxy", daily_confirmed=True,
                  rationale="Regional context only; catchment suitability remains uncertain",
                  scenario_ids=w.selected[:1])
    values.update(changes)
    return w.save_custom_upload(raw, **values)


def accept_all(w):
    for identifier in w.selected:
        w.get(identifier).review(True)


def test_save_restore_originals_and_comparison(workspace, tmp_path):
    accept_all(workspace)
    old = workspace.get(workspace.selected[0]).digest()
    identifier = attach(workspace)
    record = workspace.custom_uploads[0]
    assert record["original_sha256"] == hashlib.sha256(RAW).hexdigest()
    assert record["comparison"]["paired_days"] == 2
    assert record["comparison"]["upload_total_mm"] == 3
    assert record["missing_days"] == 2
    assert record["id"] in workspace.evidence_refs[workspace.selected[0]]
    assert workspace.get(workspace.selected[0]).status == "unreviewed"
    assert workspace.get(workspace.selected[1]).status == "accepted"
    assert workspace.get(workspace.selected[0]).digest() == old
    restored = Workspace.load(workspace.source, workspace.save(tmp_path))
    assert restored.custom_uploads == workspace.custom_uploads
    assert base64.b64decode(restored.custom_originals[identifier]) == RAW
    assert restored.get(workspace.selected[0]).status == "unreviewed"


def test_consent_and_replay(workspace):
    attach(workspace)
    accept_all(workspace)
    with pytest.raises(ValueError, match="consent"):
        export_bundle(workspace)
    workspace.notes = "PRIVATE NOTE"
    payload = export_bundle(workspace, include_custom=True)
    report = verify_bundle(payload)
    assert report["custom_comparisons_replayed"] == 1
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        audit = json.loads(z.read("audit.json"))
        assert audit["schema_version"] == "2.1"
        assert "custom_originals" not in audit
        assert "PRIVATE NOTE" not in z.read("audit.json").decode()
        assert audit["custom_uploads"][0]["observations"]


def test_replace_requires_review_and_keeps_history(workspace, tmp_path):
    first = attach(workspace)
    accept_all(workspace)
    second = attach(workspace, RAW.replace(b",2\n", b",4\n"), supersedes=first)
    assert second != first
    assert len(workspace.custom_uploads) == 2
    assert first not in workspace.evidence_refs[workspace.selected[0]]
    assert second in workspace.evidence_refs[workspace.selected[0]]
    with pytest.raises(ValueError, match="Review every"):
        export_bundle(workspace, include_custom=True)
    restored = Workspace.load(workspace.source, workspace.save(tmp_path))
    accept_all(restored)
    assert verify_bundle(export_bundle(restored, include_custom=True))["custom_comparisons_replayed"] == 2


def test_assumption_change_also_invalidates(workspace):
    first = attach(workspace)
    accept_all(workspace)
    attach(workspace, supersedes=first, rationale="Updated assessment: no catchment validation")
    assert workspace.get(workspace.selected[0]).approved_revision is None


def test_uncertain_relationship_can_be_saved_without_calculation(workspace):
    attach(workspace, relationship="not_established", daily_confirmed=False)
    assert workspace.custom_uploads[0]["comparison"]["status"] == "blocked"
    accept_all(workspace)
    assert verify_bundle(export_bundle(workspace, include_custom=True))["verified"]


def test_invalid_and_unreviewed_uploads_are_atomic(workspace):
    before = deepcopy(workspace.record(True, True))
    for changes in ({"reviewed": False}, {"rationale": ""}, {"scenario_ids": ["missing"]}, {"relationship": "guess"}):
        with pytest.raises(ValueError):
            attach(workspace, **changes)
        assert workspace.record(True, True) == before


@pytest.mark.parametrize("field,value", [("missing_days", 100), ("normalized_sha256", "0" * 64), ("snapshot_sha256", "0" * 64)])
def test_saved_metadata_tampering_rejected(workspace, tmp_path, field, value):
    attach(workspace)
    path = workspace.save(tmp_path)
    data = json.loads(path.read_text())
    data["custom_uploads"][0][field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        Workspace.load(workspace.source, path)


def test_original_bytes_tampering_rejected(workspace, tmp_path):
    identifier = attach(workspace)
    path = workspace.save(tmp_path)
    data = json.loads(path.read_text())
    data["custom_originals"][identifier] = base64.b64encode(b"other").decode()
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        Workspace.load(workspace.source, path)


def test_numerical_comparison_recomputed_not_trusted(workspace):
    attach(workspace)
    records = deepcopy(workspace.custom_uploads)
    records[0]["comparison"]["upload_total_mm"] = 999
    unsigned = {k: v for k, v in records[0].items() if k != "id"}
    records[0]["id"] = "custom-" + digest(unsigned)
    with pytest.raises(ValueError, match="replay mismatch"):
        validate_records(records, workspace.source)


def test_forged_links_cannot_bypass_approval(workspace):
    attach(workspace)
    accept_all(workspace)
    workspace.get(workspace.selected[0]).history = [e for e in workspace.get(workspace.selected[0]).history if e["action"] != "custom evidence changed"]
    with pytest.raises(ValueError):
        export_bundle(workspace, include_custom=True)


def test_inches_normalized_once(workspace, tmp_path):
    attach(workspace, unit="inches")
    assert workspace.custom_uploads[0]["comparison"]["upload_total_mm"] == pytest.approx(76.2)
    restored = Workspace.load(workspace.source, workspace.save(tmp_path))
    assert restored.custom_uploads == workspace.custom_uploads


def test_upload_ui_save_restore_and_export_consent(tmp_path, monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    monkeypatch.setattr(st, "file_uploader", lambda *args, **kwargs: io.BytesIO(RAW) if kwargs.get("key") == "local_rainfall_file" else None)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
    next(b for b in app.button if b.label == "Try an example").click().run()
    app.sidebar.radio[0].set_value("Data").run()
    app.text_input(key="local_station").set_value("Local gauge")
    app.text_input(key="local_location").set_value("Example town")
    app.selectbox(key="local_unit").set_value("mm").run()
    app.selectbox(key="upload_reference_station").set_value("USW00012924").run()
    # Uncertain relationship is preserved rather than forcing a fabricated confirmation.
    next(t for t in app.text_input if t.label == "Source / provider").set_value("Local provider")
    next(t for t in app.text_input if t.label == "Observation-day definition").set_value("Unknown daily boundary")
    next(t for t in app.text_area if t.label.startswith("Why this reference")).set_value("Provisional regional context")
    next(c for c in app.checkbox if c.label.startswith("I reviewed the upload")).check()
    next(b for b in app.button if b.label == "Save reviewed evidence").click().run()
    assert not app.exception
    w = app.session_state.workspace
    assert len(w.custom_uploads) == 1
    assert w.custom_uploads[0]["comparison"]["status"] == "blocked"
    assert any(x.label == "Saved upload version" for x in app.selectbox)
    restored = Workspace.load(w.source, tmp_path / f"session-{w.id}.json")
    assert restored.custom_uploads == w.custom_uploads
    accept_all(w)
    app.sidebar.radio[0].set_value("Exports").run()
    assert not app.exception
    assert next(b for b in app.button if b.label == "Build verified export").disabled
    next(c for c in app.checkbox if c.label.startswith("Include custom numerical inputs")).check().run()
    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    assert app.session_state.packet["report"]["custom_comparisons_replayed"] == 1
    next(c for c in app.checkbox if c.label.startswith("Include custom numerical inputs")).uncheck().run()
    assert not app.exception
    assert next(b for b in app.button if b.label == "Build verified export").disabled


def test_audit_failure_preserves_last_saved_session(workspace, tmp_path, monkeypatch):
    from pathlib import Path
    path = workspace.save(tmp_path)
    before = path.read_bytes()
    attach(workspace)
    original_open = Path.open
    def fail_audit(self, mode="r", *args, **kwargs):
        if self.name == f"audit-{workspace.id}.jsonl" and mode == "a":
            raise OSError("Disk unavailable")
        return original_open(self, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", fail_audit)
    with pytest.raises(OSError):
        workspace.save(tmp_path)
    assert path.read_bytes() == before
    assert Workspace.load(workspace.source, path).custom_uploads == []


def test_rehashed_bundle_cannot_forge_comparison(workspace):
    attach(workspace)
    accept_all(workspace)
    payload = export_bundle(workspace, include_custom=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        files = {name: z.read(name) for name in z.namelist()}
    audit = json.loads(files["audit.json"])
    audit["custom_uploads"][0]["comparison"]["difference_mm"] = 999999
    files["audit.json"] = json.dumps(audit).encode()
    manifest = json.loads(files["bundle_manifest.json"])
    manifest["files"]["audit.json"] = hashlib.sha256(files["audit.json"]).hexdigest()
    files["bundle_manifest.json"] = json.dumps(manifest).encode()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as z:
        for name, value in files.items():
            z.writestr(name, value)
    with pytest.raises(ValueError):
        verify_bundle(output.getvalue())


def test_unknown_extra_fields_rejected(workspace):
    attach(workspace)
    record = deepcopy(workspace.custom_uploads[0])
    record["original_filename"] = "must-not-leak.csv"
    with pytest.raises(ValueError, match="fields mismatch"):
        validate_records([record], workspace.source)


def test_replacing_superseded_version_fails_without_mutation(workspace):
    first = attach(workspace)
    attach(workspace, supersedes=first, rationale="Second review")
    before = deepcopy(workspace.record(True, True, include_custom=True))
    with pytest.raises(ValueError):
        attach(workspace, supersedes=first, rationale="Invalid branch")
    assert workspace.record(True, True, include_custom=True) == before
