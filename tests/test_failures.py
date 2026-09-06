import hashlib
import json
import socket

import pytest
from streamlit.testing.v1 import AppTest

from basin_core.data import CachedSource, ROOT
from basin_core.workspace import Workspace
from scripts.start_browser import find_port


@pytest.mark.parametrize("raw", [b"garbage\n", b"date,station_id,precip_mm\ninvalid,USW00012924,1\n", b"date,station_id,precip_mm\n2001-01-01,unknown,1\n"])
def test_malformed_snapshot_with_matching_hash(source, raw):
    manifest = {**source.manifest, "sha256": hashlib.sha256(raw).hexdigest()}
    with pytest.raises(ValueError): CachedSource(raw=raw, manifest=manifest)


def test_unavailable_and_invalid_session(source, workspace, tmp_path):
    with pytest.raises(OSError): Workspace.load(source, tmp_path / "missing.json")
    path = workspace.save(tmp_path)
    data = json.loads(path.read_text())
    data["scenarios"][0]["dates"][0] = "1990-01-01"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError): Workspace.load(source, path)


def test_failed_save_keeps_prior_session(workspace, tmp_path, monkeypatch):
    from pathlib import Path
    target = workspace.save(tmp_path)
    previous = target.read_bytes()
    def failed_replace(*args, **kwargs): raise PermissionError("Write denied by test")
    monkeypatch.setattr(Path, "replace", failed_replace)
    workspace.notes = "Unsaved note"
    with pytest.raises(PermissionError): workspace.save(tmp_path)
    assert target.read_bytes() == previous


def test_ui_failed_save_does_not_claim_success(tmp_path, monkeypatch):
    original = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    next(b for b in app.button if b.label == "Generate").click().run()
    def failed(*args, **kwargs): raise PermissionError("Test save denial")
    monkeypatch.setattr(Workspace, "save", failed)
    next(b for b in app.button if b.label == "Save notes").click().run()
    assert not app.exception
    assert any("Save failed" in e.value for e in app.error)
    assert not any("Saved locally" in str(t.value) for t in app.get("toast"))


def test_occupied_port_is_skipped_and_exhaustion_reported():
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        port = occupied.getsockname()[1]
        with pytest.raises(RuntimeError, match="No free local port"): find_port(port, 1)
        if port < 65535: assert find_port(port, 2) == port + 1


def test_evidence_conflict_ui_workflow(tmp_path, monkeypatch):
    original = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    next(b for b in app.button if b.label == "Generate").click().run()
    app.sidebar.radio[0].set_value("Review").run()
    next(t for t in app.text_input if t.label == "Public disagreement").set_value("Airport data may not represent the catchment")
    next(t for t in app.text_input if t.label.startswith("Public comparability limits")).set_value("Different spatial definitions")
    next(t for t in app.text_input if t.label.startswith("Private conflict annotation")).set_value("PRIVATE-SENTINEL")
    next(b for b in app.button if b.label == "Record unresolved disagreement").click().run()
    assert not app.exception
    w = app.session_state.workspace
    assert len(w.conflicts) == 1 and w.conflicts[0]["status"] == "unresolved"
    restored = Workspace.load(w.source, tmp_path / f"session-{w.id}.json")
    assert restored.conflicts == w.conflicts
    for identifier in w.selected:
        next(s for s in app.selectbox if s.label == "Scenario").set_value(identifier).run()
        next(b for b in app.button if b.label == "Accept").click().run()
    app.sidebar.radio[0].set_value("Exports").run()
    assert any("unresolved evidence" in e.value for e in app.warning)
    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    assert app.session_state.packet["report"]["verified"]
