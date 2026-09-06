# Review of the supplied BASIN research

Reviewed 2026-09-06. This review takes precedence over the imported AI packet. It is a research assessment, not hydrologic validation or a determination of the City's currently declared restrictions.

The supplemental transcript is now corrected in [corrected_supplement.md](corrected_supplement.md). It also resolves Article XII versus VII, unsupported geography and capacity-cause claims, missing hyperlink targets, overbroad approval-preservation requirements and free-text export privacy.

## What is useful

The packet identifies a sensible evidence stack: NOAA precipitation, TWDB storage and regional planning, municipal policy, USGS flow and watershed boundaries, and U.S. Drought Monitor context. Its proposed source details, comparison view, export provenance, and analyst questions support the team's goal of reducing time spent reconciling conflicting evidence. Keep those ideas; verify each underlying claim before implementation.

The project remains a rainfall-scenario workbench. Historical rainfall windows and scaled precipitation do not establish runoff, future reservoir storage, a restriction date, intervention effectiveness, or the probability of drought. More sources help only when they answer a defined question and their scope and transformations are explicit.

## Corrections that block use of the original packet as approved evidence

| Finding | Correction and evidence | Required action |
|---|---|---|
| E001 identifies `P` as trace precipitation | NOAA defines `P` as missing presumed zero and `T` as trace. Preserve distinctions between trace, missing, failed quality and observed zero. [NOAA format documentation](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt). | Correct the register before using it in an importer or UI. |
| Snapshot missing dates are wrong | Re-reading all 38,352 local CSV rows finds Victoria `USW00012912` missing on **1996-03-07** and San Antonio `USW00012921` on **2023-06-21**. Both have blank precipitation and `excluded=True`. The packet's 1996-02-18 and 2011-04-18 are incorrect. | Use reproducible local snapshot checks, not the packet's audit numbers. |
| E008 misnames station IDs | `08210000` is Nueces River near **Three Rivers**, not near Mathis. `08206900` is **Choke Canyon Reservoir near Three Rivers**, not a Frio River near Tilden discharge gauge. [USGS station identity](https://pubs.usgs.gov/dds/wqn96cd/html/wqn/wq/region12/08210000.htm), [TWDB reservoir source](https://waterdatafortexas.org/reservoirs/individual/choke-canyon). | Validate site identity, variable, regulation, location, record coverage and relation to the reservoir before selecting any flow series. These identity checks do not establish gauge suitability. |
| E009 proposes unverified watershed mappings | The packet inconsistently treats six-digit values as HUC8. HUC8 requires eight digits; names alone do not establish upstream contribution. Its specific basin-code assignments have not been validated. [USGS WBD](https://www.usgs.gov/national-hydrography/watershed-boundary-dataset). | Obtain official polygons and document catchments, outlets and station relationships. Do not copy its mapping into code. |
| Drought categories are shifted | Official example indicator percentile ranges are D0 20.01–30, D1 10.01–20, D2 5.01–10, D3 2.01–5 and D4 0–2. D0 is abnormally dry. These are illustrative indicator ranges, not a rule to turn one station's rainfall into an official USDM category. [USDM classification](https://droughtmonitor.unl.edu/About/AbouttheData/DroughtClassification.aspx). | Remove the packet's incorrect <=20/10/5/2/1 mapping. |
| E007 invents an exact June 1 effective date | The supplied PDF cover says amended June 2026. Visual inspection of PDF page 60 shows Ordinance 033940 approved **June 2, 2026**, with effective-date stamp **June 8, 2026**. | Record those as dates visible in the supplied artifact; verify current applicability with the City before operational use. |
| Case-study storage agreement is overstated | Arithmetic using the packet's quoted volumes gives `378337 / 918882 * 100 = 41.17%` for two reservoirs and `517292 / 1077857 * 100 = 47.99%` for three. This demonstrates denominator scope, not independently verified simultaneous agreement between City and TWDB. | Retain as a derived example with input provenance/date limitations. Do not describe it as a live observation or an independent corroboration. |
| Threshold arithmetic and default interpretation are unsafe | 41.2% is 1.2 percentage points above 40%, and 11.2 above 30%. The app's 0.48 starting value is labeled a scenario assumption associated with 2024; today's three-reservoir percentage does not prove where that assumption came from. | Do not automatically replace the scenario default with a live dashboard number. |
| Case 3 asserts unverified 2026 observations | Near-normal airport rainfall, upstream flow below the fifth percentile and declining storage are not supported by a reproduced, aligned time-series query. The bundled rainfall snapshot ends in 2025. | Label this an illustrative hypothesis until actual series, interval, baseline and computations are supplied. |
| Runoff and proxy claims exceed evidence | Numeric claims such as 40% less rain producing 85–95% less flow lack a reproduced local model. Precipitation alone does not measure evaporative stress or demand. Gridding does not eliminate all spatial bias. | Remove unsupported numbers; obtain a calibrated model and relevant validation before causal claims. |
| Metadata overstates review | Portal pages, datasets and policy documents are different evidence types. Original `reviewed`/`adopted` values, precise retrieval times, missing hashes, guessed dates and broad reuse claims are not independent verification. | Consult source_review.json. Keep unknown values unknown and distinguish discovery from content inspection. |

## Supplied City policy snapshot

Source: [wat-drought-contingency-plan.pdf](sources/wat-drought-contingency-plan.pdf), 77 PDF pages. Page numbers below are physical PDF pages, followed by printed page numbers. This is an extraction from the supplied version. The City's [water supply dashboard](https://www.corpuschristitx.gov/department-directory/corpus-christi-water/water-supply-dashboard/) is the official starting point for checking subsequent updates and declared status.

The plan defines the storage grouping as **Choke Canyon Reservoir plus Lake Corpus Christi**, not all reservoirs supplying the service area (PDF p9, printed p6). The City Manager/designee retains initiation and termination discretion. A computed threshold crossing must therefore not be labeled an official declaration.

| Condition | Initiation stated in supplied plan | Termination stated in supplied plan | Citation |
|---|---|---|---|
| Watch | Combined storage below 50% | Above 50% for 15 consecutive calendar days | PDF p9 / printed p6 |
| Stage 1 | Below 40% | Above 50% | PDF p10 / printed p7 |
| Stage 2 | Below 30% | Above 40%; Stage 1 becomes operative | PDF p10 / printed p7 |
| Stage 3 | Below 20% | Above 30%; Stage 2 becomes operative | PDF p10 / printed p7 |
| Level 1 emergency | City determination that total supply will not meet demands within 180 days; alternative supplies may alter timing | City determines total supply can meet regional demands for more than 180 days | PDF p10 / printed p7 |
| Level 2 emergency | City determines emergency causing demand to exceed supply and imminent inability to maintain required pressure, including infrastructure, production/distribution or contamination conditions | At City Manager/designee determination | PDF p11 / printed p8 |

The policy table targets 5%, 5%, 10%, 15%, 25% and 50% demand reductions for Watch, Stages 1–3 and emergency Levels 1–2 respectively (PDF p13 / printed p10). These are **targets**, not demonstrated savings. Level 1 curtailment may begin at 5% or greater (PDF p20 / printed p17); do not turn the 25% target into an invariant instantaneous effect. Surcharges and some other measures have approval conditions. Wholesale rules have their own section (PDF pp33–42), and exemptions, baselines and variances matter.

Additional source-quality concerns discovered during this review:

- PDF pp23–24 repeat printed page 20. Store physical page numbers and section identifiers to avoid ambiguous citations.
- Appendix C (PDF p75) visibly states a Phase III minimum release of **200,000 acre-feet per month**, while adjacent phases describe **2,000 acre-feet per month**. The rendered page confirms this is present in the supplied document, not merely an OCR substitution. Treat it as an unresolved source inconsistency; do not silently repair or implement either number without authoritative clarification.
- Appendix C's historical capacity figures (PDF p76) should not automatically replace contemporary storage denominators. Capacity definition and survey/version dates must accompany comparisons.
- Appendix B contains an older agreed order and Appendix C an operations plan. Their inclusion does not establish that every historic parameter is the current operating rule. Check amendment history and applicability separately.

Inspection limits: the packet's narrative and embedded JSON were reviewed, and the embedded register exactly matches the standalone JSON. All PDF pages were text-extracted and structurally inspected; the initiation/termination, target, response and appendix passages above received focused review. PDF pp10, 60 and 75 were also visually checked. This is not a line-by-line legal reconciliation of every surcharge, contract or ordinance clause, nor a complete hydrologic audit. Remaining questions are explicitly open.

## Planning and scientific questions still open

- Retrieve and review the actual adopted Region N plan chapters and appendices. An adoption index supports status, not every assertion about unseen chapters.
- Do not dismiss the entire older technical memorandum as superseded. The earlier reviewed TWDB correspondence distinguishes existing-system CCWSM work from WAM-based strategy analysis and allows separately approved variances. Confirm the adopted plan and approvals before asserting universal requirements.
- Verify exact extended-naturalized-flow file versions, basin periods and assumptions. Portal discovery does not establish that the packet's end year or publication date is correct.
- Confirm safe-yield reserve assumptions and matched operating conditions. Do not claim safe yield is universally strictly lower under every definition/model.
- Validate precipitation geography. Airport stations are provisional proxies; [NOAA nClimGrid-Daily](https://www.ncei.noaa.gov/products/land-based-station/nclimgrid-daily) is a candidate area-based comparison, not an automatically independent source because it derives from station observations.
- Supply the actual team submission and practitioner feedback before treating proposed features as agreed requirements.

## Work the group can start now

The main deliverable should be **one reproducible evidence packet for one defined reservoir system and historical drought interval**, showing observations, a reviewed scenario, relevant policy, and explained disagreements.

### Research and policy owner — B03/B07

- [ ] Confirm the two-reservoir scope with the team and analyst; list any additional supplies separately.
- [ ] Resolve the Appendix C release inconsistency and verify current ordinance applicability.
- [ ] Retrieve adopted Region N chapters and resolve model/variance claims with page citations.
- [ ] Produce one reviewed source entry per actual artifact; keep unresolved claims visibly pending.
- Done when: a teammate can locate and reproduce every quoted fact and distinguish policy text from interpretation.

### Data owner — B03/B04

- [ ] Correct gauge and watershed mappings using official metadata and GIS.
- [ ] Select a single overlapping historical interval for rainfall, storage and suitable flow observations.
- [ ] Record units, timezone/day boundaries, quality flags, revisions, gaps, capacity basis and source dependencies.
- [ ] Reproduce one apparent disagreement and show whether scope, date or definition explains it.
- Done when: another teammate can rerun the retrieval/transformation and obtain the same values from pinned inputs.

### Interface and export owner — B05/B06/B08

- [ ] Add source details showing source/version, effective and observation dates, geography, units, quality and citation location.
- [ ] Separate observed data, user scenario assumptions, model results and policy context visually.
- [ ] Add a comparison view that exposes denominator/time-window differences and unresolved conflicts.
- [ ] Extend export provenance only after agreeing the schema; include citations, assumptions and review state.
- Done when: an analyst can trace any displayed claim to its evidence without asking the presenter.

### Validation and demo owner — B02/B09/B11

- [ ] Establish the executable baseline using existing tests and the actual demo laptop.
- [ ] Have an analyst perform a concrete evidence-reconciliation task and record time, mistakes and unclear terminology.
- [ ] Rehearse one historical case plus one clearly labeled hypothetical rainfall scenario.
- [ ] Verify exports replay and cannot be mistaken for a water-supply forecast or official restriction declaration.
- Done when: the team can demonstrate the evidence workflow end to end and explain its limitations.

### Defer unless the above is complete

A defensible time-to-danger estimate needs a calibrated water balance, storage-area/evaporation relationships, inflows, demand, releases, alternative supplies, policy logic and out-of-sample validation. Historical rainfall alone cannot support it. Treat solution-impact comparisons as future modeling work until intervention assumptions and validation are available. Prioritize usable evidence and one well-supported case over collecting the largest number of links.
