# BASIN current handoff

## September 11 — Part C status and development-device checkpoint

Current state: Review browser acceptance is merged at `cf374bd`; the status reconciliation is pushed at `0098dad`. The active release documents now separate implementation, automated verification, development-machine observation and external acceptance. The 601-line historical TODO is preserved under `docs/archive/`; the active `TODO.md` is a concise ordered queue.

The documentation reconciliation corrected a material boundary: assistant-created Region N experiments are the schema 2.2 saved/replayed path. Review’s selectable storage-system experiment is a separate transient session/report configuration. Aligning these paths remains the first technical follow-up.

Part C checks completed on this development Windows machine:

- Actual Chromium Review acceptance at 1280×720 and 375×812 in Dark and Light, including four focus profiles, skip/show-all/change-focus, saved-session restoration, visible keyboard focus and tutorial targeting.
- Browser launcher selected port 8505 and reached readiness when requested port 8504 was occupied.
- Development environment recorded as Windows NT 10.0.26200.0 AMD64, CPython 3.12.14 and Streamlit 1.63.0.
- Tracked `BASIN.exe`: 14,869,768 bytes, SHA-256 `838ee698c8ec3d879af622818fb566fcd30c496833b0a2057e0c9dad1e195809`. Identity recorded only; the executable was not accepted in this pass.
- A real browser generated a six-scenario PDF/ZIP, replay verified six scenarios and 300 audit records, and all three PDF pages were visually inspected. The consent cycle exposed and corrected missing workspace-level provider notes in PDF output. With consent on, `PRIVATE-DEMO-123` appeared in ZIP and PDF; after revocation/rebuild it appeared in neither and the PDF disclosed omission.

Changed files are listed in `docs/status_reconciliation_handoff.md`. No production code, dependencies, configuration, data or model artifacts changed during status reconciliation.

Verification:

- `git diff --check`: passed.
- Relative links in every changed Markdown file: passed.
- Diff inspection found no `.py`, `.cmd`, `.sh`, `.toml`, `.txt` or `.json` changes.
- Part B regression baseline remains **554 passed, 3 skipped**; routing **50/50**; demo replay verified.
- Focused PDF/privacy regression after the correction: **39 passed**.

The earlier GitHub fetch limitation is resolved; upstream was fetched and integrated in this review. Actual presentation-laptop install/offline/native/download/PDF/projector checks, intended-user exercise, organizer format and final rehearsal remain not run. No weights were downloaded and no network/firewall settings were changed.

Next action: run Task 6 on the actual presentation laptop with the user controlling connectivity and model download authorization.

## Task-branch integration

Task branches `864d95f` and `127a344` are integrated with newer upstream `0098dad`. The newer live board, source/persistence distinctions, browser evidence and presentation disclaimers take precedence. Original branch handoffs are retained in `docs/archive/task_branch_review_acceptance_handoff.md` and `docs/archive/task_branch_status_reconciliation_handoff.md`. The newer logo styling is preserved without a second padded wrapper; the original checkbox/radio keyboard-focus rule is retained. Task 6 remains external acceptance; its new-chat prompt is in `docs/next_tasks/06_laptop_and_people.md`.

Final combined verification after the provider-note correction and teammate integration: Review preferences, AppTest workflow, UI improvements, cross-output consent and both PDF paths passed **100 tests in 102.89s**. The teammate integration had separately passed its 61-test UI set; an earlier focused UI/storage run passed 119 tests before the last upstream reconciliation. Neither is a final full-suite result. `git diff --check` passed. No fresh physical-device acceptance is claimed by this integration review.
