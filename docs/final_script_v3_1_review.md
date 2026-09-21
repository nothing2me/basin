# BASIN Final Script v3.1 review

Reviewed: 2026-09-20

## Overall assessment

The available script is substantially aligned with the professor's recommendations. Its strongest sections clearly define BASIN as a rainfall-scenario screening and expert-handoff tool, limit replay verification to the ZIP's internal-consistency contract, distinguish observations from filled values, identify human review as internal, and place the storage experiment behind the rainfall workflow.

The pasted attachment ends during Q2 in the Q&A section, so this review covers the text available through that point. The remaining Q&A should receive the same claim audit before the script is frozen.

## Required wording changes

1. **Slides 11 and 17: do not promise six scenarios that are physically or genuinely different.** K-Means groups candidates in the implemented feature space and BASIN selects one representative per cluster. Rename Slide 17 from “six different stress shapes” to “300 candidates to six cluster representatives.” Replace “Six scenarios that are actually different from each other” and “Six scenarios that look different from each other” with:

   > BASIN selects one high-scoring representative from each of six statistical clusters. This aims to reduce repetition; it does not prove that the six scenarios are hydrologically distinct.

2. **Slides 10 and 15: narrow the watershed wording.** Replace “basins that feed our reservoirs,” “reservoir-relevant footprint,” and “rainfall inside the basins that actually feed” with:

   > The Watershed preset uses ten point gauges located within the Nueces, Frio, and Atascosa drainage-basin footprint. Their location makes them a more relevant screening set, but they do not establish catchment-average rainfall, runoff, or reservoir inflow.

3. **Slide 9: avoid an uncited claim about the current official drought-stage rule.** Replace “the combined number is what sets the drought stages” unless the slide cites the current adopted City plan. A safe version is:

   > The City reports combined storage as an important planning indicator. BASIN's storage bands are illustrative assumptions, not a reproduction of the current adopted drought plan.

4. **Slide 18: avoid treating the cluster names as physical drought types.** Replace “each pile has a name that says what kind of dry spell it is” with:

   > Each cluster receives a descriptive label based on its statistical feature profile. The label helps comparison; it is not a meteorological drought classification.

5. **Slide 20: soften control claims about the assistant.** Replace “The assistant can't quietly change a number” with:

   > BASIN's tools perform the calculations and return the values shown. The assistant helps route the question, and users can inspect the tool result and assumptions.

6. **Slide 25 and demo preflight: there is no editable review-scope field.** The current app asks for reviewer name/team and reviewer role; it records the internal review scope automatically. Rehearse those two fields and explain the automatic scope label instead of telling the presenter to enter a scope.

7. **Slide 30: replace “validated process.”** Structure and integrity checks are not scientific validation. Use:

   > Evidence enters through a structured, checked process. Transformations remain traceable, and scientific boundaries are stated explicitly.

8. **Slide 31: avoid “genuinely different stresses.”** Use:

   > It should show the evidence, expose the assumptions, compare a less repetitive set of rainfall stresses, preserve human judgment, and make the next professional analysis easier to reproduce.

9. **Closing question: use the professor's wording exactly.** Replace the current two-sentence paraphrase with:

   > Would this packet help you identify and document rainfall scenarios worth carrying into a formal water-supply model? What additional data and validation would you require before relying on its outputs for an operational drought decision?

10. **Slide 33: remove the unresolved production note.** Apply `docs/final_slide_copy.md` to the real deck and make the spoken close match it before release freeze.

## Deck and rehearsal corrections already identified by the script

- Slide 13 still has an “IMAGE TO ADD” placeholder.
- Slide 17 should remove “Eight visible feature dimensions.” For the ten-gauge Watershed footprint the implementation uses fifteen features, but the safest slide wording is “five shared features plus one station-deficit feature per selected station.”
- Slide 19 should replace “Hard data—not hallucinations” with “Numbers come from tools, not guesses,” and should avoid any zero-hallucination promise.
- Slide 20 should say “BASIN picks a built-in tool.”
- Slide 22 has “Explicit noticies”; use “Explicit notices.”
- Slide 26 must use the live scenario duration, such as “within the 270-day modeled window,” rather than a fixed 90- or 365-day statement.
- Confirm whether the team name submitted to Zoho is **NoMiMo** or **NoNiMo**.
- Confirm the organizer's 50-minute presentation and 10-minute Q&A timing.

## Strong sections to keep

- The “rain is not the same as water in the lake” explanation is clear and central to the product boundary.
- The explanation of point gauges versus inflow is accessible to a nontechnical audience.
- The review section correctly states that inclusion is an internal screening decision rather than approval.
- The storage demonstration repeatedly labels its results as assumption-driven and optional.
- The ZIP/PDF distinction is unusually clear and should stay.
- The Q&A answers on forecasting, replay scope, and AI limitations are concise and defensible.

## Final rehearsal rule

Read every live value from the screen. Do not memorize scenario IDs, scores, threshold days, page counts, Qwen status, or artifact hashes. Freeze the deck, script, application commit, and generated artifacts together only after the final laptop rehearsal.
