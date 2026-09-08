# Build validation — September 5/6, 2026

Environment: Windows, CPython 3.12.7; exact Python packages in requirements.txt.

- 20 tests passed, including NOAA units/flags/missing values, invalid parameters, synchronized deterministic generation, missing-window exclusion, reference formulas, scores/group representatives, edited approval invalidation, custom replacement, rejection, private-note exclusion/opt-in, approval content mutation, session restore, offline export replay, and a Streamlit user workflow through every screen.
- 300 candidates generated and grouped in an initial measured 0.835 seconds; timings vary by environment and settings.
- Network-blocked 500-candidate rehearsal: six approved scenarios replayed from bundled observations through transformations and revisions. Measured initial wall time 1.097 seconds and final resident process memory 177.7 MB. No peak-memory claim.
- That run covered six groups with BASIN, one with score-only and three with seeded random. Mean feature distances were 0.916, 0.549 and 1.131 respectively; mean scores 66.4, 80.5 and 49.5. This is one example and does not establish user benefit.
- All 49 pinned dependencies installed into a clean second environment using only the downloaded Windows CPython 3.12 wheel directory and `--no-index`.
- Local browser UI was opened and inspected; full workflow interactions are also covered by Streamlit AppTest. Actual projector and other OS behavior are untested.

The packaged kit contains no user sessions, private notes, source correspondence or raw survey. Python itself must already be installed. Automated rehearsal approvals do not constitute professional review. Refer to validation_notes.md for pending human validation.

Interface revision: replaced the presentation-oriented pages with Workspace, Review, Exports and Data. Added searchable/filterable candidate inspection, direct daily-value editing and observed rainfall interval selection. The updated UI regression checks generation, ranking, approvals/export, editing-induced approval invalidation and data inspection.

## Local upload workstream — 2026-09-06

Python 3.12.14 virtual environment created at .venv; pinned requirements installed successfully. Initial sandbox network restriction was resolved with an approved dependency-install call; no requirements changed.

- Clean ff3ff0f snapshot: 24 existing tests passed using `python -m pytest -q tests --basetemp=<local-temporary-directory> --tb=short`.
- Working tree existing tests plus initial upload tests: 43 passed, one test assertion failed because an untouched session has no workspace key rather than a None value. Corrected the test to accept the actual empty state.
- `.venv/Scripts/python.exe -m pytest -q tests/test_uploads.py --basetemp=tmp/pytest-upload-ui-final --tb=short`: 20 passed, including UI valid/error/clear behavior.
- `.venv/Scripts/python.exe scripts/demo_smoke.py`: verified, six scenarios replayed, no pipeline network calls.
- `.venv/Scripts/python.exe scripts/replay_bundle.py output/BASIN-rehearsal.zip`: verified.
- `git diff --check`: passed.

Initial pytest runs encountered Windows default-temp permissions and duplicate collection from the temporary baseline copy. Explicit local basetemp resolved permissions; the baseline snapshot was moved outside the repo afterward. These were test setup issues, not silently skipped application tests.

New capability is preview only: Data (or initial Workspace) → Preview your local rainfall CSV. One station, exact date/precipitation columns, explicit mm/inches, location description, bounded parsing, missing-day coverage, chart/table and original hash. Files stay in Streamlit process memory, not persistent workspace storage. No scenario, reference, PDF or export integration yet. Private data persistence and source suitability remain future work. That checkpoint was local at the time of writing; it was superseded by the published integration recorded in the next section.

## Published CSV preview integration — 2026-09-06

User explicitly authorized publication, superseding the prior local-only checkpoint. Integrated the upload preview with teammate main commit 8f04091, preserving schema 2.0 evidence/integrity and revised reservoir work.

