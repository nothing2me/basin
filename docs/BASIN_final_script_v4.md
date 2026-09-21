# BASIN Final Script v4

Team NoMiMo: Noah Wilborn, Misha Stegall, Mohammed Asad Khan

Zoho “From the Ground Up” AI Hackathon finalist showcase

Updated September 20, 2026 to match `BASIN_final-1.pptx`, the current application, and the professor’s recommendations.

## Presentation rules

- BASIN is a **rainfall-scenario screening and expert-handoff tool**.
- Rainfall screening is the primary contribution. The storage view is an optional, uncalibrated assumption sensitivity.
- Use **replay-verified** only for the ZIP’s declared file and calculation checks.
- Human review is an internal screening decision. It is not hydrologic validation, engineering sign-off, or professional approval.
- Read live scenario IDs, scores, threshold days, output counts, and model status from the screen.
- The Watershed preset uses point gauges. It does not establish catchment-average rainfall, runoff, or reservoir inflow.
- K-Means reduces repetition. It does not prove that the selected scenarios are hydrologically distinct.
- If the storage demonstration is skipped, move directly from Slide 25 to Slide 27.
- Keep Slide 34 as a reference slide. Do not present it unless someone asks about image sources.

## Run of show

| Time | Slides | Lead |
|---|---:|---|
| 0:00–5:00 | 1–2 | Noah, Misha, Mo |
| 5:00–9:00 | 3–6 | Misha |
| 9:00–15:00 | 7–12 | Mo |
| 15:00–18:00 | 13–14 | Noah |
| 18:00–21:00 | 15–16 | Misha |
| 21:00–25:00 | 17–20 | Mo, then Misha |
| 25:00–37:00 | 21–27 | Team live demo |
| 37:00–40:00 | 28–29 | Mo |
| 40:00–48:00 | 30–33 | Misha |
| 48:00–50:00 | Buffer | Team |
| 50:00–60:00 | Q&A | Team |

## Slides 1–2: Team and product

### Slide 1 — NoMiMo

**NOAH**

“Good morning. I’m Noah Wilborn, the ‘No’ in NoMiMo. Thank you to Zoho and the judges for having us. I grew up in Corpus Christi, and I’m a senior at Texas A&M University–Corpus Christi studying computer science with a cybersecurity focus. Today I’ll drive the live demonstration so you can see BASIN work rather than only hear us describe it.”

“Misha is next.”

**MISHA**

“Good morning. I’m Mihail Stegall, or Misha, the ‘Mi’ in NoMiMo. I have lived in Corpus Christi my entire life, and I’m also a senior studying computer science with a cybersecurity focus. I’ll explain the evidence behind BASIN, why a person remains responsible for the review decision, and what the tool still needs to earn.”

“Mo can tell you why a cybersecurity student became interested in water.”

**MO**

“I’m Mohammed Asad Khan, the ‘Mo’ in NoMiMo. I’m an international student and a senior studying computer science with a cybersecurity focus. Noah and Misha grew up here. I did not, but the drought still affected all of us.”

“Security teaches us to ask where information came from, what changed, and what a result actually proves. Those questions became the foundation of BASIN.”

### Slide 2 — Basin Analysis and Scenario Intelligence Navigator

**MO**

“BASIN stands for Basin Analysis and Scenario Intelligence Navigator. It is a rainfall-scenario screening and expert-handoff tool. It helps a reviewer turn scattered rainfall evidence into a transparent shortlist for professional follow-up.”

“Misha will begin with why this problem matters to us.”

## Slides 3–6: The decision gap

### Slide 3 — Why this is personal

**MISHA**

“I have lived in Corpus Christi my entire life. Over the past two years, changing drought restrictions turned a technical issue into a daily concern. We watched reservoir percentages fall, heard different dates and explanations, and saw how difficult it was to understand what any one number meant.”

“This affected homes, businesses, and the future of the community that raised me. The question that stayed with us was not whether one number sounded alarming. It was which evidence a decision-maker should investigate next.”

