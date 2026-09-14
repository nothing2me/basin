import io
import json
import zipfile

import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest

from basin_core.analysis_context import AnalysisContext, REGION_N_COUNTIES
from basin_core.exporter import export_bundle, verify_bundle
from basin_core.pdf_report import build_fallback_pdf, render_html_report
from basin_core.workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]


def specific_context():
    return AnalysisContext(
        scope="specific_provider",
        organization_type="municipality",
        organization_name="City of Alice",
        counties=("Jim Wells",),
        community="Alice service area",
        supply_relationship="mixed",
        decision_use="modeling_request",
    )


def test_specific_context_requires_a_named_owner_and_region_n_county():
    values = specific_context().record()
    values["organization_name"] = ""
    with pytest.raises(ValueError, match="city, provider"):
        AnalysisContext.from_record(values)

    values = specific_context().record()
    values["counties"] = ["Outside Region N"]
    with pytest.raises(ValueError, match="Region N counties"):
        AnalysisContext.from_record(values)


def test_context_round_trips_with_workspace_and_verified_handoff(workspace, tmp_path):
    context = specific_context()
    workspace.set_analysis_context(context)
    restored = Workspace.load(workspace.source, workspace.save(tmp_path))
    assert restored.analysis_context == context
    assert restored.selection_history[-1]["action"] == "analysis context changed"

    for identifier in restored.selected:
        restored.get(identifier).review(True, "Reviewed rainfall content for handoff")
    payload = export_bundle(restored)
    assert verify_bundle(payload)["verified"] is True
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        audit = json.loads(archive.read("audit.json"))
        brief = archive.read("Hydrologist_Handoff_Brief.md").decode()
    assert audit["analysis_context"] == context.record()
    assert "## Intended decision context" in brief
    assert "City of Alice" in brief
    assert "Jim Wells" in brief
    assert "does not select representative gauges" in brief

    accepted = restored.exportable()
    html = render_html_report(restored, accepted)
    pdf = build_fallback_pdf(restored, accepted)
    assert "Prepared for:</strong> City of Alice" in html
    assert "Jim Wells" in html
    assert b"Prepared for: City of Alice" in pdf
    assert b"does not select representative gauges" in pdf


def test_older_saved_run_without_context_loads_as_explicit_region_wide(workspace, tmp_path):
    record = workspace.record(include_series=True)
    record.pop("analysis_context")
    path = tmp_path / "pre-context.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    restored = Workspace.load(workspace.source, path)
    assert restored.analysis_context.scope == "region_wide"
    assert restored.analysis_context.counties == REGION_N_COUNTIES


def test_specific_city_context_survives_data_to_builder_transition(tmp_path, monkeypatch):
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception

    app.radio(key="context_scope").set_value("Specific community or provider").run()
    assert app.selectbox(key="context_org_type").value == "municipality"
    assert app.selectbox(key="context_supply").value == "unknown"
    assert app.selectbox(key="context_decision").value == "modeling_request"
    accept = next(button for button in app.button if button.label.startswith("✅ Accept Baseline"))
    assert accept.disabled
    app.text_input(key="context_org_name").set_value("City of Alice").run()
    app.text_input(key="context_community").set_value("Alice service area").run()
    app.multiselect(key="context_counties").set_value(["Jim Wells"]).run()
    accept = next(button for button in app.button if button.label.startswith("✅ Accept Baseline"))
    assert not accept.disabled
    accept.click().run()
    assert app.session_state.page == "Workspace"

    next(button for button in app.button if button.label == "Create rainfall scenarios").click().run()
    context = app.session_state.workspace.analysis_context
    assert context.organization_name == "City of Alice"
    assert context.community == "Alice service area"
    assert context.counties == ("Jim Wells",)