- `.venv/Scripts/python.exe -m pytest -q --basetemp=tmp/pytest-integrated-preview --tb=short`: **97 passed**.
- `.venv/Scripts/python.exe scripts/check_snapshot_checkout.py`: passed fresh-clone observation hash and LF policy.
- `.venv/Scripts/python.exe scripts/demo_smoke.py`: verified, 5 exported scenarios and 500 audit records replayed.
- `.venv/Scripts/python.exe scripts/replay_bundle.py output/BASIN-rehearsal.zip`: verified, implementation matches.
- `.venv/Scripts/python.exe scripts/package_demo.py`: source ZIP built; checked inclusion of upload parser, tests and illustrative CSV and exclusion of local sessions/environment.
- Diff whitespace checks passed. Windows Python 3.12.14; other operating systems and teammates' hardware not validated here.

README now includes teammate setup and preview use. docs/examples/local-rainfall-example.csv is the supplied illustrative 30-day gauge example adapted by header only: 62.5 mm total, no gaps. It is not authenticated historical data. The multi-station example, original attachment and private/local artifacts remain out of Git. The in-app template remains available too.

Preview limitations remain: one station per file; no upload persistence, scenario mutation, PDF parsing or numeric public-versus-upload comparison. Existing manual evidence and scenario comparisons from teammate changes remain available separately. Publishing repository code does not host a shared running app.

## Running-process update recovery — 2026-09-06

After pulling the schema 2.0 changes while the older server was still running, the UI reported missing Workspace.selection_reason and evidence attributes. A fresh Python import confirmed selection_reason exists in the current source. Restarted the local Streamlit server to reload modules and clear stale in-memory objects. No application code patch was needed.

`.venv/Scripts/python.exe -m pytest -q tests/test_app.py --basetemp=tmp/pytest-restart-check --tb=short`: **2 passed**. Server restarted successfully on loopback port 8501. README now documents stopping before pull, restarting afterward, saved-session recovery and the distinction from legacy executable artifacts. Tests verify fresh-process UI workflows; they do not establish preservation of unsaved in-memory work across updates.

## Tutorial layout correction — 2026-09-06 (published in `83d593d`)

Replaced disconnected HTML target wrappers with keyed Streamlit containers. The guide appears once above the main content; navigation stays grouped and sidebar controls retain their space. Target labels and jump links replace decorative arrows. Export instructions explain the outstanding review gate, and manual navigation can return to the active step.

Verification: `.venv/Scripts/python.exe -m pytest -q tests/test_app.py --basetemp=tmp/pytest-tutorial-final --tb=short`: **2 passed in 17.43 seconds**, covering the full product workflow and seven-step tour, export gating, manual-page recovery, previous/next, finish and restart. In-app browser inspection checked actual outlines and guide placement on desktop, including generator, review and export; the review jump link was exercised. `git diff --check` passed. No core model change; full suite was not repeated for this layout change. Teammate review and other viewport/device validation remain pending. Published in `83d593d`.

## Appearance and onboarding — 2026-09-06

Native coordinated Light/Dark/System themes now style widgets, menus and canvas tables. Plotly labels/backgrounds inherit native theming. CSS adds brand, page hierarchy, metric cards, first-run invitation and theme-aware tour surfaces. Help & tutorial is directly below navigation; Settings contains browser-only shortcuts to the native theme choices. No server-global theme mutation or workspace reload occurs on a theme change. The shortcuts depend on the pinned Streamlit menu test IDs and provide a native-menu fallback if unavailable.

`.venv/Scripts/python.exe -m pytest -q tests/test_app.py tests/test_uploads.py --basetemp=tmp/pytest-appearance-final --tb=short`: **22 passed in 20.45 seconds**. Tutorial coverage starts through the first-run invitation and restarts through Help. Browser inspection checked light and dark first-run/table/chart/tour contrast; switching Light to Dark retained run `4857c0cc575c`, 300 candidates, seed 22, and tutorial step 1. Source packaging succeeded and inclusion of `basin_theme.py` was checked. Diff whitespace checks passed. Native theme persistence is browser-local. Other viewport/device validation and teammate review remain pending. Published in `83d593d`.

## Documentation reconciliation checks — 2026-09-06

Commit `83d593d` on `main`, working tree clean, `origin/main` at the same commit. Windows 11 Pro, CPython 3.12.14 in the repository `.venv`; dependencies already installed from the pinned `requirements.txt`, no installation performed in this pass. Commands were run as `.venv/Scripts/python.exe <command>` from the repository root.

