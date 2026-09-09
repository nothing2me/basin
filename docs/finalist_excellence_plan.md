# BASIN: plan for an excellent September 22 finalist presentation

Prepared September 8, 2026, from the mock-judge assessment of checkout `cd67c8b` and the supplied August 10 rules/resource packet.

**Objective:** present a reliable, useful, community-controlled rainfall scenario workbench, with evidence strong enough to answer every major judging objection identified in the assessment. “10/10” is the quality target, not a guaranteed panel score or winning probability. The official materials publish five criteria without weights.

**Available external access:** the team has access to a hydrologist or technical faculty reviewer. Confirm their actual expertise and describe their role accurately. Access to a rural-serving water operator or planner is not yet established. A faculty review cannot substitute for evidence from the intended community.

This document is a proposed execution plan. It does not record completed validation, assign teammates without their agreement, or authorize external messages. Keep implementation ownership and status on the existing `TODO.md` board; this plan defines priorities, dates and acceptance criteria. Use B03/B04 for evidence and verification, B05/B06 for workflow and selection, B08 for the illustrative reservoir, B09 for human validation and B11 for presentation readiness, as applicable.

## The product to make excellent

**Primary user:** a rural-serving provider's analyst or a regional planner supporting small providers. Choose one actual role with the reviewer and prospective community contact.

**Primary task:** prepare three meaningfully different rainfall stress scenarios for a professional modeling discussion, explain their selection, challenge one assumption, and hand off the reviewed evidence.

**Observable outcome:** another person can locate the source observations, understand the transformations and priorities, identify unresolved limitations, and use the packet to specify the next analytical step without calling the developer.

**Pitch:** “BASIN helps rural-serving water providers turn public rainfall records into a diverse, human-reviewed set of stress scenarios and a reproducible evidence packet for professional analysis.”

Retain the previously selected reservoir experiment as an explicitly illustrative, optional view. Its assumptions and outputs must be separate from operational advice and the verified rainfall packet. Do not attempt to calibrate a regional reservoir model during this sprint. Keep the local assistant optional; the complete core workflow must work without it.

## What an excellent result looks like under each criterion

| Criterion | Evidence needed | Acceptance gate |
|---|---|---|
| Impact | A specific preparation task, a completed user exercise, and a recipient who can explain the packet's next use. | Record actual completion time, errors and assistance for BASIN and a reasonable existing process. Report only observed results, including failures and sample size. The recipient names the next analysis and what remains missing. |
| Feasibility | A frozen build, reliable outputs, modest deployment requirements and an independent laptop run. | All relevant checks pass; three consecutive complete demo workflows succeed on the presentation laptop offline. Installation requirements are measured and documented. The embedded assistant needs no model installation. |
| Community Centeredness | A real affected user changes the design and controls priorities, acceptance and sharing. | Record at least one concrete change arising from a rural-serving operator/planner and have that person review the response. Demonstrate that disagreement remains visible and private notes are excluded across every output by default. |
| Innovation | Evidence that the combined workflow adds something useful beyond familiar methods. | Compare shortlist approaches blindly where feasible. The reviewer identifies a useful distinction or reduced review burden attributable to BASIN, with a written explanation and limitations. |
| Clarity | One coherent story with claims tied to evidence. | Every factual pitch claim has a source, reproducible calculation or explicitly labeled study result. Two people unfamiliar with the project can explain who it serves, what it does, why the AI helps and what it cannot establish. |

These are proposed project gates, not additional Zoho requirements. Community impact remains only partially demonstrated if no affected user participates. Strong software or faculty feedback does not close that gap.

## Three work lanes and capacity

Allocate approximately **70-90 combined team hours** between September 9 and 20, subject to actual availability. Choose an owner and a second-person reviewer for each deliverable on the shared board. Protect the critical path if capacity is smaller.

- **Product and verification lane:** reporting correctness, assistant boundaries, privacy, regression checks and packaging; roughly 28-36 hours.
- **Evidence and validation lane:** reviewer coordination, station/method review, user tasks, baseline comparison and claim evidence; roughly 24-30 hours.
- **Presentation and deployment lane:** operator feedback capture, novice walkthroughs, pitch, laptop rehearsal and recording; roughly 18-24 hours.

