# BASIN current work board

Updated: 2026-09-11. This file tracks current release work. The previous detailed board is preserved in [the historical archive](docs/archive/TODO_history_through_2026-09-11.md); checked historical items there are evidence records, not current release claims.

## Completed and merged

- [x] **Tasks 1–3 — release integration.** Optional native-runtime install/repair, numerical meaning corrections, PDF outcome disclosure, consent/revocation coverage and upstream integration are on `main`. Evidence: [integration review](docs/tasks_1_3_integration_review.md) and [current handoff](HANDOFF.md).
- [x] **Part A — tailored Review.** The Scenario Builder asks three questions before generation. Four display profiles (`compare`, `storage`, `operations`, `handoff`) change Review ordering and disclosure without changing calculations or ranking. Review also provides an optional focus chooser for example, restored and legacy sessions.
- [x] **Part B — saved illustrative experiments.** Assistant-created Region N simulation settings, trajectories, review rationale and provenance persist in schema 2.2 sessions and are replayed in the verified ZIP. Replay establishes internal consistency, not calibration or forecast validity. Review’s selectable-system preview remains a separate session/report path until T1 is resolved.
- [x] **Task 4 — Review browser acceptance on the development machine.** Dark/light, 1280×720 and 375×812, all focus profiles, skipped setup, Show all, Change focus, session restore, keyboard focus and tutorial targeting were observed in the actual browser. Evidence: [Review acceptance handoff](docs/review_acceptance_handoff.md). This is not presentation-laptop, projector, screen-reader or intended-user acceptance.
- [x] **Task 5 — current-status reconciliation.** Current docs distinguish implementation, automated verification, local browser observation and external acceptance. Evidence: [status reconciliation handoff](docs/status_reconciliation_handoff.md).

## Next technical work

- [ ] **T1 — align assistant and Review storage systems.** Assistant simulation requests are tied to Region N while Review can select another configured storage system. Define one shared selection contract before changing calculations.
- [ ] **T2 — remove remaining report ambiguity.** Audit legacy report percentage arguments and ensure every rainfall percentage says whether it is retained rainfall or reduction from observations.
- [ ] **T3 — strengthen custom-observation source language.** Keep user-entered sources and observation periods explicit across Data, Review and exports. Do not imply station identity, catchment fit or source authenticity.
- [ ] **T4 — decide the area-model boundary.** Catchment weighting, reservoir surface area and calibrated inflow/evaporation remain future domain work. Do not extend the illustrative experiment until an expert-approved data/model contract exists.
- [ ] **T5 — document ingestion.** PDF/report ingestion remains future work; define provenance, extraction review and privacy contracts first.
- [ ] **T6 — native release gates.** Verify VC++ and CPU prerequisites, offline `vcomp140.dll` handling, model license/provenance, advisory status and a frozen-package privacy inspection.

## Part C external acceptance

- [ ] **Task 6A — presentation laptop.** Record release/package hashes, OS/Python/runtime, clean setup, no-AI startup, occupied-port recovery and missing-prerequisite behavior on the actual device.
- [ ] **Task 6B — controlled offline workflow.** With the user controlling connectivity, exercise Data/map, generation, Review focus, storage changes, save/reopen, review/accept and downloads. Test embedded Qwen separately only after its install path is ready; do not download weights or change network/firewall settings without explicit instruction.
- [ ] **Task 6C — output/privacy acceptance.** Export with harmless private sentinel notes and test consent off/on/revoked, replay the ZIP, inspect the PDF pages and confirm the download location.
- [ ] **Task 6D — presentation conditions.** Check projector readability, keyboard navigation and startup recovery using the frozen release and backup media.
- [ ] **Task 6E — intended-user exercise.** An intended user must complete scenario review/export without coaching. Record actual confusion and wording changes; automated tests cannot satisfy this item.
- [ ] **Task 6F — organizer/team confirmation.** Confirm speaking time, submission mechanism/deadline, A/V constraints, required disclosures and final backup plan from organizer communication. Rehearse to the confirmed format.

## Claim boundaries for every release

- BASIN constructs and reviews rainfall-stress scenarios. It does not forecast reservoir levels, safe yield, deliveries, official restriction dates or drought probability.
- Airport observations are reproducible regional proxies, not validated catchment rainfall.
- Saved storage experiments are uncalibrated. Numerical replay does not validate their assumptions or establish operational outcomes.
- SHA-256 checks establish internal packet consistency. They do not authenticate a source or provide a digital signature.
- Local development checks do not establish presentation-device, practitioner, scientific, accessibility or organizer acceptance.