### Slide 4 — Two dates reveal different conditions

**MISHA**

“On April 16, 2026, the City reported Lake Corpus Christi and Choke Canyon at 7.8 percent combined capacity.”

“By September 17, the reported values were 85.1 percent for Lake Corpus Christi, 22.5 percent for Choke Canyon, and 39.9 percent combined. These dated values describe very different conditions. They also show why one headline percentage cannot explain the entire water system.”

“Corpus Christi sits beside an ocean, but its drinking-water system depends on reservoirs, rivers, pipelines, treatment plants, contracts, and operating decisions. Salt water on the horizon does not become drinking water simply because the community needs it.”

### Slide 5 — One percentage cannot explain the system

**MISHA**

“Which sources are included? Which date does the number describe? Which reservoirs define the denominator? Which assumptions changed? What happened upstream? What deserves investigation next?”

“When the reasoning is difficult to follow, uncertainty turns into confusion or delayed action. That is the decision gap we wanted to address.”

### Slide 6 — The ethics behind BASIN

**MISHA**

“Cybersecurity taught us that trust should not depend on appearance. Evidence should be traceable. A system should reveal its limits. A reviewer should be able to inspect the reasoning.”

“We applied those principles to drought-scenario screening. BASIN preserves the evidence, records transformations, keeps assumptions visible, and leaves the decision with a person.”

“Before we show the workflow, Mo will define the terms we use.”

## Slides 7–12: Vocabulary

### Slide 7 — From rain to your tap

**MO**

“A rain gauge measures rainfall at one location. A watershed is the land draining toward the same river system. Inflow is the water that actually reaches a river or reservoir after rainfall, infiltration, evaporation, and other processes. A reservoir stores water for later use.”

“BASIN begins with rain gauges. It does not calculate the physical steps between rainfall and inflow.”

### Slide 8 — Rain is not water in the lake

**MO**

“This distinction is central to the project. Rain falls across a watershed. Dry soil can absorb much of it. A point gauge only measures its own location. Some rainfall may eventually reach a reservoir, but rainfall alone does not tell us how much.”

“BASIN uses rainfall as screening evidence. It does not turn a gauge measurement into a claim about reservoir inflow.”

### Slide 9 — Rainfall deficit and capacity

**MO**

“A rainfall deficit means less rain than the comparison baseline over a defined period. BASIN builds its scenarios from that concept.”

“Capacity describes how full a reservoir is relative to its storage capacity. The City reports the combined capacity of Choke Canyon and Lake Corpus Christi and uses that combined value in its drought-stage framework. BASIN’s storage experiment uses visible comparison bands, but it does not reproduce the City’s full current operating plan.”

### Slide 10 — How BASIN builds a scenario

**MO**

“A candidate is one possible dry stretch sampled from the rainfall record. By default, BASIN builds 300 candidates.”

“The seed makes the random sampling repeatable. The same data, settings, and seed produce the same candidate set.”

“The footprint determines which gauges participate. Regional uses eleven stations. Watershed uses ten point gauges inside the Nueces, Frio, and Atascosa drainage-basin footprint. Their location makes them more relevant for screening, but they do not establish catchment rainfall, runoff, or inflow.”

“Every candidate keeps the selected gauges synchronized on the same dates.”

### Slide 11 — Sorting the scenarios

**MO**

“BASIN describes each candidate using five shared rainfall features plus one normalized station-deficit feature for each selected station.”

“K-Means groups candidates with similar feature profiles. BASIN then selects one high-scoring representative from each of six clusters.”

“This aims to reduce repetition before human review. It does not prove that the six representatives are hydrologically distinct, and the cluster labels are descriptive statistical profiles rather than official drought classes.”

### Slide 12 — Words for trust

**MO**

“The assistant helps a user ask questions in plain language and routes supported questions to BASIN’s tools.”

“Human review means a person records an Include or Exclude decision and explains why. BASIN stores the reviewer’s name or team, role, time, and an automatic internal-review scope label.”

