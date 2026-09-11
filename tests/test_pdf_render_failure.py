"""Renderer selection, failure and degraded-output disclosure for PDF export.

BASIN can render its executive brief two ways: a headless system browser converting
BASIN's HTML report to PDF, or BASIN's own pure-Python vector renderer. Both produce the
complete report. ``generate_pdf_report_with_status``/``generate_pdf_report`` never attempt
the browser path on Windows (unverified end-to-end on the presentation laptop; see
``_render_pdf_with_status`` for the platforms that do use it) and disclose that explicitly
rather than silently. These tests exercise ``_render_pdf_with_status`` directly -- with a
mocked browser binary and mocked subprocess, so no real browser process is spawned and the
platform this happens to run on does not matter -- to cover the working, missing, crashing,
timing-out and empty-output browser paths, and confirm private-note consent still holds no
matter which renderer produced the bytes. No real browser is required to run this file.
"""
import subprocess
from pathlib import Path

import pytest

import basin_core.pdf_report as pdf_report
from basin_core.pdf_report import (
    RenderOutcome,
    generate_pdf_report,
    generate_pdf_report_with_status,
    resolve_config,
)


@pytest.fixture
def approved(workspace):
    for identifier in workspace.selected:
        workspace.get(identifier).review(True, "Accepted for renderer-failure test")
    return workspace


def render_with_status(workspace, accepted, include_notes=False):
    """Call the platform-agnostic renderer-selection core directly.

    Bypasses the Windows disclosure branch in the public entry points so the browser-path
    behavior below is exercised (and tested) regardless of which OS runs the suite.
    """
    return pdf_report._render_pdf_with_status(workspace, accepted, include_notes, resolve_config(None))


# --------------------------------------------------------------------------------------
# Public entry points: the disclosed, explicit Windows behavior
# --------------------------------------------------------------------------------------

def test_windows_entry_point_uses_vector_renderer_and_discloses_why(approved, monkeypatch):
    monkeypatch.setattr(pdf_report.sys, "platform", "win32")
    outcome = generate_pdf_report_with_status(approved, approved.exportable())

    assert isinstance(outcome, RenderOutcome)
    assert outcome.renderer == "vector_fallback"
    assert outcome.degraded is False
    assert "system browser is not used" in outcome.detail
    assert outcome.pdf_bytes.startswith(b"%PDF-")


def test_non_windows_entry_point_delegates_to_the_browser_selection_logic(approved, monkeypatch):
    monkeypatch.setattr(pdf_report.sys, "platform", "linux")
    monkeypatch.setattr(pdf_report, "find_browser_executable", lambda: None)
    outcome = generate_pdf_report_with_status(approved, approved.exportable())

    assert outcome.renderer == "vector_fallback"
    assert outcome.degraded is False
    assert "No Chromium-based browser" in outcome.detail


def test_generate_pdf_report_wrapper_still_returns_bytes_only(approved, monkeypatch):
    """Existing callers of the bytes-only entry point are unaffected by the new status type."""
    monkeypatch.setattr(pdf_report.sys, "platform", "win32")
    pdf_bytes = generate_pdf_report(approved, approved.exportable())

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_output_path_write_failure_is_not_swallowed(approved, monkeypatch, tmp_path):
    """A failing disk write must raise, never be reported as a saved file."""
    monkeypatch.setattr(pdf_report.sys, "platform", "win32")

    def _raise_oserror(self, data):
        raise OSError("synthetic disk full")

    monkeypatch.setattr(Path, "write_bytes", _raise_oserror)

    with pytest.raises(OSError):
        generate_pdf_report_with_status(
            approved, approved.exportable(), output_path=tmp_path / "out.pdf"
        )


# --------------------------------------------------------------------------------------
# Browser renderer selection core: available, missing, crashing, timing out, empty output
# --------------------------------------------------------------------------------------

def test_no_browser_found_uses_vector_renderer_undegraded(approved, monkeypatch):
    monkeypatch.setattr(pdf_report, "find_browser_executable", lambda: None)
    outcome = render_with_status(approved, approved.exportable())

    assert outcome.renderer == "vector_fallback"
    assert outcome.degraded is False  # no browser present is a normal, expected path
    assert "No Chromium-based browser" in outcome.detail
    assert outcome.pdf_bytes.startswith(b"%PDF-")


def test_missing_browser_binary_falls_back_and_is_marked_degraded(approved, monkeypatch):
    """find_browser_executable claims a path, but launching it fails (moved/deleted binary)."""
    monkeypatch.setattr(pdf_report, "find_browser_executable", lambda: r"C:\does\not\exist\msedge.exe")
    outcome = render_with_status(approved, approved.exportable())

    assert outcome.renderer == "vector_fallback"
    assert outcome.degraded is True
    assert "browser renderer" in outcome.detail.lower()
    assert "failed" in outcome.detail.lower()
    assert outcome.pdf_bytes.startswith(b"%PDF-")
    # The fallback must still be a complete, readable report, not a truncated stub.
    assert len(outcome.pdf_bytes) > 1000


