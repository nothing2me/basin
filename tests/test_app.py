from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_full_user_workflow(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert "A clearer starting point" not in str(app.markdown)
    next(b for b in app.button if b.label == "Generate").click().run()
    assert not app.exception
    w = app.session_state.workspace
    assert len(w.scenarios) == 300
    app.sidebar.radio[0].set_value("Workspace").run()
    assert not app.exception
    preset_box = next((s for s in app.sidebar.selectbox if s.label == "Community priority preset"), None)
    if preset_box:
        preset_box.set_value("Rural Water District (Nueces County WCID #3)").run()
        assert app.session_state.workspace.weights["season"] == 50
    app.slider(key="weight_duration").set_value(80).run()
    assert app.session_state.workspace.weights["duration"] == 80
    app.sidebar.radio[0].set_value("Review").run()
    assert not app.exception
    series_radio = next((r for r in app.radio if "Cumulative rainfall" in r.options), None)
    if series_radio:
        series_radio.set_value("Reservoir simulation").run()
        assert not app.exception
        series_radio.set_value("Cumulative rainfall").run()
        assert not app.exception
    for identifier in list(w.selected):
        next(s for s in app.selectbox if s.label == "Scenario").set_value(identifier).run()
        next(b for b in app.button if b.label == "Accept").click().run()
        assert not app.exception
    app.sidebar.radio[0].set_value("Exports").run()
    next(b for b in app.button if b.label == "Build verified export").click().run()
    assert not app.exception
    assert app.session_state.packet["report"]["verified"]
    assert b"Hydrologist_Handoff_Brief.md" in app.session_state.packet["data"]
    app.sidebar.radio[0].set_value("Review").run()
    inspected = app.session_state.inspect_id
    next(t for t in app.text_area if t.label == "Review note").set_value("Check a drier daily sequence").run()
    next(b for b in app.button if b.label == "Apply multiplier").click().run()
    assert not app.exception
    assert app.session_state.workspace.get(inspected).status == "unreviewed"
    app.sidebar.radio[0].set_value("Exports").run()
    assert next(b for b in app.button if b.label == "Build verified export").disabled
    app.sidebar.radio[0].set_value("Data").run()
    assert not app.exception


def test_interactive_tutorial_walkthrough(tmp_path, monkeypatch):
    from basin_core.workspace import Workspace
    original_save = Workspace.save
    monkeypatch.setattr(Workspace, "save", lambda self: original_save(self, tmp_path))
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert "tutorial_active" not in app.session_state or not app.session_state["tutorial_active"]

    # Click "Start tutorial" in Settings menu
    start_btn = next(b for b in app.button if b.label == "Start tutorial")
    start_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_active is True
    assert app.session_state.tutorial_step == 0
    assert app.session_state.page == "Data"

    # Step through all 7 steps across the pipeline
    for step in range(1, 7):
        next_btn = next(b for b in app.button if b.label == "Next Step ▶")
        next_btn.click().run()
        assert not app.exception
        assert app.session_state.tutorial_step == step

    assert app.session_state.tutorial_step == 6
    assert app.session_state.page == "Exports"

    # Test Previous button
    prev_btn = next(b for b in app.button if b.label == "◀ Prev")
    prev_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_step == 5
    assert app.session_state.page == "Review"

    # Advance back to end and finish
    next_btn = next(b for b in app.button if b.label == "Next Step ▶")
    next_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_step == 6

    finish_btn = next(b for b in app.button if b.label == "✓ Finish Tutorial")
    finish_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_active is False

    # Verify we can restart anytime from Settings and exit early
    start_btn2 = next(b for b in app.button if b.label == "Start tutorial")
    start_btn2.click().run()
    assert not app.exception
    assert app.session_state.tutorial_active is True
    exit_btn = next(b for b in app.button if b.label == "✕ Exit")
    exit_btn.click().run()
    assert not app.exception
    assert app.session_state.tutorial_active is False