“Provenance is the record of where data came from and how it changed. A SHA-256 hash is a file fingerprint. Replay means another compatible BASIN installation can check the declared package and rerun its calculations.”

“When those checks pass, we call the ZIP replay-verified within its declared scope.”

“Noah will show where that workflow fits.”

## Slides 13–14: BASIN’s role

### Slide 13 — The screening gap

**NOAH**

“Formal tools such as the Texas Water Availability Models and HEC-ResSim answer specialized questions using detailed legal, operational, and engineering inputs.”

“Before a community commissions that work, someone still has to organize the first questions. Which historical rainfall patterns deserve attention? Are the shortlisted cases repetitive? What assumptions produced them? Can another analyst reproduce the handoff?”

“That early work can become scattered across downloads, spreadsheets, screenshots, and meeting notes. BASIN fills that screening gap.”

### Slide 14 — What BASIN does

**NOAH**

“BASIN does not tell a mayor when a city will run out of water. It does not replace a hydrologist, engineer, adopted drought plan, WAM, HEC-ResSim, or a formal water-supply model.”

“It creates reproducible rainfall-stress candidates, reduces repetition through clustering, records internal human review, and builds a replayable evidence packet.”

“The sentence we want you to remember is this: BASIN turns public rainfall observations and explicit assumptions into a transparent scenario shortlist for human review and professional follow-up.”

## Slides 15–16: Evidence and boundaries

### Slide 15 — Evidence that can be inspected

**MISHA**

“BASIN uses a pinned NOAA GHCN-Daily snapshot covering 1991 through 2025. The bundled registry contains eleven regional stations and ten additional gauges in the Watershed footprint.”

“The workflow checks structure, preserves station and observation dates, records transformations, and prevents station-identity collisions. Reviewed custom observations can travel with a saved workspace.”

“Coverage is reported honestly. The app and report separate actual observed station-days from proxy-filled values used in the analysis matrix. Padre Island, for example, is about 49.96 percent observed. Filled values remain labeled as filled.”

### Slide 16 — What the evidence can establish

**MISHA**

“These point observations support regional and watershed-footprint rainfall screening, reproducible comparisons, and traceable assumptions.”

“They do not establish catchment-average precipitation, reservoir inflow, operational shortage, or water-supply reliability.”

“That boundary matters. Information should not gain authority simply because it appears in a polished interface. BASIN preserves the evidence and its limitations before a scenario reaches the reviewer.”

“Mo will show how the candidates become a shortlist.”

## Slides 17–20: Scenarios and assistant

### Slide 17 — From candidates to cluster representatives

**MO**

“The scenario engine samples synchronized historical windows. It compares season-matched periods and preserves the rainfall-retention setting and repeatable seed.”

“The implemented clustering space contains five shared features plus one normalized deficit feature for every selected station. With the ten-gauge Watershed footprint, that means fifteen features.”

“K-Means groups similar feature profiles, and BASIN selects one high-scoring representative from each cluster. This creates a less repetitive shortlist for review. It does not validate hydrology.”

### Slide 18 — Candidate chart

**MO**

“Every dot is a candidate. The columns show 90-, 180-, and 270-day windows. The vertical axis shows total rainfall deficit. Color represents cluster membership. The outlined circles mark scenarios selected for review.”

“This frozen chart came from a Regional run, which is why it shows the rehearsal ID B-091. Our live demonstration uses the Watershed footprint, so the live scenario ID and values may differ. We will follow the screen.”

“The chart shows how clustering reduces repetition. It does not tell us that any candidate is physically correct or likely to occur.”

### Slide 19 — Assistant analyst

**MO**

“The assistant is an optional way to ask about the current workspace in plain language. It can route supported questions to BASIN’s built-in tools.”

“The local Qwen model is optional. BASIN’s core workflow still works when it is unavailable.”

### Slide 20 — The tools own the calculations

**MO**

“A user asks a question. BASIN selects a supported tool. Application-owned Python performs the calculation, and the interface shows the returned values with their assumptions and limits.”