def test_browser_nonzero_exit_falls_back_and_is_marked_degraded(approved, monkeypatch):
    monkeypatch.setattr(pdf_report, "find_browser_executable", lambda: "fake-browser")

    class _Result:
        returncode = 1
        stderr = b"synthetic renderer crash"

    monkeypatch.setattr(pdf_report.subprocess, "run", lambda *a, **k: _Result())
    outcome = render_with_status(approved, approved.exportable())

    assert outcome.renderer == "vector_fallback"
    assert outcome.degraded is True
    assert "synthetic renderer crash" in outcome.detail
    assert outcome.pdf_bytes.startswith(b"%PDF-")


def test_browser_timeout_falls_back_and_is_marked_degraded(approved, monkeypatch):
    monkeypatch.setattr(pdf_report, "find_browser_executable", lambda: "fake-browser")

    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="fake-browser", timeout=15)

    monkeypatch.setattr(pdf_report.subprocess, "run", _raise_timeout)
    outcome = render_with_status(approved, approved.exportable())

    assert outcome.renderer == "vector_fallback"
    assert outcome.degraded is True
    assert outcome.pdf_bytes.startswith(b"%PDF-")


def test_browser_produces_no_usable_file_falls_back_and_is_marked_degraded(approved, monkeypatch):
    """The subprocess exits cleanly but never wrote a real PDF (e.g. a broken profile)."""
    monkeypatch.setattr(pdf_report, "find_browser_executable", lambda: "fake-browser")

    class _Result:
        returncode = 0
        stderr = b""

    monkeypatch.setattr(pdf_report.subprocess, "run", lambda *a, **k: _Result())
    outcome = render_with_status(approved, approved.exportable())

    assert outcome.renderer == "vector_fallback"
    assert outcome.degraded is True
    assert "did not produce a usable pdf" in outcome.detail.lower()


def test_successful_browser_render_is_reported_as_such(approved, monkeypatch):
    """A working browser path is labelled 'browser', not silently treated as the fallback."""
    monkeypatch.setattr(pdf_report, "find_browser_executable", lambda: "fake-browser")
    fake_pdf_bytes = b"%PDF-1.4\n%fake-browser-output\n" + b"x" * 2000

    def _fake_run(cmd, capture_output=True, timeout=None):
        print_arg = next(a for a in cmd if a.startswith("--print-to-pdf="))
        out_path = print_arg.split("=", 1)[1]
        Path(out_path).write_bytes(fake_pdf_bytes)

        class _Result:
            returncode = 0
            stderr = b""

        return _Result()

    monkeypatch.setattr(pdf_report.subprocess, "run", _fake_run)
    outcome = render_with_status(approved, approved.exportable())

    assert outcome.renderer == "browser"
    assert outcome.degraded is False
    assert outcome.pdf_bytes == fake_pdf_bytes


# --------------------------------------------------------------------------------------
# Consent must hold regardless of which renderer actually ran
# --------------------------------------------------------------------------------------

def test_private_notes_stay_opt_in_through_a_degraded_fallback(approved, monkeypatch):
    """Consent gating must hold even when the browser renderer failed and BASIN fell back."""
    for identifier in approved.selected:
        approved.get(identifier).review(True, "PRIVATE-SENTINEL")
    accepted = approved.exportable()
    monkeypatch.setattr(pdf_report, "find_browser_executable", lambda: r"C:\does\not\exist\msedge.exe")

    excluded = render_with_status(approved, accepted, include_notes=False)
    included = render_with_status(approved, accepted, include_notes=True)

    assert excluded.degraded is True and included.degraded is True
    assert b"PRIVATE-SENTINEL" not in excluded.pdf_bytes
    assert b"PRIVATE-SENTINEL" in included.pdf_bytes


def test_private_notes_stay_opt_in_through_a_mocked_successful_browser_render(approved, monkeypatch):
    """Consent gating must hold on the browser path too, not just the vector fallback."""
    for identifier in approved.selected:
        approved.get(identifier).review(True, "PRIVATE-SENTINEL")
    accepted = approved.exportable()

    monkeypatch.setattr(pdf_report, "find_browser_executable", lambda: "fake-browser")

    def _fake_run(cmd, capture_output=True, timeout=None):
        html_path = cmd[-1]
        print_arg = next(a for a in cmd if a.startswith("--print-to-pdf="))
        out_path = print_arg.split("=", 1)[1]
        # "Render" by writing the actual generated HTML bytes so the consent check is real.
        Path(out_path).write_bytes(Path(html_path).read_bytes() + b"\n%%padding%%" + b"x" * 2000)

        class _Result:
            returncode = 0
            stderr = b""

        return _Result()

    monkeypatch.setattr(pdf_report.subprocess, "run", _fake_run)

    excluded = render_with_status(approved, accepted, include_notes=False)
    included = render_with_status(approved, accepted, include_notes=True)

    assert excluded.renderer == "browser" and included.renderer == "browser"
    assert b"PRIVATE-SENTINEL" not in excluded.pdf_bytes
    assert b"PRIVATE-SENTINEL" in included.pdf_bytes
