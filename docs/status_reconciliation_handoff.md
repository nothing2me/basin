# Status reconciliation handoff

Date: 2026-09-11 | Base reviewed: `cf374bd010295fdc46bb73dca889032a8ff97345`

## Outcome

The active board and public-facing status documents now distinguish implemented behavior, automated verification, development-machine browser observation and external acceptance. The prior 601-line TODO is preserved verbatim at `docs/archive/TODO_history_through_2026-09-11.md`; `TODO.md` is now the concise release queue.

The reconciliation removed unsupported presentation claims from the active plan: authoritative 60-minute timing, a completed independent hydrologist benchmark, 30×–50× productivity, universal laptop support, zero-hallucination guarantees, fixed operational breaking points and completed social/day-of requirements. Historical master-deck, social and rapid-response drafts retain their content but carry prominent unconfirmed-draft notices.

Source inspection originally found a material boundary that earlier prose blurred: assistant-created Region N simulations persisted and replayed while Review’s selectable-system experiments were transient. T1 resolved that boundary on 2026-09-12 with a single versioned workspace selection and saved-run system snapshot. README, methodology, claims and TODO now state the shared contract.

## Files changed

- `README.md`
- `TODO.md`
- `docs/archive/TODO_history_through_2026-09-11.md`
- `docs/claim_inventory.md`
- `docs/methodology.md`
- `docs/presentation_plan.md`
- `docs/finalist_showcase_master_deck.md`
- `docs/social_media_assets_and_schedule.md`
- `docs/day_of_surprise_rapid_response_guide.md`
- `docs/tasks_1_3_integration_review.md`
- `docs/device_acceptance_results.md`
- `docs/status_reconciliation_handoff.md`
- `HANDOFF.md`

No production code, dependencies, configuration or model/data artifacts were changed in this documentation pass.

## Evidence checked

- Current implementation and tests for Review preferences, saved simulations, exports and launcher behavior.
- Part C actual-browser evidence in `docs/review_acceptance_handoff.md`.
- Task 1–3 integration evidence and Part B regression baseline recorded in the current handoff.
- Development-machine release identity and occupied-port startup behavior recorded in `docs/device_acceptance_results.md`.
- Relative Markdown links in every changed document and cited repository paths were checked after editing; `git diff --check` and documentation-only diff inspection were used as completion gates.

## Unresolved

- Teammate changes were not available at the initial fetch attempt because GitHub network access was unavailable in the sandbox. Fetch must be repeated immediately before commit/push.
- T1 storage selection is resolved in the current working release; physical and scientific acceptance remain separate.
- Legacy percentage wording, custom-observation source descriptions, catchment/area calibration, document ingestion and native release gates remain open.
- Actual presentation-laptop offline/native/download/PDF/projector checks, intended-user review, organizer format and final team rehearsal remain external tasks.
- The app footer’s `<200 MiB RAM` and broad on-device wording should be reviewed separately as a product-code claim; the historical audit recorded a 270.2 MiB development-browser working set.

## Part C continuation after the documentation commit

Development-browser output acceptance exposed a consent mismatch: workspace-level provider notes entered the ZIP but were omitted from both PDF renderers. `basin_core/pdf_report.py` now renders a Provider Notes section only when the shared note consent is on and otherwise discloses that recorded notes were omitted. `tests/test_cross_output_consent.py` now covers provider notes alongside scenario notes across ZIP, HTML and vector PDF paths.

Focused PDF/consent verification: **39 passed**. After rebasing onto teammate integration `6aed073`, the combined Review/App/UI/PDF/consent selection passed **100 tests in 102.89s**. A real browser rebuild proved `PRIVATE-DEMO-123` present in both consented ZIP/PDF and absent from both after revocation; independent replay passed for six scenarios and 300 audit records. All three PDF pages were rendered and visually inspected. Presentation-device downloads remain open.

T1 follow-up completed on 2026-09-12: Review and assistant experiments now share a versioned workspace water-system selection. Saved runs snapshot the complete system and replay it; reports use the saved capacities, bands and assumptions. Review previews remain side-effect free until their rationale is recorded. Final combined verification with the integrated native-release gates passed **590 tests with 3 optional-runtime skips in 403.26s**. Fresh-browser selection and save-review behavior passed on the development machine.
