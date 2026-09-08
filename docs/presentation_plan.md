# BASIN finalist showcase presentation plan

Updated: 2026-09-07 | Product baseline: `f78d692` on `main`

## Confirmed event context

- Event: From the Ground Up 2026 AI Hackathon finalist showcase
- Location: Pleasanton, California
- Date: September 22, 2026
- Expected travel day: September 21, subject to later organizer instructions
- Team: Noah Wilborn, Mohammed Asad Khan and Misha Stegall
- Judging themes: impact, feasibility, community centeredness, innovation and clarity

The supplied organizer materials do not specify the finalist presentation length, required deck/demo format, A/V setup or exact submission mechanism. The three-minute demonstration below is the team's compact working version, not an official time limit. Confirm and record the actual format under TODO B11.7 before final rehearsal.

## What BASIN is

BASIN helps a Region N or rural-serving water analyst turn public rainfall evidence into a small set of transparent rainfall-stress scenarios, challenge assumptions, and hand a reviewable packet to a hydrologist for deeper analysis.

BASIN does not predict reservoir levels, water deliveries, safe yield, shortage probability or restriction dates. Its three airport stations are provisional regional proxies pending practitioner review. The optional reservoir view is a separate uncalibrated illustration and is excluded from the evidence packet.

The sentence judges should remember:

> BASIN turns a disputed starting point into a transparent request for the right expert analysis.

## The presentation argument

1. **Problem:** Region N's current planning model does not include newer conditions after its hydrologic record ends, while smaller providers have limited resources for exploratory specialist work.
2. **Current gap:** The step before formal modeling can begin with scattered evidence, conflicting assumptions and no shared explanation of which stress patterns deserve attention.
3. **Product:** BASIN uses public observations, deterministic scenario construction, local KMeans grouping and explainable priorities to create a diverse shortlist.
4. **Human control:** A user can compare, challenge, edit, reject or replace scenarios. Changed rainfall invalidates prior acceptance.
5. **Handoff:** The export contains rainfall, assumptions, evidence, unresolved issues and audit history for expert review.
6. **Boundary:** Verification establishes internal consistency within its published contract. It does not certify scientific validity or professional approval.

## Compact three-minute demonstration

This route should fit one presentation viewport per stage after B13. Until that refactor lands, use the current Data, Workspace, Review and Exports navigation names.

### 0:00-0:25 - Frame the decision

Say: “A small provider does not need BASIN to declare a water emergency. They need a clear way to tell a hydrologist which plausible rainfall stresses should be examined first and why.”

Show the BASIN title and the four-stage workflow. State that the tool runs locally and uses public NOAA rainfall plus user-controlled priorities.

### 0:25-0:55 - Check the evidence

Open **Data**.

- Identify the 1991-2025 public snapshot and its recorded hash.
- Point out that Corpus Christi, Victoria and San Antonio airports are provisional regional proxies.
- If demonstrating a local upload, show the preview and same-date public comparison only. State that it is descriptive and not yet persisted into scenario packets.

Do not describe station coordinates as catchment coverage or an affected-area map.

### 0:55-1:30 - Build and compare scenarios

Open **Workspace** and generate the prepared run.

- Use 300 candidates, six scenarios to review and seed 22.
- Explain that historical windows remain synchronized across selected stations.
- Show two or three scenarios and “Why this scenario ranked here.”
- Change one illustrative priority and show that scores can change while the reviewed shortlist stays in place until an explicit rebuild.

Say: “The clustering narrows repetition; the analyst still controls what survives.”

### 1:30-2:15 - Challenge and review

Open **Review**.

- Trace one metric to its source and limitation.
- Record or show one unresolved assumption.
- Edit one scenario or apply a prepared multiplier and show that prior acceptance clears.
- Accept the revised rainfall content and reject another scenario with a reason.

Say: “Acceptance records the analyst's rainfall-content decision. It is not engineering sign-off.”

Keep the reservoir experiment out of the compact route. If judges ask, show it later with the complete illustrative disclaimer.

