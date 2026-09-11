# BASIN current handoff

## September 11 — Part C Review browser acceptance

Current state: `main` is based on verified Part B release `d88650a`. Actual browser acceptance exercised the tailored Review at desktop 1280 × 720 and narrow 375 × 812 in Dark and Light appearances. All four focus profiles, skipped setup, Show all tools, Change focus, saved-workspace reopening, keyboard focus and the Step 5 storage tutorial target behaved as documented. Focus changes preserved scenario `B-209` revision 1 and the unchanged `0 of 6` review state.

Two localized defects were corrected: the white BASIN bitmap now has a theme-independent dark backing so it remains readable in Light appearance, and the tutorial uses `storage-balance experiment` because selectable systems may contain one or multiple pools.

Files changed: `app.py`, `basin_theme.py`, and `docs/review_acceptance_handoff.md`.

Verified commands and evidence:

- Live Streamlit browser acceptance is recorded in `docs/review_acceptance_handoff.md`.
- Focused Review/App/UI run: 60 tests passed; one AppTest workflow timed out at 60 seconds while the live browser server competed for resources.
- The timed-out `tests/test_app.py::test_full_user_workflow` passed alone in 51.87s after stopping the server.
- Part B release base: **554 passed, 3 skipped**; routing **50/50**; demo replay verified.

Blocker: none for Part C browser acceptance on this machine. Next action: reconcile TODO, README, claims, methodology and presentation status against the merged implementation. The separate presentation-laptop, offline native-model, projector, download, intended-user and organizer-format checks remain physical/team tasks and are not established here.
