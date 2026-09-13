# BASIN current handoff

## September 13 — T2 terminology audit & T3 custom observation provenance

Tasks T2 and T3 have been fully implemented, verified, and integrated:

1. **T2 — Rainfall percentage terminology audit:**
   - Standardized all user-visible and exported rainfall percentages to explicitly state their baseline and whether they denote retained rainfall (e.g. "70% of observed rainfall") or a reduction (e.g. "30% reduction from observed rainfall").
   - Implemented canonical formatters in `basin_core/summary.py` (`format_retained_rainfall`, `format_rainfall_reduction`, `format_rainfall_dual_explanation`) with strict numerical validation rejecting negative, NaN, and infinite values.
   - Audited and updated `app.py`, `basin_core/assistant.py`, `basin_core/exporter.py`, `basin_core/pdf_report.py`, `basin_core/simulation.py`, and `basin_core/scientific_contract.py`.
   - Prohibited isolated or undefined percentage claims via `validate_report_text_against_prohibited_claims`.
   - Verified by `tests/test_rainfall_terminology.py` (9 tests passing).

2. **T3 — Custom-observation source and date language:**
   - Explicitly marked all user-provided datasets as unverified across preview, comparison, saved panels, and exports (`format_custom_source_label`).
   - Standardized observation date bounds with valid record counts (`format_custom_coverage_dates`).
   - Integrated mandatory proxy/catchment disclaimer: `"Custom data represents unverified local observations, not a calibrated catchment model."`
   - Strengthened `validate_report_text_against_prohibited_claims` to strictly reject claims of official, verified, or certified status for custom data.
   - Preserved full backward compatibility with legacy saved evidence records in `custom_data.py`.
   - Verified by `tests/test_custom_observation_language.py` (8 tests passing).

Verification: The full test suite passed **607 passed, 3 skipped in 825.52s**. Zero failures. `git diff --check` clean. Presentation-device and scientific acceptance remain governed by Part C.

## September 12 — T1 shared storage-system contract

Review and assistant tools now consume one versioned workspace water-system selection. New saved simulation records contain the complete preset or custom configuration and replay against that exact snapshot. Save/reopen restores the selection; reports and the verified handoff brief identify it. Changing the selected system deactivates previous active runs without deleting historical records or reviews.

Review calculation is deliberately split into a side-effect-free preview and an explicit persistence action. Navigating between scenarios no longer creates active simulations. Choosing **Record experiment review** saves and reviews the exact preview identity; later changes to the scenario, system or settings prevent that run from being silently substituted. Assistant experiment requests continue to save runs automatically using the same workspace selection.

Gemini's native-release work is integrated at `b1c51ac`, and its T4 scientific contract is integrated at `3a03ebd`. The T4 module defines and tests the data, calibration, review and prohibited-claim boundaries without changing the current illustrative calculation. Physical presentation-laptop, offline, projector, intended-user and organizer gates remain open; calibrated hydrology still requires approved source data and expert review.

Verification: the final combined suite passed **590 tests with 3 optional-runtime skips in 403.10s**. A fresh browser at 127.0.0.1:8508 confirmed the Region N default, selection of the 12,000 ac-ft municipal preset, changed one-pool trajectory/metrics/wording, explicit experiment rationale, and the saved-review success state. `git diff --check` passed. Presentation-device and scientific acceptance are not implied.

## September 11 — Part C status and development-device checkpoint

Current state: Review browser acceptance is merged at `cf374bd`; the status reconciliation is pushed at `0098dad`. The active release documents now separate implementation, automated verification, development-machine observation and external acceptance. The 601-line historical TODO is preserved under `docs/archive/`; the active `TODO.md` is a concise ordered queue.

The documentation reconciliation identified the former split between assistant-created Region N runs and Review’s transient selectable-system configuration. The September 12 T1 work above resolves that split.

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