### 2:15-2:45 - Produce the handoff

Open **Exports**.

- Show which evidence and unresolved issues will be included.
- Leave private notes excluded.
- Build the packet and identify `daily_rainfall.csv`, `shortlist.csv`, the readable brief and audit record.
- State that replay checks dates, stations, transformations, revisions, accepted IDs, calculations, evidence links and privacy defaults.

Say: “The packet gives the recipient both the proposed rainfall and the reasons to question it.”

### 2:45-3:00 - Close on value

Say: “BASIN does not replace the hydrologist. It helps rural-serving communities arrive at that conversation with explicit priorities, visible uncertainty and evidence another person can inspect.”

Name the next validation step: TAMUCC practitioner review and an independent recipient test.

## Expansion modules for a longer official slot

Use only the modules that fit the organizer-confirmed schedule. Preserve the compact demo as one uninterrupted section.

### Problem and community context - 1 to 2 minutes

- Explain the post-2015 planning-record gap using the submitted problem statement.
- Describe the intended users: Region N technical participants, consulting hydrologists, WCIDs and rural-serving wholesale providers.
- Summarize the three anonymous discovery responses as a small convenience sample: conflicting assumptions, difficult-to-audit evidence, desire for explanations and local control.
- Do not claim those responses are product validation or representative statistics.

### Method and architecture - 1 to 2 minutes

- Public NOAA GHCN-Daily snapshot, kept local with a recorded hash.
- Complete synchronized historical windows; no silent zero imputation.
- Rainfall-retention transformation, not streamflow scaling.
- Local KMeans groups similar feature patterns; deterministic scoring applies user weights.
- The diverse shortlist covers groups before using global score fills.
- Saved comparisons and KMeans labels are recorded/hash-checked but excluded from semantic replay certification.

### Verification and privacy - 1 minute

- Local loopback application with no product LLM or cloud inference.
- Private notes excluded from packets unless explicitly included.
- Bundle verifier checks internal consistency and current source identity.
- Unsigned hashes do not prove source authenticity or prevent coordinated fabrication.

### Validation and next steps - 1 minute

- Automated suite, fresh-checkout snapshot, offline smoke and packet replay pass on the development machine.
- Practitioner catchment/method review, recipient interoperability, actual presentation-laptop testing and measured user benefit remain open.
- The local upload comparison is useful descriptive review but is not yet part of scenario persistence or packet replay.

## Three-person speaking lanes

Each teammate must claim their own lane; these are roles rather than assigned names.

| Lane | Responsibilities |
|---|---|
| Problem and community | Open with the specific Region N decision gap, intended users, community control and impact boundary. |
| Product and method | Explain data, scenario construction, grouping/ranking and the live build/compare steps in plain language. |
| Review, verification and close | Demonstrate challenge/edit/export, state verification limits, describe validation status and lead questions. |

Every teammate should be able to explain the complete workflow, proxy-station limitation, privacy choice, clustering rationale and reservoir boundary.

## Judging-criteria map

| Criterion | Demonstrated evidence | Honest limit or proposed benefit |
|---|---|---|
| Impact | Submitted Region N planning gap and three anonymous discovery responses; packet focuses a request for analysis. | Faster or fairer planning is a proposed benefit until a baseline user exercise measures it. |
| Feasibility | Laptop-scale local implementation, 105-test suite, offline calculation rehearsal, open CSV/Markdown/JSON outputs. | Presentation-device and direct downstream-model interoperability tests remain open. |
| Community centeredness | Users control priorities, edits, rejection, final shortlist, unresolved dispositions and private-note sharing. | Practitioner sessions must show that intended users understand and value those controls. |
| Innovation | Diverse scenario grouping plus auditable human challenge creates a bridge between public evidence and expert modeling. | KMeans does not make a scenario scientifically correct and should not be sold as autonomous judgment. |
| Clarity | Four-stage workflow, plain-language labels, decision summary and explicit recipient action. | B13 usability refactor and unassisted testing remain required before claiming success. |

## Claims to show and claims to avoid

### Supported in the demonstration