Begin reviewer and potential operator scheduling immediately while technical repair proceeds. The team handles outreach; no messages have been sent by this plan.

## Phase 1: make every output trustworthy — September 9-11

### Repair the executive report first

1. Replace formatted-string arithmetic with numeric breach-day fields. Format “Day N” only at the display boundary. Cover no breach, one breach, multiple breaches, and different earliest tiers.
2. Remove the hard-coded `+9 Days` benefit and fixed policy/savings assertions. For an optional illustrative comparison, calculate both runs under the same explicit settings and display the difference only when it is defined. If a run never crosses the threshold within the modeled window, show that fact rather than implying an infinite extension or a guaranteed reserve.
3. Pass explicitly selected settings into the report; show their values and units. Do not silently substitute a different starting storage or conservation fraction. Identify which selected scenario drives any illustration.
4. Make “verified” precise. The rainfall packet's verification badge applies only to outputs covered by the verifier. Give a separate report an accurate draft/illustrative status until it is included in a defined verification contract. A successful ZIP check does not verify a separately generated PDF.
5. Remove operational policy recommendations from the primary brief. Any retained policy reference must have an authoritative source, jurisdiction, date and scope, and must distinguish prescribed rules from illustrative assumptions.
6. Apply private-note and custom-data consent consistently to PDF, Markdown, ZIP and previews. Inspect the PDF path, which currently accesses scenario history notes directly. Acceptance without a sharing opt-in must not silently publish those notes.
7. Render the corrected brief and inspect it at normal reading size and on the projector. The first page should explain the task, selected scenarios, evidence, limitations and requested next step.

**Done when:** the failing multiple-breach case works; changing a scenario/settings changes the relevant derived results correctly; a note sentinel is absent from all default exports; unsupported guarantees are absent; the displayed verification scope matches the code.

### Bound the assistant's behavior

- Expose only validated read-only tools. Validate argument names, types, ranges, dates and identifiers; make the chosen scenario and parameters visible.
- If the question is ambiguous, use a fixed clarification response rather than guessing another scenario/year. Unsupported questions get a fixed abstention/help response.
- Render factual answers from tool results. The embedded assistant uses fixed templates; unsupported questions should explain the available tools. A deterministic suggestion menu can provide next steps.
- Record the application revision for the demo and document prerequisites. Remove “zero hallucinations” and “runs on any laptop” claims: routing and interpretation still need evaluation.
- Verify the embedded assistant and core workflows without any model server or model download.

**Done when:** the previously demonstrated arbitrary-text path is closed; invalid tool arguments are rejected; the embedded assistant runs without any model service; a 30-question evaluation records correct tool/parameter selection, clarifications, abstentions and failures. Proposed target: at least 90% correct handling overall, with zero critical failures such as exposing private information or presenting unsupported forecasts in the test set. This is a bounded test result, not a universal guarantee. If the gate fails by September 17, use direct controls for the primary demo.

### Reconcile public claims

Update README, claim inventory, AI-use/third-party disclosures, report copy, demo script and setup guidance against the same release. Separate development assistance from runtime AI. Remove unsubstantiated professional affiliations, benchmark speedups, universal consulting cost/timeline claims, authenticity guarantees and operational conclusions.

Create a compact claim ledger: statement, evidence link, scope/date, reviewer and allowed wording. Keep historical submission answers intact as historical records; revise the current pitch rather than rewriting what was submitted.

## Phase 2: establish scientific scope and a meaningful handoff — September 10-13

Ask the available reviewer for two bounded sessions: approximately 45 minutes for scope/method feedback and 45 minutes for independent packet use. If they are a technical faculty member without relevant hydrology expertise, record that limitation and use their review for software/evidence usability. Seek hydrologic feedback separately rather than inventing credentials.

For the first session, bring one complete case and ask:

