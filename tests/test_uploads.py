import hashlib

import pytest

from basin_core.uploads import TEMPLATE, preview_rainfall


def parse(raw, unit="mm"):
    return preview_rainfall(raw, "My gauge", "Local town", unit)


def test_preview_preserves_gaps_identity_and_original_hash():
    result = parse(TEMPLATE)
    assert result.expected_days == 4
    assert result.valid_days == 2
    assert result.missing_days == 2
    assert result.station == "My gauge"
    assert result.original_sha256 == hashlib.sha256(TEMPLATE).hexdigest()
    assert result.observations[-1][1] is None


def test_units_and_sorting_do_not_modify_original():
    raw = b"date,precipitation\n2024-02-29,1\n2024-02-28,0\n"
    result = parse(raw, "inches")
    assert result.observations[-1][1] == pytest.approx(25.4)
    assert result.expected_days == 2
    assert result.original_sha256 == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("row", ["2024-01-01,-1", "2024-01-01,nan", "2024-01-01,inf",
    "2024-01-01,1e999", "2024-01-01,no", "01/02/2024,1", "2024-02-30,1",
    "2024-01-01,1,2", "2024-01-01,1\n2024-01-01,1"])
def test_rejects_ambiguous_or_invalid_data(row):
    with pytest.raises(ValueError):
        parse(("date,precipitation\n" + row).encode())


@pytest.mark.parametrize("raw", [b"", b"date,precipitation\n", b"date,precipitation\n2024-01-01,",
    b"date,rain\n2024-01-01,1", b"\xff", b"date,precipitation\n\"unclosed"])
def test_rejects_empty_or_malformed_file(raw):
    with pytest.raises(ValueError):
        parse(raw)


def test_explicit_metadata_and_bounded_input(monkeypatch):
    with pytest.raises(ValueError):
        preview_rainfall(TEMPLATE, "", "Town", "mm")
    with pytest.raises(ValueError):
        parse(TEMPLATE, "unknown")
    monkeypatch.setattr("basin_core.uploads.MAX_BYTES", 4)
    with pytest.raises(ValueError, match="10 MB"):
        parse(TEMPLATE)


def test_row_and_calendar_limits(monkeypatch):
    monkeypatch.setattr("basin_core.uploads.MAX_ROWS", 2)
    with pytest.raises(ValueError, match="row limit"):
        parse(b"date,precipitation\n2024-01-01,1\n2024-01-02,1\n2024-01-03,1")
    with pytest.raises(ValueError, match="Date span"):
        parse(b"date,precipitation\n2024-01-01,1\n2024-01-04,1")


def test_preview_ui_does_not_create_or_modify_a_scenario(monkeypatch):
    import io
    from pathlib import Path
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    original = st.file_uploader
    payload = [TEMPLATE]

    def uploaded(label, *args, **kwargs):
        if label.startswith("Local observations CSV"):
            return io.BytesIO(payload[0]) if payload[0] is not None else None
        return original(label, *args, **kwargs)

    monkeypatch.setattr(st, "file_uploader", uploaded)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
    app.text_input(key="local_station").set_value("Private local gauge")
    app.text_input(key="local_location").set_value("My town")
    app.selectbox(key="local_unit").set_value("mm").run()
    assert not app.exception
    assert "workspace" not in app.session_state or app.session_state.workspace is None
    assert next(m for m in app.metric if m.label == "Missing rainfall days").value == "2"
    payload[0] = b"date,precipitation\n2026-01-01,-1"
    app.run()
    assert not app.exception
    assert any("nonnegative" in e.value for e in app.error)
    assert not any(m.label == "Missing rainfall days" for m in app.metric)
    payload[0] = None
    app.run()
    assert not app.exception
    assert not app.error
    assert "workspace" not in app.session_state or app.session_state.workspace is None
