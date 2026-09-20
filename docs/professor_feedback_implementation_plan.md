# Professor feedback implementation plan

Updated: 2026-09-20 | Presentation target: 2026-09-22

## Release objective

Present BASIN as a pre-model rainfall-scenario screening and expert-handoff tool. The release must distinguish replay and file-integrity checks from scientific validation, identify internal review as internal, and keep the uncalibrated storage experiment secondary to the rainfall-screening contribution.

The sentence used across the presentation and product is:

> BASIN turns public rainfall observations and explicit assumptions into a transparent scenario shortlist for expert review.

## P0 — complete before the presentation

- [x] Preserve observed-versus-filled rainfall lineage in the snapshot and dashboard.
- [x] Reconcile station selections when the selected community changes.
- [x] Replace unsupported suggested-review language with factual limitations.
- [x] Correct dark/light theme initialization.
- [x] Correct README descriptions of clustering, evapotranspiration, review and replay.
- [x] Reserve **replay-verified** for the ZIP's declared replay scope. Use **hash checked**, **integrity checked**, **internally reviewed**, and **illustrative** for other claims.
- [x] Replace the PDF's fixed five-dimensional description with the implemented feature-space definition: five shared features plus one station-deficit feature per selected station.
- [x] Describe `n >= 5` as a minimum comparison gate with a small-sample limitation, never as statistical validity.
- [x] Report threshold non-crossings against the actual modeled duration, never as `>365 days` for a shorter run.
- [x] Show observed coverage, proxy-filled coverage and remaining gaps separately in the PDF and assistant.
- [x] Label review records as internal screening decisions and capture the reviewer identity in the exported rationale.
- [x] Move the 35%/15% storage comparison and evaporation ratios out of executive findings. Label remaining storage output as an assumption sensitivity appendix.
- [x] Make the rainfall-screening workflow the live demo. Treat storage as an optional limitations demonstration or Q&A response.
- [x] Correct the final-slide copy and use the professor's proposed closing question.
- [x] Generate and visually inspect a fresh PDF and ZIP, replay the ZIP, and run presentation-focused tests.
- [ ] Freeze the release commit and record the final presentation artifact hashes after team approval of the external slide deck.

## P1 — after the presentation

- Assemble watershed-representative precipitation and observed inflow, release, transfer, demand, storage and surface-area records.
- Define calibration and validation periods before fitting a rainfall-runoff and routing model.
- Replace fixed evaporation with dynamic surface area and net-evaporation calculations.
- Add uncertainty ranges and parameter sensitivity rather than single deterministic threshold dates.
- Hindcast documented drought periods and publish performance against withheld observations.
- Arrange independent review with utility practitioners and hydrologists. Record disagreements and required revisions; do not represent review as approval unless the reviewer explicitly provides it.

## Presentation acceptance criteria

1. A repository-wide claim audit finds no generic user-facing **verified** label whose scope is unclear.
2. A generated report contains no five-dimensional claim, no statistical-validity claim at `n >= 5`, and no fixed `>365 days` label.
3. Padre Island and every other station display raw observations separately from proxy-filled analysis values in both the app and report.
4. Every exported scenario decision identifies an internal reviewer or explicitly says that the reviewer identity was not recorded; no record implies external hydrologic approval.
5. Storage results are absent from the executive conclusion or visibly labeled as uncalibrated assumption sensitivity.
6. The live close asks:

   > Would this packet help you identify and document rainfall scenarios worth carrying into a formal water-supply model? What additional data and validation would you require before relying on its outputs for an operational drought decision?

## Validation record

- Presentation-focused report, replay, integrity and pipeline tests: 119 passed across the final focused runs.
- Full Streamlit user workflow with internal reviewer identity and **Build replayable handoff**: passed.
- Repository claim scan: no active occurrence of the removed five-dimensional, statistical-validity, fixed `>365 days`, evaporation-dominance, or generic verified-export phrases.
- Fresh replay bundle: 3 scenarios and 30 audit records replayed; implementation identity matched the current checkout.
- Visual inspection: all 8 pages rendered and inspected. The executive page now leads with rainfall shortlist, duration and matched historical rank; storage appears in the assumptions/results appendix.
- QA PDF SHA-256: `5355B6E77C99BD4D8DB06D0409880350B622E21FDCB1680B4E99616D92CC119D`.
- QA ZIP SHA-256: `036B7732A821C4F6B2535E5B6E33190286EB97D0C7137731A6623549248D2E2A`.