1. Is this a useful preparatory task, and who would normally perform it?
2. What can these stations and time windows legitimately support? Which claims must be narrowed?
3. Are the features, reference periods, concurrence definition and scenario transformations understandable and appropriate for this exercise?
4. What fields and caveats does a recipient need to request further analysis?

Record findings as accepted changes, open disagreements and work beyond scope. Ask the reviewer to confirm the summary; confirmation is not certification of the software or reservoir model.

Create a concise applicability sheet with station names/locations, rainfall coverage, observation-day limitations, selected dates, missing-data handling, baseline definition and supported questions. If a catchment relationship cannot be established, retain explicit station-level wording. Do not quietly rebrand point observations as basin averages.

The handoff should contain a readable brief, selected rainfall data, documented transformations/priorities, source identity, review history, unresolved assumptions and clear replay instructions. Have the recipient find and explain these without the developer narrating. Have them state the exact next step the packet supports. Do not claim WAM/HEC-ResSim import compatibility unless it is actually tested.

**Done when:** the method summary reflects the review, one recipient completes the handoff task independently after any revisions, and remaining scientific limitations are stated in both the app and pitch.

## Phase 3: prove user value and the contribution of AI — September 12-16

### A small, honest user study

Use the reviewer for a technical evaluation and recruit two or three unfamiliar users for usability. Students/faculty outside the project are suitable proxy novice users, but label them as proxies. Prioritize one actual rural-serving operator or planner if available.

Task: inspect source limitations, prepare three scenarios, explain a selection, alter a priority, challenge or reject one candidate, export with private notes excluded, and explain the professional handoff.

Before starting, define success, the time limit, permitted help and error categories. Use a reasonable comparison workflow chosen with the reviewer: an existing spreadsheet/process or a supplied basic template with the same inputs and requested outcome. Do not force the comparison participant to build an entire application from scratch.

Where participants complete both methods, use matched but different cases and vary the order to reduce learning effects. Record actual times, completed steps, critical errors, assistance and comprehension. With a tiny sample, present individual results and limitations rather than broad productivity or water-savings claims.

Proposed usability target: at least two of three proxy novices complete the core task without coaching within 15 minutes, all can explain that the output is not a reservoir forecast, and no participant accidentally shares private notes. If only two participate, report two; do not alter the denominator to hide an unsuccessful session. Fix the largest misunderstanding and rerun with a fresh case where possible.

### Demonstrate why scenario grouping helps

Reuse the existing multiple-profile evaluation as a starting point. Compare equal-size shortlists from BASIN, score-only ranking, seeded random selection and a simple deterministic diversity rule such as farthest-first selection. Use identical candidate pools and documented seeds.

Have the reviewer define useful distinctions before seeing method identities: examples might include duration, seasonal timing and the station pattern of deficits. Show anonymous method outputs in varied order, then ask which set exposes useful differences and why. Record features missed, redundant scenarios, priority tradeoffs and review time.

Group coverage is descriptive because BASIN explicitly selects group representatives. Do not use it alone as proof of usefulness. Keep at least one case unseen during tuning. If a simple baseline performs as well or better, report that result and explain the product's workflow benefit honestly; do not tune repeatedly to manufacture an AI win.

**Done when:** the pitch contains an actual observed example of usefulness, or states clearly that usefulness is still being tested. No fabricated speedup or professional endorsement remains.

### Community participation: the critical external dependency

By September 10, the team should seek a short conversation with a rural-serving operator/planner through its existing reviewer or school network. The useful ask is a 20-minute task review, not a sweeping endorsement.

Capture the person's real constraint, the change requested, the change made and their response. They should influence something substantive: a ranking priority, terminology, the report's next-step request, or data-sharing behavior.

If no operator can participate by September 16, freeze the claims at “reviewer-informed prototype with proxy usability testing.” Explicitly describe intended rural beneficiaries and the next pilot, but keep real community validation pending. This limits the achievable Community Centeredness and Impact case; it cannot be repaired with stronger marketing language.

## Phase 4: prove deployability and account for resources — September 16-19

