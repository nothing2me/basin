"""End-to-end checks that stale report artifacts cannot remain available in the app.

These drive the real Streamlit script, so they cover the wiring between the Review
controls, the shared experiment configuration and the export/preview caches.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from basin_core.pdf_report import ExperimentConfig

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app(tmp_path, monkeypatch):
    """An app with three accepted scenarios, sitting on the Exports page."""
    from basin_core.workspace import Workspace

    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    at.sidebar.radio[0].set_value("Workspace").run()
    next(b for b in at.button if b.label == "Create rainfall scenarios").click().run()

    workspace = at.session_state.workspace
    at.sidebar.radio[0].set_value("Review").run()
    for identifier in list(workspace.selected):
        next(s for s in at.selectbox if s.label == "Scenario").set_value(identifier).run()
        next(b for b in at.button if b.label == "Include this revision in handoff").click().run()
    at.sidebar.radio[0].set_value("Exports").run()
    assert not at.exception
    return at


def prep_preview(at):
    next(b for b in at.button if "Prep PDF Preview" in b.label).click().run()
    assert not at.exception
    return at.session_state["preview_pdf"]


def preview_download_offered(at) -> bool:
    return any("Download PDF Preview" in b.label for b in at.download_button)


def test_review_settings_become_the_shared_configuration(app):
    """The Review controls, not hard-coded defaults, define the report configuration."""
    app.sidebar.radio[0].set_value("Review").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    assert not app.exception

    app.selectbox(key="review_initial_storage").set_value("35% (illustrative)").run()
    app.select_slider(key="review_conservation").set_value(30).run()
    app.checkbox(key="review_pipeline_active").set_value(False).run()
    assert not app.exception

    config = app.session_state["experiment_config"]
    assert config.selected is True
    assert config.initial_pct == pytest.approx(0.35)
    assert config.conservation_pct == pytest.approx(0.30)
    assert config.pipeline_active is False
    assert config.scenario_id == app.session_state.inspect_id


def test_configuration_defaults_are_explicit_before_any_experiment(app):
    """With no Review experiment the export page states a default, not a past run."""
    assert "experiment_config" not in app.session_state
    assert any("Reports use BASIN's documented defaults" in i.value for i in app.info)


def test_changing_experiment_settings_drops_a_prepared_preview(app):
    prepared = prep_preview(app)
    assert preview_download_offered(app)

    app.sidebar.radio[0].set_value("Review").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    app.selectbox(key="review_initial_storage").set_value("60% (illustrative)").run()
    app.sidebar.radio[0].set_value("Exports").run()
    assert not app.exception

    # The stale bytes are gone, not merely hidden behind a changed key.
    assert "preview_pdf" not in app.session_state
    assert not preview_download_offered(app)
    assert any("Prep PDF Preview" in b.label for b in app.button)

    refreshed = prep_preview(app)
    assert refreshed["token"] != prepared["token"]
    assert refreshed["bytes"] != prepared["bytes"]


def test_changing_note_consent_drops_a_prepared_preview(app):
    prep_preview(app)
    assert preview_download_offered(app)

    app.checkbox(key=f"share_notes_{app.session_state.workspace.id}").set_value(True).run()
    assert not app.exception
    assert "preview_pdf" not in app.session_state
    assert not preview_download_offered(app)


def test_editing_a_scenario_drops_a_prepared_preview(app):
    prep_preview(app)
    assert preview_download_offered(app)

    app.sidebar.radio[0].set_value("Review").run()
    next(t for t in app.text_area if t.label == "Review note").set_value("Check a drier sequence").run()
    next(b for b in app.button if b.label == "Apply multiplier").click().run()
    app.sidebar.radio[0].set_value("Exports").run()
    assert not app.exception

    assert "preview_pdf" not in app.session_state
    assert not preview_download_offered(app)


def test_built_export_is_discarded_when_settings_change(app):
    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    packet = app.session_state.packet
    assert packet["report"]["verified"]
    # No Review experiment has been configured yet, so it records the explicit default.
    assert packet["config"] == ExperimentConfig().fingerprint()
    assert any("Download Executive Brief (PDF)" in b.label for b in app.download_button)

    app.sidebar.radio[0].set_value("Review").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    app.select_slider(key="review_conservation").set_value(20).run()
    app.sidebar.radio[0].set_value("Exports").run()
    assert not app.exception

    assert "packet" not in app.session_state
    assert not any("Download Executive Brief (PDF)" in b.label for b in app.download_button)
    assert any("Rebuild the verified export" in i.value for i in app.info)


def test_exported_pdf_uses_the_selected_settings(app):
    app.sidebar.radio[0].set_value("Review").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    app.selectbox(key="review_initial_storage").set_value("35% (illustrative)").run()
    app.select_slider(key="review_conservation").set_value(30).run()
    app.sidebar.radio[0].set_value("Exports").run()
    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception

    pdf_bytes = app.session_state.packet["pdf_bytes"]
    assert b"35% of combined capacity" in pdf_bytes
    assert b"30% demand reduction" in pdf_bytes
    assert b"Selected in Review" in pdf_bytes
    assert b"48% of combined capacity" not in pdf_bytes


def test_same_revision_note_change_invalidates_preview(app):
    w = app.session_state.workspace
    app.checkbox(key=f"share_notes_{w.id}").set_value(True).run()
    prep_preview(app)
    scenario = w.get(w.selected[0])
    revision = scenario.revision
    scenario.review(True, "Updated consented note without numerical edits")
    assert scenario.revision == revision
    app.run()
    assert not app.exception
    assert "preview_pdf" not in app.session_state


def test_weight_change_invalidates_preview(app):
    prep_preview(app)
    app.session_state.workspace.rerank({"severity": 100, "duration": 0, "concurrence": 0, "season": 0})
    app.run()
    assert not app.exception
    assert "preview_pdf" not in app.session_state


def test_new_workspace_discards_previous_experiment(app):
    from basin_core.workspace import Workspace
    old = app.session_state.workspace
    app.session_state["experiment_config"] = ExperimentConfig(initial_pct=0.35, selected=True)
    prep_preview(app)
    replacement = Workspace(old.source, old.params, 3)
    app.session_state.workspace = replacement
    app.run()
    assert not app.exception
    assert "experiment_config" not in app.session_state
    assert "preview_pdf" not in app.session_state


def test_no_accepted_scenarios_discards_prepared_preview(app):
    prep_preview(app)
    w = app.session_state.workspace
    for sid in w.selected:
        w.get(sid).review(False, "Remove from report")
    app.run()
    assert not app.exception
    assert "preview_pdf" not in app.session_state


def test_review_settings_survive_navigation(app):
    app.sidebar.radio[0].set_value("Review").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    app.selectbox(key="review_initial_storage").set_value("35% (illustrative)").run()
    app.select_slider(key="review_conservation").set_value(30).run()
    app.checkbox(key="review_pipeline_active").set_value(False).run()
    app.sidebar.radio[0].set_value("Exports").run()
    app.sidebar.radio[0].set_value("Review").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    assert not app.exception
    config = app.session_state["experiment_config"]
    assert config.initial_pct == pytest.approx(0.35)
    assert config.conservation_pct == pytest.approx(0.30)
    assert config.pipeline_active is False


def test_hiding_experiment_preserves_report_configuration(app):
    app.sidebar.radio[0].set_value("Review").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    app.selectbox(key="review_initial_storage").set_value("35% (illustrative)").run()
    app.select_slider(key="review_conservation").set_value(20).run()
    app.checkbox(key="review_pipeline_active").set_value(False).run()
    configured = app.session_state.experiment_config

    app.toggle(key="storage_experiment").set_value(False).run()
    assert not app.exception
    assert app.session_state.experiment_config == configured
    app.sidebar.radio[0].set_value("Exports").run()
    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    assert app.session_state.packet["config"] == configured.fingerprint()
    assert b"35% of combined capacity" in app.session_state.packet["pdf_bytes"]

    app.sidebar.radio[0].set_value("Review").run()
    app.toggle(key="storage_experiment").set_value(True).run()
    assert not app.exception
    assert app.selectbox(key="review_initial_storage").value == "35% (illustrative)"
    assert app.select_slider(key="review_conservation").value == 20
    assert app.checkbox(key="review_pipeline_active").value is False


def test_export_reports_which_renderer_produced_the_pdf(app):
    """On this platform BASIN's built-in renderer runs; the export flow discloses that."""
    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    packet = app.session_state.packet
    assert packet["pdf_renderer"] == "vector_fallback"
    assert packet["pdf_degraded"] is False
    assert any("PDF renderer:" in c.value for c in app.caption)


