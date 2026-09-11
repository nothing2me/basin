# Task 3 handoff — PDF renderer failure/degraded-output handling and cross-output consent

Worktree: `C:\Users\moham\Documents\GitHub\basin-pdf-failures`
Branch: `task/pdf-report-failure-handling`
Base: `origin/main` at `0b3d9031b89674ef7279381284a70edb06f850bb` (not merged, not pushed)

Scope actually completed: the remaining part of B17.3 (renderer-failure/degraded-output
handling and disclosure) and B17.4's cross-output consent checks (private-note and
custom-data consent verified consistently across the ZIP and both PDF renderers, plus
consent revocation). Did not touch the already-complete PDF content/layout work, and did
not touch `docs/report_device_acceptance.md`'s manual device-check items — those remain
manual as instructed.

## What changed

### `basin_core/pdf_report.py`

- New `RenderOutcome` frozen dataclass: `pdf_bytes`, `renderer` (`"browser"` or
  `"vector_fallback"`), `degraded` (bool), `detail` (human-readable explanation).
- New `_render_pdf_with_status(workspace, accepted, include_notes, config)`: the actual
  renderer-selection core. Tries `find_browser_executable()`; if none is found, uses the
  vector renderer and reports `degraded=False` (no browser present is a normal, expected
  state, not a failure). If a browser is found, it runs headless print-to-pdf and now
  explicitly checks the subprocess exit code and the output file's existence/size before
  trusting it; any of those failing, or the process erroring/timing out, falls back to the
  vector renderer with `degraded=True` and a `detail` string naming what failed. Both
  renderers produce the complete report (this was already true — see B17.3's earlier HTML
  parity work); only the disclosure is new.
- Bumped the browser subprocess timeout from 2 seconds to `BROWSER_RENDER_TIMEOUT_S = 15`.
  The old value was measured shorter than a real render on this dev machine (~1.3s for a
  full report with a real installed Edge, timed directly before making this change — see
  commands below), so it would have turned a working browser into a reported "failure" on
  any load at all. This only matters on the non-Windows path today (see below) but keeps
  the number honest if that ever changes.
- New `generate_pdf_report_with_status(...)`: the public entry point returning
  `RenderOutcome`. **On `sys.platform == "win32"` it still does not attempt the browser
  path** — see "Deliberately not changed" below — and returns an explicit, disclosed
  `vector_fallback` outcome (`degraded=False`) saying so. On other platforms it delegates
  to `_render_pdf_with_status`. Writing to `output_path` is unchanged in effect (still just
  `Path.write_bytes`, so a disk-write failure still raises `OSError` rather than being
  swallowed) but now happens after the outcome is built so the exception can't be mistaken
  for a render failure.
- `generate_pdf_report(...)` (the pre-existing bytes-only function) is now a thin wrapper
  around `generate_pdf_report_with_status(...).pdf_bytes`, so every existing caller and test
  that only wanted bytes keeps working unchanged.

### `app.py`

- Both call sites (`Build verified export` and `Prep PDF Preview`) now call
  `generate_pdf_report_with_status` instead of `generate_pdf_report`.
- The built packet's session-state dict carries `pdf_renderer`, `pdf_degraded`,
  `pdf_render_detail` alongside `pdf_bytes`; the preview dict carries `degraded`/`detail`.
- Next to the PDF download button: a `st.caption` naming the renderer when not degraded, or
  a `st.warning` with the fallback detail when it is. The preview download button gets the
  same warning caption when degraded.
- No other export/report logic was touched. The existing "Verified Export Package Ready"
  success message and the download-card wording that already scopes SHA-256 verification to
  the ZIP only (not the PDF) were left exactly as they were — confirmed by grep that no
  "cryptographically verified" claim about the PDF exists anywhere in `app.py`.

### Tests (all new files/additions; nothing removed)

- `tests/test_pdf_render_failure.py` (12 tests): exercises `_render_pdf_with_status`
  directly (bypassing the Windows disclosure branch so the logic is tested regardless of
  which OS runs the suite) for: no browser found, browser path found but binary
  missing/unlaunchable, non-zero exit code, timeout, empty/undersized output file, and a
  genuine success path (all via a mocked `subprocess.run`, no real browser spawned). Also
  covers the public entry points' Windows-disclosure behavior, the bytes-only wrapper, an
  `OSError` on `output_path` write not being swallowed, and that private-note consent holds
  through both a degraded fallback and a mocked successful browser render.