- Use a clean or freshly prepared account/device for setup. Document Python/WebView2, dependencies, disk use, and support steps. The embedded assistant requires no model installation. Include the entire release footprint, not only the launcher executable.
- Freeze the core on September 17. Rebuild the release, regenerate the demo packet and backup recording from that release, and identify source/dependency versions. Afterward accept only fixes for correctness, privacy, failures or critical usability; rerun affected checks.
- On the actual presentation laptop, run three consecutive complete workflows with Wi-Fi disabled, including fresh launch, edit/rejection, review, export and replay. Test the projector, sleep/resume, restore, embedded chat and Quick Queries, and recovery from a failed PDF build. Do not let a report failure discard the valid rainfall packet.
- Record cold-start time, repeated core computation time, peak memory where measured, and embedded assistant latency. Measure installation footprint separately from runtime performance.
- If a suitable energy meter is available, use repeated runs and an idle baseline, reporting the method and instrument resolution. Otherwise show an assumption-based range clearly labeled as such. Include a short water-footprint accounting note: which direct/indirect components are known and which are unmeasured. Offline runtime does not imply zero total water impact.
- Run the existing full suite and the focused regressions for the identified report/assistant/privacy cases. Recheck source data identity, fresh packet replay and current implementation identity. Passing tests do not replace the human exercises.

**Done when:** another teammate can set up and demonstrate the frozen release from the instructions; three actual-laptop offline runs succeed; the current packet replays; costs and resource claims match measurements or explicitly labeled estimates.

## Phase 5: present the evidence clearly — September 18-20

Confirm the organizer's presentation length, submission mechanism and A/V requirements immediately; neither supplied August 10 document establishes a three-minute slot. Prepare modular material and fit it to the actual slot.

Suggested presentation allocation:

| Portion | Content |
|---|---|
| First 15% | One specific user, a documented planning constraint, and the task BASIN helps them complete. |
| Next 45% | One complete demonstration: inspect evidence, see distinct candidates, change a priority, challenge a choice, approve reviewed content, export. |
| Next 20% | Actual user/reviewer findings and one honest shortlist comparison. |
| Final 20% | Local deployment evidence, community control, scientific limits, and the next pilot. |

Use a small deck with a source-backed problem slide, a workflow view, the user-study result, the specific innovation comparison, and deployment/next steps. Keep detailed architecture, reservoir illustrations, scoring formulas and evidence tables in backup material. Use permissioned quotations and identify sample sizes and reviewer roles accurately.

Conduct two mock judging sessions with people unfamiliar with the code. Ask them to interrupt and challenge geography, community relevance, AI necessity, validation, privacy and verification scope. Each team member must be able to explain these boundaries. End by asking the audience to explain BASIN back in their own words.

**Done when:** the story fits the actual time slot, two unfamiliar listeners accurately explain the value and limits, all three teammates can answer the central questions, and the frozen backup recording demonstrates the same claims as the live build.

## Dated milestones and cut rules

| Deadline | Reviewable milestone | If it misses |
|---|---|---|
| September 9 | Team owners, reviewer sessions requested, organizer-format clarification started, claim ledger established. | Reduce optional work before touching the core workflow. |
| September 11 | Correct report path; honest verification labels; assistant bounded or omitted from the primary demo. | Use the corrected rainfall brief as the primary output; keep the optional reservoir view clearly illustrative. |
| September 13 | First expert feedback incorporated; one candidate handoff independently attempted. | Narrow claims and fix the recipient's biggest blocking issue. |
| September 16 | User/proxy study and shortlist comparison recorded; community-contact outcome known. | Report the actual evidence and unresolved gaps. No invented speedup, endorsement or partnership. |
| September 17 | Core feature freeze. | Cut noncritical functionality; preserve a stable end-to-end path. |
| September 19 | Actual-device release gate and fresh replay pass. | Repair only critical failures and regenerate affected artifacts; use the last validated build if necessary and describe its actual capabilities. |
| September 20 | Final timed rehearsal, deck, evidence appendix, recording and offline kit ready. | Prefer the verified recorded workflow over an unreliable live branch. |
| September 21 | Travel and final logistics; avoid new dependencies or feature changes. | Follow organizer instructions. |
| September 22 | Present the verified release and its measured evidence. | Clearly label any fallback demonstration. |

