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