def test_export_surfaces_a_degraded_browser_fallback_to_the_user(app, monkeypatch):
    """A browser found but failing to render must show a visible warning, not a quiet swap."""
    import basin_core.pdf_report as pdf_report

    real_generate = pdf_report.generate_pdf_report_with_status

    def _forced_degraded(workspace, accepted, **kwargs):
        outcome = real_generate(workspace, accepted, **kwargs)
        return pdf_report.RenderOutcome(
            pdf_bytes=outcome.pdf_bytes,
            renderer="vector_fallback",
            degraded=True,
            detail="synthetic forced fallback for the app-level UI test",
        )

    # app.py imports this name at module load time, so patch the module attribute it
    # re-reads on every Streamlit script rerun rather than mutating global interpreter state.
    monkeypatch.setattr(pdf_report, "generate_pdf_report_with_status", _forced_degraded)

    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    packet = app.session_state.packet
    assert packet["pdf_renderer"] == "vector_fallback"
    assert packet["pdf_degraded"] is True
    assert any("PDF renderer fallback" in w.value for w in app.warning)
    # The fallback PDF must still be the complete, valid report, not an empty/broken file.
    assert packet["pdf_bytes"].startswith(b"%PDF-")
    assert len(packet["pdf_bytes"]) > 1000


def test_revoking_note_consent_removes_sentinel_from_a_rebuilt_pdf(app):
    """Consent revocation must actually remove private content from the next real export."""
    w = app.session_state.workspace
    scenario = w.get(w.selected[0])
    scenario.review(True, "PRIVATE-DEMO-SENTINEL")

    app.checkbox(key=f"share_notes_{w.id}").set_value(True).run()
    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    assert b"PRIVATE-DEMO-SENTINEL" in app.session_state.packet["pdf_bytes"]

    # Revoke consent: the stale (notes-included) packet must be dropped, not merely hidden.
    app.checkbox(key=f"share_notes_{w.id}").set_value(False).run()
    assert not app.exception
    assert "packet" not in app.session_state
    assert not any("Download Executive Brief (PDF)" in b.label for b in app.download_button)

    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    assert b"PRIVATE-DEMO-SENTINEL" not in app.session_state.packet["pdf_bytes"]
