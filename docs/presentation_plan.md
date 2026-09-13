# BASIN finalist showcase presentation plan

Updated: 2026-09-11 | Product line: BASIN 0.2.0

This is a rehearsal plan, not an organizer rules record. The repository supports the September 22, 2026 Pleasanton event and a three-person team from supplied material. Speaking time, submission mechanism/deadline, A/V constraints, publicity requirements and any day-of assignment still require organizer confirmation. Do not call a 45+15 or 60-minute format authoritative until that evidence is recorded.

## Presentation claim rule

Use only behavior demonstrated by the frozen release. Say “internally replayed” for the verified ZIP, “illustrative” for storage experiments and “observed on the development machine” for current browser acceptance. Do not say certified, zero-hallucination, any laptop, exact operational breaking point, independently validated, or measured productivity improvement.

The sentence judges should remember:

> **BASIN turns public rainfall observations and explicit assumptions into a transparent scenario shortlist for expert review.**

## Three-minute core demonstration

### 0:00–0:25 — Decision gap

- Explain that small providers need a transparent way to screen rainfall-stress questions before commissioning formal hydrologic modeling.
- State the boundary: BASIN organizes evidence and assumptions; it does not replace WAM, HEC-ResSim, a hydrologist or an official water-supply model.

### 0:25–0:55 — Data and tailored setup

- Open **Data** and identify the bundled NOAA snapshot and airport-station proxy limitation.
- Open **Workspace** and answer the three setup questions. Explain that the answers tailor Review layout and do not change calculations or ranking.
- Generate the example shortlist and show synchronized whole historical windows and visible ranking contributions.

### 0:55–1:30 — Grounded interrogation

- Open **AI Assistant** and use one deterministic chip or supported question such as “Why did this scenario rank first?”
- Explain that numerical answers come from read-only Python tools. Embedded Qwen is optional and should be demonstrated only if the frozen laptop acceptance records it as ready.
- Avoid a “cannot hallucinate” guarantee; unsupported or ambiguous questions can still require clarification, and generated language has a bounded but nonzero risk.

### 1:30–2:15 — Tailored Review and illustrative storage

- Show the chosen Review focus and the **More tools** disclosure.
- If storage is relevant, select a configured system and identify all assumptions on screen. The Review preview is retained for the current session/report; do not call it a saved schema 2.2 experiment.
- Describe threshold days as outcomes of those inputs. Do not convert them into official restriction dates, forecasts or policy recommendations.
- If demonstrating a storage experiment, choose the workspace water system first. Review and assistant tools share that selection. Record the experiment review before export so the exact system inputs, settings, trajectories and rationale can be replayed from the verified packet.

### 2:15–2:45 — Human decision and handoff

- Review or revise a rainfall scenario and show that edits invalidate prior acceptance.
- Build outputs only after the current revisions and any saved experiment have the required review state.
- Describe the ZIP as internally consistent and replayable within its manifest scope. Describe the PDF as a companion brief.

### 2:45–3:00 — Close

- Reiterate that BASIN helps a user decide what deserves deeper modeling and preserves how that shortlist was constructed.
- Name the next validation step: a domain expert checks station/catchment suitability and the handoff’s usefulness.

## Longer-format modules

Use these only after the organizer confirms the available time:

1. **Method walkthrough:** synchronized windows, retention, clustering, ranking and revision history.
2. **Evidence disagreements:** source comparison, public disposition and private-note consent.
3. **Saved experiment replay:** selected system, assumptions, conservation comparison, review rationale and verifier scope.
4. **Custom rainfall evidence:** preview, paired-date comparison, explicit source declarations and schema 2.1 consent.
5. **Architecture:** local deterministic core, optional embedded model, process isolation and single-operator limits.
6. **Questions and limitations:** catchment fit, calibrated modeling, source authenticity, accessibility and final-device status.

## Three-person speaking lanes

The team must assign these roles; the repository does not assign credentials.

| Lane | Responsibility |
|---|---|
| Problem and community context | Explain the screening need, target users and scientific boundary. |
| Product demonstration | Drive Data, tailored Workspace, Review and assistant flow. |
| Evidence and handoff | Show saved experiment provenance, export scope, replay and next expert step. |

## Defensible Q&A

**How is this different from WAM or HEC-ResSim?**
BASIN prepares rainfall-stress evidence and an auditable shortlist for deeper work. It does not reproduce statutory water-rights accounting, calibrated reservoir operations or dam-safety models.

**Why is this AI?**
The core uses local KMeans grouping and deterministic ranking. The optional embedded Qwen path maps supported language to constrained read-only tools; direct deterministic tools remain available without it.

**Can generated answers invent numbers?**
Tool results come from application-owned calculations and rendering, with validation and call limits. This narrows risk but is not a universal guarantee. Users should rely on cited scenario/tool outputs and review assumptions.

**What does verified mean?**
The ZIP verifier recomputes the declared numerical and provenance scope and checks SHA-256 file identities. It does not authenticate upstream sources, digitally sign the packet or validate scientific assumptions.

**Does the storage experiment predict an emergency date?**
No. It shows what the configured accounting assumptions produce for a saved rainfall scenario. Coefficients, capacities and bands require domain review and calibration before operational use.

**Does it run offline?**
Core Python workflows have passed a socket-blocked smoke test. The final browser/native/model workflow must still pass on the presentation laptop with connectivity controlled by the user.

## Release and rehearsal gates

- [x] Tailored Review implementation and automated tests.
- [x] Development-machine browser acceptance at desktop/narrow widths and light/dark appearance.
- [x] Schema 2.2 saved experiment persistence and numerical replay tests.
- [ ] Freeze a release SHA and package hash.
- [ ] Complete clean setup, no-AI and optional native-AI checks on the presentation laptop.
- [ ] Inspect final PDF and ZIP with consent off/on/revoked and replay the downloaded packet.
- [ ] Check projector readability, keyboard flow and failed-start recovery.
- [ ] Run an uncoached intended-user review/export exercise.
- [ ] Confirm organizer speaking time, submission requirements, A/V constraints and required disclosures.
- [ ] Rehearse the confirmed format and prepare the team-approved backup recording/media.

Record results in [device acceptance](device_acceptance_results.md). Historical draft scripts may contain unsupported figures; use this plan and the [claim inventory](claim_inventory.md) for the final presentation.