“This design narrows the risk of invented numerical answers, but we do not promise that an AI system can never make a mistake. Users can inspect the tool result or open the same function directly.”

**MISHA**

“The assistant helps ask the question. A person still decides whether the scenario belongs in the handoff.”

## Slides 21–27: Live workflow

### Slide 21 — Live workflow

**NOAH**

“We will inspect the evidence, generate a shortlist, ask why one scenario ranked, record a human decision, and build the handoff. If time permits, we will briefly open the storage experiment to demonstrate its limitations.”

**Action:** Switch to the frozen BASIN build. Use the reviewed backup workspace or recording only if the live application fails.

### Slide 22 — Inspect the evidence

**NOAH**

“This is the pinned NOAA rainfall snapshot running locally. The dashboard shows the 1991–2025 period, selected stations, source information, coverage lineage, and file identity.”

**Action:** Select the Watershed community footprint. Point to the ten selected point gauges and the observed-versus-filled coverage fields.

“These gauges are useful point references. We are not presenting them as a calibrated watershed precipitation product.”

### Slide 23 — Generate the shortlist

**NOAH**

“We are using 300 candidates, six cluster representatives, and seed 22. The visible weights prioritize severity, duration, concurrence, and summer timing.”

**Action:** Confirm Watershed is selected. Create rainfall scenarios. Read the live top scenario ID.

**MISHA**

“Each candidate keeps its source window, rainfall transformation, feature values, score contributions, and cluster identity. Concurrence means the selected gauges crossed their rainfall-stress definitions together. It does not establish inflow failure or a water shortage.”

### Slide 24 — Ask why a scenario ranked

**MO**

**Action:** Ask, “Why did [live scenario ID] rank first?”

“The response breaks the score into visible components. I am reading these values from the screen rather than from rehearsal notes.”

**If Qwen is confirmed active:** “Qwen interpreted the wording and selected the tool. BASIN’s Python function supplied the values.”

**If Qwen is inactive:** “The deterministic router recognized the request and called the same tool. The analysis does not depend on the language model.”

“For an unsupported or ambiguous question, BASIN should request clarification or direct the user to a tool rather than invent an answer.”

### Slide 25 — Human review

**MISHA**

**Action:** Open Review Selections. Enter the actual reviewer name or team and role. Enter: “Selected for handoff because this scenario combines a substantial rainfall deficit with summer timing; station suitability still requires hydrologist review.”

“BASIN does not convert a ranking into approval. Include and Exclude remain locked until the reviewer provides a substantive rationale.”

“The app records who made the decision and automatically labels its scope as internal rainfall-scenario screening. Inclusion means this scenario belongs in our handoff. It does not mean a hydrologist approved it.”

### Slide 26 — Optional storage limitations demonstration

**MISHA**

“We are now leaving the rainfall evidence and entering an illustrative storage-accounting experiment. This view uses configured capacities, rainfall-to-inflow sensitivity, seasonal evaporation, demand, pipeline, release, and storage-band assumptions.”

“The calculation is numerically checked, but it has not been calibrated to observed Nueces and Frio runoff, historical inflow, dynamic surface area, or actual system operations.”

**Action:** Select the intended scenario and the 35 percent illustrative start. Read the live scenario duration and displayed results.

**NOAH**

“Under these assumptions, the trajectory [read the live result]. Any threshold day is a model-window index. It is not a forecast date, restriction date, or hydrologic finding.”

“The evaporation value follows from the seasonal rates entered in the experiment. It is an assumption-driven result rather than a measured system loss.”

**Action:** Save a specific internal experiment-review note.

### Slide 27 — The handoff gate

**MO**

“BASIN will not build the handoff until every shortlisted scenario has an Include or Exclude decision.”

**Action:** If scenarios remain pending, enter a substantive batch rationale and use the batch decision. Choose note-sharing consent deliberately.

“A ranking is a suggestion. The handoff records the human decision, its rationale, and its internal scope.”

## Slides 28–29: Deliverables and replay scope

### Slide 28 — Companion deliverables