## What to defer

Defer calibrated reservoir forecasting, multi-year hydrologic extensions, new geographic models without expert review, additional LLMs, cloud integrations, wildfire/agriculture feature expansion, multiplayer collaboration, and cosmetic redesign beyond readability fixes. Keep the existing illustrative reservoir experiment within its chosen scope. Each new capability would create evidence and reliability obligations during the remaining preparation window.

## Final go/no-go checklist

- [ ] Current public claims agree with the release and evidence ledger.
- [ ] No hard-coded outcome, unsupported policy guarantee or implied professional certification remains.
- [ ] All outputs respect consent and disclose the correct verification scope.
- [ ] The current release and packet pass software/replay checks, including the newly identified edge cases.
- [ ] Reviewer qualifications, feedback, disagreements and actual validation limits are documented.
- [ ] User/proxy study results and baseline conditions are recorded honestly.
- [ ] Community participation is demonstrated or clearly identified as pending.
- [ ] The novelty comparison explains useful outcomes and tradeoffs rather than only cluster coverage.
- [ ] Actual-device operation, fallback, footprint and setup are documented.
- [ ] Every teammate can explain the product, evidence, limits and next step within the confirmed format.

The project earns a stronger judging case when these boxes are backed by artifacts and observations. Checking the boxes without their evidence does not complete the plan.

## Code and workflow refinement — September 8 follow-up

The code review suggests that professional clarity requires explicit task boundaries and predictable state changes. Some foundations already exist: four labeled stages, example entry, human review, revision invalidation and a core workspace model. Refine these foundations instead of adding another parallel navigation system. The recommendations below are proposed changes, not implemented behavior or findings from a new live visual inspection.

### One complete analysis journey

| Stage | User task | Main content | Primary action |
|---|---|---|---|
| Data and purpose | Identify the preparation task, station observations and their limits. | Analysis title, purpose, source coverage, station-level geography and data-quality summary. | Continue to scenarios |
| Compare scenarios | Understand alternative rainfall conditions and why they were selected. | Three initial scenario cards, one main comparison chart, visible priorities and a concise explanation of differences. | Review these scenarios |
| Review choices | Inspect assumptions and decide whether to include each current revision. | Source-to-transformation explanation, focused metrics, public rationale, unresolved issues and revision history. | Accept for packet / Exclude with reason |
| Prepare handoff | Review what will be shared and address incomplete review. | Exact report preview, accepted/excluded counts, consent summary, actionable blockers and verification scope. | Build handoff packet |

Allow movement backward and sideways. Guidance must not trap an analyst in a rigid wizard. Keep a persistent analysis identity and review summary across pages; distinguish “saved locally,” “accepted for packet” and “packet checks passed.” None means scientific certification.

The entry screen should offer “Try a worked example,” “Start a rainfall analysis,” and “Compare my rainfall CSV.” The CSV path currently supplies supporting comparison evidence, not a new numerical station driver for scenarios; its label and success message must make that relationship clear. Previewing, saving evidence and changing scenario rainfall must look like different actions because they have different effects.

### Make result explanations systematic

Every scenario detail view should show the same sequence:

1. **Original observations:** stations and actual historical dates.
2. **Scenario change:** an explicit transformation such as “retain 80% of daily rainfall at all selected stations.”
3. **Calculated result:** a principal chart with units and a clearly named comparison basis.
4. **Selection explanation:** which priorities and distinguishing features put it on the shortlist.
5. **Review decision:** current revision, evidence disagreements and inclusion state.

Example title, not a real measured result: “90-day July scenario · 20% less rainfall.” Keep the stable scenario ID nearby as a secondary identifier. Distinguish the original historical observations from the seasonal reference; they answer different questions. A ranking score is a priority measure, not a likelihood or drought hazard category.

