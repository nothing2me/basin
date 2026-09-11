# BASIN claim inventory

Updated: 2026-09-11 | Release line: `main`

This inventory separates source availability, automated verification, local observation and external acceptance. Historical wording in `submission_record.md` records the original proposal; it does not automatically describe the current product.

States used below:

- **Implemented:** present in current source.
- **Automatically verified:** exercised or recomputed by named tests within their declared scope.
- **Observed locally:** inspected on this development computer.
- **Pending external acceptance:** requires the presentation device, an intended user, a domain expert, the team or the organizer.
- **Excluded:** outside the product claim.

## Current product claims

| Claim | State | Evidence and boundary |
|---|---|---|
| BASIN is a local rainfall-scenario evidence workbench. | Implemented; automatically verified in core workflows | `app.py`, `basin_core/`, regression tests and offline Python smoke. It is a single-operator loopback application, not a hosted multiuser service. |
| Core scenario generation and ranking do not require an LLM. | Implemented; automatically verified | Complete synchronized windows, declared rainfall retention, KMeans grouping and deterministic weighted ranking are covered by tests and packet replay. Retention scales rainfall, not streamflow or shortage. |
| The bundled snapshot contains 1991–2025 NOAA GHCN-Daily observations for three airport stations. | Automatically verified | `data/manifest.json` and snapshot checks. The stations are reproducible regional proxies, not validated catchment rainfall. |
| Users can edit, reject, approve and trace rainfall revisions and evidence disagreements. | Implemented; automatically verified | Session/history tests and bundle replay. Approval is a local content decision, not engineering certification. |
| Review is tailored to a stated use case. | Implemented; automatically verified; observed locally | Three pre-run questions select one of four display profiles. The profile changes ordering/disclosure only. Review also offers an optional focus chooser for sessions without that setup. Browser evidence is in `review_acceptance_handoff.md`. |
| Assistant-created Region N storage experiments persist and replay. | Implemented; automatically verified | Schema 2.2 stores versioned settings, trajectories, evidence context and review rationale. Review’s selectable-system preview and report configuration are a separate path and do not yet create these saved records. Replay checks internal numerical consistency; it does not establish physical or operational validity. |
| The optional assistant can use embedded Qwen when its pinned runtime and weights are ready. | Implemented; automatically tested without claiming device readiness | Deterministic tools remain available without the model. Model outputs are constrained and checked, but there is no blanket “zero hallucination” or network-isolation certification. Actual-laptop load time and offline behavior remain open. |

## Evidence, uploads and outputs

| Claim | State | Evidence and boundary |
|---|---|---|
| Local CSVs can be previewed, compared with a selected public station and saved as versioned supporting evidence. | Implemented; automatically verified | Paired valid dates, explicit comparison declarations, consent and schema 2.1 replay are tested. BASIN does not establish station identity, observation-period compatibility, source authenticity or catchment fit. |
| A verified ZIP is internally consistent and replayable. | Automatically verified | SHA-256 inventory, source identity, scenario transformations/revisions, accepted IDs, consented evidence and schema 2.2 saved experiments are checked. The hashes are unsigned and do not prove source authenticity or prevent coordinated replacement. |
| The PDF is a readable companion brief. | Implemented; renderer and consent paths automatically verified | PDF success/failure status and cross-output consent/revocation are tested. Current pages still need inspection on the final device and with the final release data. The PDF is not covered by the ZIP’s cryptographic verification claim. |
| The packet imports directly into WAM or HEC-ResSim. | Pending external acceptance | Current CSV/Markdown outputs support human handoff; no direct importer or recipient interoperability exercise is recorded. |

## Deployment, privacy and accessibility

| Claim | State | Evidence and boundary |
|---|---|---|
| Python core workflows run with sockets blocked. | Automatically verified | `scripts/demo_smoke.py`. This does not prove browser/native/model network behavior on the presentation laptop. |
| A Windows launcher and tracked native executable exist. | Implemented | Python 3.12 x64, VC++/CPU requirements and optional model components are documented. Clean presentation-laptop installation, frozen-package inspection and native Qwen acceptance remain open. |
| Notes and uploads remain local unless explicitly exported. | Implemented with stated limits; automatically verified at application boundaries | Loopback binding, ignored local storage, no telemetry and separate consent controls. Local files are unencrypted; OS, browser and dependency behavior are outside this narrow claim. |
| Review controls are usable in light/dark desktop and narrow layouts. | Observed locally | Actual Chromium checks covered 1280×720 and 375×812, focus profiles, save/restore, tutorial and visible keyboard focus. Projector, screen-reader and intended-user acceptance remain open. |
| BASIN has a measured low environmental footprint. | Not established broadly | The app reports timing/memory and an assumption-based 15–65 W range, not meter readings or lifecycle impact. |

## Scientific and outcome boundaries

| Claim | State | Evidence and boundary |
|---|---|---|
| Storage experiments conserve their defined accounting quantities. | Automatically verified as numerical experiments | Tests cover configured systems, inflow, evaporation, served/unmet demand, spill, bands and day-zero/inclusive crossings. These tests do not calibrate coefficients or validate the system representation. |
| BASIN forecasts reservoir levels, safe yield, deliveries or official restriction dates. | Excluded | The storage view is explicitly illustrative. No operational decision should use its timing without a suitable calibrated model and domain review. |
| Agronomic and KBDI panels provide exploratory indicators. | Implemented; automatically verified as formulas | Fixed regional assumptions are shown. They are not field irrigation schedules, current burn-ban determinations or regulatory advice. |
| BASIN improves analyst productivity or water outcomes. | Pending external acceptance | No completed independent product-use benchmark, recipient exercise or measured outcome is recorded. Do not present a 30×–50× speedup as evidence. |
| Current stations, ranking priorities and terminology are suitable for Region N decisions. | Pending domain review | A hydrologist/provider must review catchment fit, baseline meaning, model language and handoff usefulness. |

## Competition and release questions

| Claim | State | Evidence and boundary |
|---|---|---|
| The finalist event is September 22, 2026 in Pleasanton, with September 21 expected for travel. | Recorded from supplied organizer material | Reconfirm late logistics with the organizer. |
| Judging considers impact, feasibility, community centeredness, innovation and clarity. | Recorded from supplied organizer material | Weights or later Stage 2 guidance are not established here. |
| The session is 60 minutes, the deck is due at 9:00 AM, or three social posts are mandatory. | Unconfirmed | These appear in planning drafts without source evidence in the repository. The team must verify speaking time, submission mechanism/deadline, A/V rules and publicity requirements from organizer communication. |
| The final release works offline on the presentation laptop. | Pending external acceptance | Follow `device_acceptance_results.md`; development-machine checks cannot satisfy this claim. |

## Open conflicts before freeze

1. Align assistant storage-system selection with Review’s selectable systems.
2. Resolve remaining legacy percentage wording and custom-observation source descriptions.
3. Decide the catchment/area/calibration contract with a domain expert before expanding the model.
4. Complete native prerequisites, license/provenance and advisory review on the frozen package.
5. Complete presentation-laptop, output/privacy, projector, intended-user and organizer-format acceptance.

No automated or local result above converts into practitioner approval, scientific validation or final-device acceptance.
