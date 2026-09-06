"""Rehearse generation, review, edit, privacy-safe export and replay offline."""
from pathlib import Path
import json
import socket
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from basin_core.data import CachedSource, ROOT
from basin_core.engine import ScenarioParams
from basin_core.exporter import export_bundle, verify_bundle
from basin_core.workspace import Workspace
from basin_core.analysis import comparison

if __name__ == "__main__":
    with patch.object(socket, "create_connection", side_effect=AssertionError("Offline rehearsal attempted a network connection")), patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")):
        source = CachedSource()
        workspace = Workspace(source, ScenarioParams(tuple(source.daily.columns), candidates=500))
        first = workspace.selected[0]
        workspace.get(first).review(True, "Initial selection for rehearsal")
        workspace.edit(first, "Rehearsal: examine reduced rainfall", factor=0.75)
        assert workspace.get(first).status == "unreviewed"
        for identifier in workspace.selected:
            workspace.get(identifier).review(True, "Automated rehearsal approval, not practitioner validation")
        bundle = export_bundle(workspace)
        report = verify_bundle(bundle)
        directory = ROOT / "output"
        directory.mkdir(exist_ok=True)
        (directory / "BASIN-rehearsal.zip").write_bytes(bundle)
        report["footprint"] = workspace.footprint
        report["comparison"] = comparison(workspace.scenarios, workspace.selected, workspace.params.seed)
        (directory / "rehearsal-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