Add a reusable “How this was calculated” disclosure to metrics, with source, date range, units, formula, reference and limitations. Use deterministic text from the current data. Present evidence kind (observation/assumption/calculation) separately from review state (needs review/accepted/excluded).

### Explain every meaningful change

Move candidate count, seed and clustering diagnostics into advanced settings. Move ranking controls into the scenario-comparison context. Provide an explicit preview-and-apply interaction with a before/after shortlist comparison. Preserve the existing behavior of keeping the reviewed shortlist until the user explicitly replaces it, and explain that distinction.

After a numerical edit, show what changed, the affected revision and why acceptance was cleared. After an evidence update, identify which scenarios need re-review. Starting another analysis should preserve the previous saved analysis and avoid silently carrying context or notes into an unrelated run. A restore operation should preserve unrelated appearance preferences and clear only analysis-specific UI state.

Show saving/saved/unsaved/error states accurately. Disabled exports need specific reasons and links to the affected items, not only an unavailable button. If PDF rendering fails, keep the current reviewed work and successfully verified data packet recoverable.

### Simplify the desktop layout

The current assistant opens by default and reserves approximately 485 pixels in `app.py`. Close it by default, retain a visible labeled entry, and open it contextually for the selected scenario. Use one secondary detail panel at a time; notes and assistance should not compete with the comparison chart.

Keep one dominant primary action in each task context, a consistent heading/metric/chart/detail hierarchy, readable spacing and restrained status styling. Put experimental reservoir views in a labeled secondary destination. Remove promotional badges, policy-certification styling and unexplained tool names from working screens.

Verify layouts at 1366×768 and 1920×1080, plus zoomed/narrow views and keyboard navigation. Status changes need readable text and accessible announcement behavior, not color alone. The interface should remain understandable without the tour. Reference patterns: [GOV.UK button hierarchy](https://design-system.service.gov.uk/components/button/) and [W3C status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html).

### Refactor code at the boundaries that cause inconsistent behavior

Keep the current Streamlit stack and core analysis implementation for the finalist sprint. Extract page rendering from `app.py` into small page modules as each workflow is repaired. Centralize shared scenario cards, metric explanations, review summaries, empty states and error messages.

Introduce one application-service boundary for actions such as changing priorities, editing rainfall, accepting a revision and building a packet. UI handlers should submit validated operations and render results. Use a controlled update-and-save path so failed persistence does not leave the interface falsely showing a committed state. Preserve the domain model's scientific and review invariants.

Create a validated report snapshot containing the chosen scenario revisions, numerical results, evidence references, review states, disclosure choices and applicable verification scope. PDF, Markdown and downloadable data should consume that same snapshot, with explicit differences in coverage. Avoid separate calculations, hard-coded conclusions or independent privacy decisions in formatters. Semantic replay should continue to recompute from source/audit evidence rather than merely trust the snapshot.

Separate UI navigation state from persistent analysis state. Replace scattered widget-key cleanup with explicit analysis-switch/reset handling. Store presentation strings centrally and format numbers only at the UI/report boundary. Keep exception handling specific and return actionable failure details while preserving existing work.

### Suggested implementation sequence

1. Repair report generation, privacy and scope; establish consistent report input data.
2. Add persistent analysis/review status and accurate change/save feedback.
3. Simplify the primary layout and entry paths; close the assistant by default.
4. Implement consistent scenario explanations and explicit priority previews.
5. Unify handoff preview, blockers, disclosure choices and artifact generation.
6. Extract page/service modules while changing those paths; preserve the existing engine and tests.
7. Validate a complete novice journey, switching/restoring analyses, edited approvals, export consent and render-failure recovery. Add targeted regression tests for these behavioral risks rather than testing every label or CSS choice.

Suggested comprehension checks: after generation the user can identify what data was used, what was changed, why the shortlist was selected, what needs review and what action comes next. After an edit they can explain why prior acceptance no longer applies. After export they can say what was shared and what was verified. Record misunderstandings and revise the workflow until these explanations are accurate without coaching.