- `-m pytest -q --basetemp=tmp/pytest-doc-reconcile --tb=short`: **97 passed** in 60.26 s.
- `scripts/check_snapshot_checkout.py`: verified. A fresh clone reproduces observation SHA-256 `672c23f8335093cdba84608c53ade768a9737e4088e60d95c04965257e0178a0` with the recorded `data/observations.csv: eol: lf` attribute.
- `scripts/demo_smoke.py`: verified; network-blocked rehearsal completed and rewrote `output/BASIN-rehearsal.zip`.
- `scripts/replay_bundle.py output/BASIN-rehearsal.zip`: verified. Run `5cf371d39eb2`, 5 accepted scenarios, 500 audit records replayed, `implementation_matches_current: true`.
- `scripts/evaluate_selection.py`: 9 configurations written to `output/selection-evaluation.json` — seeds 7, 22 and 91 across the multiple-duration, mixed-perturbation and single-station profiles, silhouettes 0.246 to 0.416. This is a diagnostic comparison, not evidence of user benefit.

These runs repeat existing automated checks on one machine at one commit. They do not repeat the offline wheel installation, the timing and memory measurements or the browser inspections recorded in the sections above, and they establish no practitioner validation, teammate review or presentation-device readiness. Documentation only was edited in this pass: `TODO.md`, `HANDOFF.md`, `README.md` and this file.

## Part B first comparison slice — 2026-09-06

Fetched/fast-forwarded to 5e17706. Latest upstream baseline: 97 tests passed. After comparison implementation: `.venv/Scripts/python.exe -m pytest -q --basetemp=tmp/pytest-partb-final --tb=short`: **105 passed**. Additional UI coverage then exercised successful paired totals/report opt-in and reset after changing the upload; upload/comparison subset: **28 passed**. No production code changed after the full suite.

Fresh snapshot checkout passed. Offline demo verified 5 scenarios and 500 audit records; explicit replay passed. Source package built. These scenario checks do not cover the new separate comparison report, whose arithmetic, blocking and UI states are checked in the new tests. Windows Python 3.12.14. No new dependency or scientific-validity claim. Video/presentation contradictions and unperformed human/laptop gates from upstream reconciliation remain open.

Part B is a bounded descriptive comparison, not completed scenario/evidence integration. User-declared same-station/proxy and daily-basis review, exact paired-date totals, missing-day exclusion, zero-reference handling and explicit numerical download opt-in are implemented. No private upload is committed or automatically transmitted. Diff whitespace passed.

Publication integrated concurrent upstream 106842a (submission record, logos and README link) by clean rebase. No tested application code changed in that upstream commit; no redundant test rerun was performed.


## Reviewed custom-data integration — 2026-09-07 (local)

- `.venv/Scripts/python.exe -m pytest -q --basetemp=tmp/custom-full-0907 --tb=short`: 125 passed.
- `.venv/Scripts/python.exe -m pytest tests/test_custom_data.py tests/test_integrity.py -q --basetemp=tmp/custom-final-contract-0907 --tb=short`: 45 passed after final verifier-scope/date-validation updates.
- Final saved-data UI presentation: `tests/test_custom_data.py::test_upload_ui_save_restore_and_export_consent`, basetemp tmp/custom-ui-final-0907: passed.
- `scripts/replay_bundle.py tmp/custom-replay-validation/packet.zip`: verified 3 scenarios, 30 audit records, 1 custom comparison; current implementation identity matched. Inputs are synthetic software-test data, not observations used for a scientific claim.
- `python -m compileall -q basin_core app.py` and `git diff --check`: passed.

Tests cover original-byte restore, normalization (including inches), paired arithmetic, unknown suitability, content/reference/metadata hash rejection, version replacement, selective approval invalidation, explicit export consent, original-byte exclusion, independently replayed packet verification, failed-save preservation and legacy baseline behavior. No human/practitioner validation or new area-model calibration is claimed.

Publication verification: final source passed all 125 tests with `python -m pytest -q --basetemp=tmp/publish-custom-final --tb=short`. User authorized GitHub publication; private local data and generated packets are excluded.
