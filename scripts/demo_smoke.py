"""Rehearse generation, review, edit, privacy-safe export and replay offline."""
from pathlib import Path
import json
import socket
import sys
import tempfile
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
        workspace.edit(first, "Rehearsal: replacement rainfall", replacement=workspace.get(first).series * .9)
        workspace.rerank({"severity": 70, "duration": 40, "concurrence": 20, "season": 10})
        assumption = {**workspace.evidence[1], "id": "rehearsal-assumption", "title": "Hypothetical catchment assumption for internal rehearsal",
                      "description": "For this internal exercise only, suppose the equal-station average represents catchment rainfall. This assumption has no validation.",
                      "review_status": "unreviewed", "private_note": "PRIVATE-REHEARSAL-SENTINEL"}
        workspace.add_evidence(assumption, [first])
        conflict = workspace.add_conflict("station-suitability", assumption["id"], "Catchment suitability is not established",
                                          "Station coordinates and catchment-mean rainfall are different spatial definitions", "PRIVATE-REHEARSAL-SENTINEL")
        workspace.resolve_conflict(conflict, "Keep unresolved for recipient review; internal rehearsal only")
        for identifier in workspace.selected:
            workspace.get(identifier).review(True, "Automated rehearsal approval, not practitioner validation")
        workspace.get(workspace.selected[-1]).review(False, "Automated rehearsal rejection")
        workspace.compare_weights({"severity": 10, "duration": 70, "concurrence": 20, "season": 0}, True)
        scratch = ROOT / "tmp"
        scratch.mkdir(exist_ok=True)
        save_dir = Path(tempfile.mkdtemp(prefix="rehearsal-session-", dir=scratch))
        workspace = Workspace.load(source, workspace.save(save_dir))
        bundle = export_bundle(workspace)
        report = verify_bundle(bundle)
        directory = ROOT / "output"
        directory.mkdir(exist_ok=True)
        (directory / "BASIN-rehearsal.zip").write_bytes(bundle)
        report["footprint"] = workspace.footprint
        report["comparison"] = comparison(workspace.scenarios, workspace.selected, workspace.params.seed)
        (directory / "rehearsal-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