**MO**

**Action:** Click **Build replayable handoff**. Show the actual generated files and open the first PDF page.

“BASIN creates a replayable ZIP, a companion Executive Technical Brief PDF, a Markdown handoff brief, and a spreadsheet.”

“The PDF begins with the rainfall shortlist and review record. The storage experiment appears later as an uncalibrated assumptions appendix when it is included.”

“The ZIP contains the declared data, scenario definitions, audit records, and hashes needed for its replay contract.”

### Slide 29 — What replay-verified means

**MO**

“Replay-verified applies to the ZIP’s declared scope. BASIN checks the inventory and hashes, then replays the calculations covered by the package.”

“That result establishes internal consistency. It does not authenticate NOAA as an institution, create a digital signature, make files immutable, validate hydrology, or imply professional approval.”

“The PDF is a readable companion. It is generated separately and is outside the ZIP’s hash and replay contract.”

## Slides 30–33: Contribution, limits, and close

### Slide 30 — The governed combination

**MISHA**

“BASIN’s contribution is the way its parts work together.”

“It starts with reproducible local evidence. Clustering reduces repetition while keeping the criteria visible. The assistant routes questions to application-owned tools. Human review controls what enters the handoff.”

“Evidence enters through a structured, checked process. Transformations remain traceable. Scientific boundaries remain explicit.”

### Slide 31 — Confidence with honesty

**MISHA**

“The hardest drought question is often, ‘How much time do we have?’ BASIN should not answer that with false precision.”

“It should show the evidence, expose assumptions, compare a less repetitive set of rainfall stresses, preserve human judgment, and make the next professional analysis easier to reproduce.”

“We are not asking anyone to trust BASIN because we built it. We are giving them a way to inspect what it did and challenge what it assumed.”

### Slide 32 — The next evidence BASIN must earn

**MISHA**

“The next step is user and domain evidence. We need to observe intended users without coaching and ask hydrologists and utility practitioners to review station suitability and assumptions.”

“Operational use would require watershed-representative precipitation, calibrated rainfall-runoff and routing, observed inflow and storage validation, dynamic surface-area and net-evaporation calculations, actual transfers, releases and demand, uncertainty analysis, historical hindcasting, and independent professional review.”

“Those are future-development requirements. We should not rush them into a presentation claim.”

### Slide 33 — Close

**MISHA**

“Corpus Christi gave this work its purpose. The broader principle is simple: when decisions carry high stakes, people deserve evidence they can follow and assumptions they can see.”

“BASIN turns public rainfall observations and explicit assumptions into a transparent scenario shortlist for human review and professional follow-up.”

“We would like to leave you with two questions.”

“Would this packet help you identify and document rainfall scenarios worth carrying into a formal water-supply model? What additional data and validation would you require before relying on its outputs for an operational drought decision?”

“Thank you. We welcome your questions.”

### Slide 34 — Image references

Do not present this slide during the main talk. Keep it available for attribution questions.

## Q&A

### Does BASIN predict when Corpus Christi will run out of water?

**MISHA:** “No. BASIN creates and reviews rainfall-stress scenarios. Its storage view is an uncalibrated sensitivity experiment under displayed assumptions. It does not forecast reservoir levels, deliveries, safe yield, or official restriction dates.”

### What decision does BASIN support?

**MISHA:** “It supports the decision about which rainfall scenarios and assumptions deserve deeper professional analysis. It helps a reviewer compare candidates, record a rationale, and hand a reproducible packet to the next analyst.”

### Why is this AI?

**MO:** “K-Means groups hundreds of rainfall candidates so the reviewer sees fewer repetitive cases. The optional local language model routes plain-English questions to BASIN tools. Python performs the calculations.”

### Can the assistant hallucinate?

**MO:** “Any language model can make mistakes. We narrow that risk by keeping calculations in application-owned tools, validating tool arguments, and showing assumptions with the result. The workflow remains available without the model.”

### Why not use ChatGPT or another cloud model?

