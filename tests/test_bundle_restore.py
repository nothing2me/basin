import io
import pytest
from basin_core.data import CachedSource
from basin_core.workspace import Workspace
from basin_core.engine import ScenarioParams
from basin_core.exporter import export_bundle


def test_workspace_restore_from_bundle():
    source = CachedSource()
    params = ScenarioParams(tuple(source.daily.columns), (90, 180), (1, 4), 0.5, 0.8, 'All stations', 50, 22)
    w = Workspace(source, params, 3)
    for s_id in w.selected:
        w.get(s_id).review(True, 'Approved scenario for testing')
    w.notes = 'Operator bundle verification note'

    bundle_bytes = export_bundle(w, include_notes=True)
    assert len(bundle_bytes) > 0

    restored_w, verif = Workspace.restore_from_bundle(bundle_bytes, source)
    assert verif['verified'] is True
    assert verif['run_id'] == w.id
    assert verif['scenarios_replayed'] == 3
    assert restored_w.id == w.id
    assert len(restored_w.scenarios) == len(w.scenarios)
    assert restored_w.selected == w.selected
    assert restored_w.notes == 'Operator bundle verification note'
    assert restored_w.get(w.selected[0]).status == 'accepted'


def test_workspace_restore_tampered_bundle_fails():
    source = CachedSource()
    params = ScenarioParams(tuple(source.daily.columns), (90,), (1,), 0.5, 0.8, 'All stations', 10, 22)
    w = Workspace(source, params, 2)
    for s_id in w.selected:
        w.get(s_id).review(True, 'Note')
    bundle_bytes = export_bundle(w)

    tampered = bytearray(bundle_bytes)
    tampered[100] ^= 0xFF
    with pytest.raises(ValueError):
        Workspace.restore_from_bundle(bytes(tampered), source)