- Public snapshot identity and provisional station metadata
- Transparent rainfall construction and matched rainfall reference
- Deterministic grouping/ranking on a fixed candidate pool
- Side-by-side scenario and evidence comparison
- Human edit, rejection, approval invalidation and unresolved conflict
- Privacy-aware evidence packet and declared replay scope
- Local runtime with browser fallback and a tracked native executable

### Do not claim

- Catchment-calibrated rainfall, streamflow or reservoir inflow
- Drought probability or official USDM category
- Forecast reservoir levels, safe yield, deliveries or restriction dates
- Verified WAM Run 3 or HEC-ResSim direct import
- Engineering sign-off, source authenticity or professional certification
- Measured community outcome, time savings or environmental benefit
- GIS pipeline/corridor overlays, drought heatmap playback, climate-warming controls or data-center demand stressors
- Four team members, a team hydrologist or credentials no teammate actually holds

## Judge questions and concise answers

**Why is this AI?**
BASIN uses local unsupervised KMeans to group many scenario patterns, then deterministic scoring and diversity rules to produce an explainable shortlist. The user controls priorities and the final decision.

**Why not give the data directly to a hydrologist?**
That remains the final destination. BASIN structures the earlier conversation: which plausible stresses to examine, why they were chosen, what changed, and which assumptions remain disputed.

**Are the airport stations the actual source catchments?**
No. They are provisional regional demonstration proxies. A practitioner must choose suitable gauges, gridded products or catchment aggregation before operational use.

**Does a 40% rainfall-retention scenario mean 40% streamflow?**
No. Rainfall retention changes the rainfall series only. Rainfall-runoff translation requires a separate reviewed hydrologic model.

**Does the reservoir animation predict restrictions?**
No. It is an uncalibrated educational accounting experiment with illustrative coefficients and thresholds, excluded from the packet and verification claim.

**What does “verified” mean?**
The replay confirms internal agreement among the packet's files, source snapshot, transformations, revisions, accepted IDs, calculations, evidence links and brief. It does not prove sources are true or scientifically suitable.

**Does the product send private data to AI services?**
No product LLM or cloud inference is used. The app runs on loopback and keeps local notes/uploads on the device unless the operator explicitly exports them. Local storage is not encrypted.

**Can the packet be loaded directly into WAM or HEC-ResSim?**
That direct interoperability has not been tested. The current packet uses open CSV, JSON and Markdown for a hydrologist to inspect and adapt.

**What evidence shows usefulness?**
Discovery responses support the problem. Product usefulness still requires the planned novice, practitioner and recipient exercises; the team does not claim measured improvement yet.

## Final preparation checklist

- [ ] Record the organizer-confirmed presentation length, deck/demo format, A/V constraints and submission mechanism.
- [ ] Claim three speaking lanes and rehearse handoffs.
- [ ] Complete B13 labels, decision summary and one-viewport guided path.
- [ ] Have the TAMUCC professional review geography, method and reservoir wording.
- [ ] Have a recipient open and interpret the CSV/brief without coaching.
- [ ] Rebuild and run the accepted executable on the presentation laptop.
- [ ] Rehearse with network disabled and the actual projector.
- [ ] Confirm downloads, saved-session recovery, occupied-port behavior and browser fallback.
- [ ] Review AI-use disclosure and third-party materials as a team.
- [ ] Build one final packet and manually inspect its assumptions, unresolved issues, privacy state and replay result.
- [ ] Record a backup video from the exact accepted build.
- [ ] Copy the versioned release, packet, deck and video to the agreed backup media.

## Source of truth

Use `docs/claim_inventory.md` for current claim status, `docs/demo_runbook.md` for the compact interaction sequence, `docs/verification_scope.md` for packet verification boundaries, `docs/methodology.md` for scientific definitions, and `TODO.md` for acceptance state.

The Stage 1 answers and tie-breaker response in `docs/submission_record.md` are historical submitted wording. Preserve them as submitted; address unmet commitments through the task board and presentation boundaries rather than silently rewriting that record.