**MO:** “A general chat model does not automatically have BASIN’s pinned data, deterministic calculations, review gate, audit trail, or replay contract. In BASIN, chat is an optional interface over an application-owned workflow.”

### Why K-Means, and why six clusters?

**NOAH:** “K-Means gives us a repeatable way to group candidates in a visible feature space. Six is a configurable review-size choice for this prototype, not a scientifically optimal number. The shortlist still requires human review.”

### Are five matched historical windows statistically valid?

**NOAH:** “Five is the minimum gate for reporting an empirical comparison. It remains a small sample and does not establish statistical validity, event probability, or forecast skill.”

### What does replay-verified mean?

**MO:** “It means the ZIP’s declared files match their hashes and the covered calculations replay consistently. It does not mean signed, immutable, scientifically validated, or professionally approved.”

### Is the PDF replay-verified?

**MO:** “No. The PDF is a readable companion generated beside the ZIP. It is outside the ZIP inventory and hash contract.”

### How complete is the rainfall data?

**MISHA:** “Coverage varies by station. BASIN now reports raw observed days and percentage separately from proxy-filled analysis values and remaining gaps. Padre Island is about 49.96 percent observed.”

### Who performed the human review?

**MISHA:** “The exported record identifies the actual team member or team name and role. The scope label says internal scenario screening. It should not be interpreted as external hydrologic approval.”

### Did the professor validate BASIN?

**MISHA:** “No. Her feedback helped us correct the product boundary and presentation language. She explicitly said her review must not be represented as hydrologic validation or professional approval.”

### Why use the Watershed footprint?

**NOAH:** “It uses ten point gauges located inside the Nueces, Frio, and Atascosa drainage-basin footprint, which makes them a more relevant screening set than distant regional references. They still do not establish catchment-average rainfall, runoff, or inflow.”

### Why did rainfall reductions barely change ending storage?

**NOAH:** “That result exposes a limitation. Under the configured experiment, fixed demand and evaporation assumptions dominate the trajectory, while the assumed rainfall-to-inflow response is weak. We present that as assumption sensitivity, not as a hydrologic conclusion.”

### What would BASIN need for operational use?

**MISHA:** “It would need representative precipitation, calibrated rainfall-runoff and routing, validation against observed inflow and storage, dynamic net evaporation, actual demand and operating records, uncertainty analysis, hindcasting, and independent review by utility practitioners and hydrologists.”

### Is Qwen open source?

**MO:** “The optional model has its own Qwen license, separate from BASIN’s code license. We describe each component under its actual terms rather than treating the whole package as one license.”

### Does the installer contain Qwen?

**MO:** “No. The installer is about 200 megabytes. The optional model is a separate download of roughly 2.1 gigabytes. The core workflow works without it.”

### Does BASIN work offline?

**MO:** “The pinned-data workflow runs locally. We will only claim the exact offline behavior demonstrated on the frozen presentation laptop. Optional downloads and external links require a network connection.”

### How do you know the shortlist is not cherry-picked?

**NOAH:** “The data snapshot, candidate settings, seed, features, weights, cluster identities, and scores are recorded. The same inputs reproduce the same run. That makes the selection inspectable, though it does not make the choice scientifically optimal.”

### What is the strongest contribution?

**MISHA:** “Transparency and handoff discipline. BASIN preserves the evidence, transformations, assumptions, review decisions, and replay scope so a professional can see what deserves deeper analysis.”

## Final preflight

- Confirm the event timing.
- Confirm the submitted team spelling: NoMiMo or NoNiMo.
- Freeze the application commit, installer, deck, script, and generated backup packet together.
- Test the exact presentation laptop offline.
- Confirm the live footprint, candidate count, shortlist count, seed, and scenario duration.
- Confirm the reviewer name/team and role to enter on stage.
- Confirm whether Qwen is active. Use only the matching branch.
- Keep a reviewed workspace, generated packet, and screen recording ready.
- Never quote a rehearsed scenario ID, score, threshold day, PDF page count, or artifact hash when the live screen differs.