- `tests/test_cross_output_consent.py` (3 tests): builds one workspace with both a private
  review-note sentinel and a custom rainfall upload, then checks the ZIP
  (`export_bundle`), the HTML report and the vector PDF all honor `include_notes` the same
  way; confirms original custom-upload bytes never reach the ZIP (by design, per B14) or
  either PDF path, and that omitting custom consent blocks export outright rather than
  silently stripping the data; and confirms revoking consent and rebuilding actually removes
  the sentinel from every output rather than leaving it in a cached artifact.
- `tests/test_report_invalidation_app.py` (+3 tests, real `AppTest`-driven Streamlit runs):
  the built packet reports `pdf_renderer`/`pdf_degraded` and the export page shows the
  renderer caption; a forced-degraded render (monkeypatching
  `basin_core.pdf_report.generate_pdf_report_with_status`, re-picked up because `app.py`
  re-imports it on every Streamlit script rerun) produces a visible `st.warning` and a
  still-valid, still-complete fallback PDF; and toggling the notes-consent checkbox off
  after a consented export, then rebuilding, actually removes the sentinel from the new PDF
  bytes (not just from a hidden/stale download).

## Deliberately not changed: the win32 browser-render skip

`generate_pdf_report_with_status` still never attempts the headless-browser path on
Windows — same as before this task, and called out as an open item in the September 9 task
3 checkpoint in `HANDOFF.md` ("the win32 guard ... still makes that path unreachable in the
product").

I looked at removing it and decided against it, and want that decision visible rather than
silently re-applied. Reasoning, with evidence from this session:

- I measured a real headless Edge print-to-pdf render of BASIN's actual HTML report on this
  Windows dev machine: **1.28 s** (`msedge.exe --headless=new --disable-gpu
  --no-pdf-header-footer --print-to-pdf=...`, timed directly, output discarded afterward —
  not part of the committed diff). That confirms the old 2-second timeout was already too
  tight, which is why I raised it — but it also means enabling this path on Windows would,
  for the first time, spawn a real browser subprocess during automated test runs whenever a
  developer's or CI machine happens to have Edge/Chrome installed.
- Several existing tests (e.g. `tests/test_report_invalidation_app.py::
  test_exported_pdf_uses_the_selected_settings`, `tests/test_pdf_report.py::
  test_generate_pdf_report`) assert literal byte substrings against the PDF that
  `generate_pdf_report`/`generate_pdf_report_with_status` returns. Those assertions were
  written against the vector renderer's uncompressed content stream. A real headless-browser
  PDF typically stores its content as a compressed stream, so those literal-substring
  assertions could start failing — not because anything is wrong with the report, but
  because the byte layout changed under them. I did not want to make that call unilaterally
  days before a presentation, or rewrite a large set of already-reviewed tests to
  accommodate a rendering path nobody has verified end-to-end on the actual presentation
  laptop.
- The task instructions ask me to test failure/success paths with isolated fixtures, not to
  re-verify the actual device. Flipping this on Windows would be a real, user-visible
  product behavior change with no device verification behind it — squarely the kind of
  thing `docs/report_device_acceptance.md` says must be checked on the actual laptop first.

What I did instead: kept today's known-good Windows behavior (vector renderer, always), but
made it an explicit, disclosed `RenderOutcome` rather than a silent path, and built the full
try/select/fail/fall-back logic (`_render_pdf_with_status`) so it is implemented and
thoroughly tested for whichever platform actually uses it. If the team wants real
headless-browser rendering attempted on Windows, that's a follow-up decision that should
come with (a) a laptop timing check, and (b) updating the tests above to extract text rather
than search compressed bytes, or to force the vector path where exact byte content is
being asserted. I have not done either, so I'm not enabling it.

## B17.4: what "cross-output consent" checks actually cover here

The existing CLI harness (`scripts/hydrologist_harness.py`) only produces the ZIP, and its
consent-flag forwarding was already tested (`tests/test_security.py::
test_cli_export_consent_defaults_and_opt_ins`, `test_cli_passes_consent_to_exporter`) —
argument-passing only, not real data flow. I did not add PDF generation to the CLI (not
asked for, and it would be new scope); instead `tests/test_cross_output_consent.py` verifies
real sentinel data flows correctly through the actual outputs BASIN does produce today: the
ZIP and both PDF renderers.

One thing learned while writing this: `include_custom=False` on `export_bundle`/
`workspace.record` does not silently drop custom data when a custom upload exists — it
raises `ValueError` and blocks export entirely (already-existing behavior, from B14/SEC.2).
My test asserts that explicitly rather than assuming silent exclusion.

## Commands run and results (this session, worktree above, Windows, `basin/.venv`'s Python
3.12.14 interpreter run against this worktree's checkout)

```
git rev-parse origin/main
# 0b3d9031b89674ef7279381284a70edb06f850bb

git worktree add -b task/pdf-report-failure-handling ../basin-pdf-failures origin/main

# Baseline, before any edits:
.venv/Scripts/python.exe -m pytest -q --basetemp=tmp/pytest
# 452 passed, 1 skipped in 452.96s

# After all changes in this handoff:
.venv/Scripts/python.exe -m pytest -q --basetemp=tmp/pytest
# 470 passed, 1 skipped in 459.79s   (18 net new tests, 0 removed, 0 newly failing)

.venv/Scripts/python.exe -m pytest -q tests/test_pdf_render_failure.py tests/test_cross_output_consent.py --basetemp=tmp/pytest
# 15 passed

.venv/Scripts/python.exe -m pytest -q tests/test_pdf_report.py tests/test_report_config.py tests/test_report_layout.py tests/test_report_invalidation_app.py tests/test_pdf_render_failure.py --basetemp=tmp/pytest
# 107 passed
```

(`.venv` referenced above is the main checkout's shared virtualenv at
`C:\Users\moham\Documents\GitHub\basin\.venv`; this worktree has no venv of its own, and
tests were invoked with that interpreter and this worktree as the working directory — the
same pattern used by other task worktrees in this repo.)

I did not run `scripts/demo_smoke.py` or `scripts/replay_bundle.py` — this task didn't touch
the export/replay/audit path, only PDF rendering and its UI disclosure, and neither script
generates or checks the PDF.

## Verification performed vs. still manual

Verified in this pass (automated, this machine):

- Renderer selection, failure and degraded-fallback disclosure logic, using mocked/isolated
  fixtures for missing browser, unlaunchable browser, non-zero exit, timeout, and
  empty-output cases — no real browser process was spawned by any committed test.
- A real (uncommitted, one-off) timing measurement of headless Edge on this machine,
  informing the timeout change.
- Private-note consent (on/off, and revocation-then-rebuild) verified with real sentinel
  text through `export_bundle`, `render_html_report`, and `build_fallback_pdf`, and through
  the actual Streamlit export/preview widgets via `AppTest`.
- Custom-data consent's existing hard-block behavior (raises rather than silently
  stripping), and confirmation that custom data — raw or normalized — never reaches either
  PDF path regardless of the ZIP's consent flag.
- Renderer/degraded status now visibly reaches the UI (asserted via `AppTest`'s `.warning`/
  `.caption` collections), not just returned internally.

Still manual / explicitly not claimed here (unchanged from
`docs/report_device_acceptance.md`, which I read but did not edit):

- Native browser download destination/recovery on the actual presentation laptop.
- Whether a real headless-browser PDF render would work end-to-end on that laptop — not
  attempted, since the win32 skip was deliberately kept (see above).
- Any human/practitioner review of report content or wording.
- No participant feedback, organizer requirement, or manual device check is claimed or
  implied anywhere in this handoff; none occurred.

## Files changed

- `basin_core/pdf_report.py` — renderer-selection/failure-handling rewrite described above.
- `app.py` — two call sites updated to the status-returning entry point; renderer/degraded
  status surfaced next to both PDF download affordances.
- `tests/test_pdf_render_failure.py` — new.
- `tests/test_cross_output_consent.py` — new.
- `tests/test_report_invalidation_app.py` — 3 tests added.
- `docs/pdf_failure_handoff.md` — this file (new).

Not edited: `TODO.md`, `HANDOFF.md`, `docs/report_device_acceptance.md` (read only, per
instructions), any other app.py sections, PDF content/layout code, or the export/audit
schema.
