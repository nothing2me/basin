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

New capability is preview only: Data (or initial Workspace) → Preview your local rainfall CSV. One station, exact date/precipitation columns, explicit mm/inches, location description, bounded parsing, missing-day coverage, chart/table and original hash. Files stay in Streamlit process memory, not persistent workspace storage. No scenario, reference, PDF or export integration yet. Private data persistence and source suitability remain future work. All changes remain local, uncommitted and unpushed.

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
