# Corrected supplemental research handoff

Updated 2026-09-06. Owner: B03 research/evidence. This is the corrected replacement for the additional pasted “BASIN Research-Agent Brief & Decision-Ready Source Shortlist,” including its Master Link Directory. It supersedes that text's factual claims and proposed acceptance criteria. Original attachment SHA-256: 29dda1199afaa8113dc1d4232c4f56daf501a7e09c0ff3792a1ef3189acf327a.

The documentation correction is complete. Facts that cannot be established are explicitly removed, qualified or assigned a verification gate below; they are not silently promoted to verified findings. Application defects remain implementation tasks in [TODO.md](../TODO.md).

## 1. Product and minimum source stack

BASIN helps an analyst inspect, edit and select historical rainfall stress scenarios, then export an auditable packet for further professional analysis. An analyst or utility planner is the proposed user; the named utilities and consulting firms in the extra handoff are examples, not validated customers, partners or committed recipients. Selecting two or three scenarios is a proposed exercise, not a demonstrated user requirement. The September 18 freeze and September 19–20 rehearsal are planning targets, not official event rules.

| Use | Sources | Boundary |
|---|---|---|
| Numerical input now | Bundled NOAA GHCN-Daily precipitation | Existing verified snapshot and quality rules; no automatic data refresh. |
| Evidence context | TWDB storage, supplied City policy, USDM | Clearly distinguish observations, policy text and declared status. This proposal is not an implemented evidence tab. |
| Candidate validation | USGS flow/site metadata and official watershed polygons | Validate station, variable, upstream coverage and period before use. |
| Deferred model inputs | Naturalized flows, evaporation, demand and operating rules | Require a specified model, applicable approvals and validation. |

Whole-window resampling, clustering and user weighting do not produce drought probabilities or validated reservoir forecasts. A proposed hydrologist brief should describe rainfall transformations and request evaluation in the recipient's applicable model; it must not claim engineering compatibility merely because it is a ZIP or CSV.

## 2. Geography and observation quality

Keep four separate boundaries: the Region N planning area, utility service/customer area, contributing reservoir catchments, and imported supplies/conveyance. The extra handoff's exact service-area size, county coverage, catchment acreage, individual HUC assignments, station-to-drainage claims and pipeline capacity ranges are not established by the supplied research. Remove these numbers from presentation claims until supported by a specific authoritative artifact.

Do not reuse six-digit labels as HUC8 or treat an administrative region as a drainage basin. A point-in-polygon result alone is insufficient to prove contributing runoff; document outlets and upstream connectivity using [USGS WBD](https://www.usgs.gov/national-hydrography/watershed-boundary-dataset).

The airport stations are provisional regional precipitation proxies. Airport rainfall does not directly measure municipal demand, evaporative stress or reservoir inflow. Remove categorical statements that a station contributes “zero inflow” or that all alternative COOP stations have unacceptable coverage unless a catchment and station-specific analysis supports them. Remove the diagram's implied water-conveyance links through weather-station locations.

Snapshot checks from data/observations.csv:

| Station | Calendar records | Valid precipitation records | Missing date |
|---|---:|---:|---|
| Corpus Christi USW00012924 | 12,784 | 12,784 | None in this snapshot |
| Victoria USW00012912 | 12,784 | 12,783 | 1996-03-07 |
| San Antonio USW00012921 | 12,784 | 12,783 | 2023-06-21 |

These are local snapshot results, not proof of uninterrupted reporting in the station inventory. Preserve observation-day conventions and source/quality flags. NOAA `T` means trace; `P` means missing presumed zero. PRCP in the raw daily format is tenths of millimetres; the repository field is precip_mm. Missing and excluded data must not become observed dry days. [NOAA documentation](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt).

Gridded precipitation is a candidate comparison, not a mandated post-freeze migration. Evaluate resolution, coverage, source dependence, uncertainty, catchment aggregation and reuse terms before choosing PRISM or [NOAA nClimGrid-Daily](https://www.ncei.noaa.gov/products/land-based-station/nclimgrid-daily). Gridding does not eliminate all bias.

Correct station identity before choosing a series:

- **08210000: Nueces River near Three Rivers, TX**, not near Mathis. [USGS identity record](https://pubs.usgs.gov/dds/wqn96cd/html/wqn/wq/region12/08210000.htm).
- **08206900: Choke Canyon Reservoir near Three Rivers**, not Frio River near Tilden. [TWDB reservoir page identifying its USGS source](https://waterdatafortexas.org/reservoirs/individual/choke-canyon).
- Neither identity check establishes an appropriate upstream discharge benchmark. Parameter 00060 must not be assumed available or suitable for both sites; inspect the actual series metadata and regulation before making that claim.

## 3. Scientific definitions to use

| Term | Correct interpretation |
|---|---|
| Rainfall deficit | A precipitation-depth shortfall relative to a specified reference, season and interval. State the exact implemented formula; generic deficit definitions are not interchangeable. Multiplying depth by area gives a precipitation volume, not available supply or runoff. |
| Meteorological drought | Precipitation deficiency over a defined climatic interval. SPI/SPEI and USDM are different products; USDM also uses hydrologic, impact and expert evidence. |
| Streamflow deficit | Discharge shortfall relative to a stated reference and interval. Specify rate versus integrated volume. Delete the unsupported “40% rain deficit causes 90%+ flow collapse” claim. |
| Storage percentage | Sum of matched storage volumes divided by sum of the corresponding capacities, times 100. State reservoir membership, storage definition, dates and capacity version. Explain mismatched vintages instead of silently combining them. |
| Firm/safe yield | Model- and policy-dependent supply measures under specified drought and operating assumptions. Do not generalize one terminal-storage definition or claim safe yield must always be strictly lower. Confirm the proposed 75,000 acre-foot reserve in applicable approvals. |
| Planning demand | A planning projection under a defined methodology and horizon, not observed daily pumpage. Do not assert an unverified universal “consumptive” definition. |
| Restriction status | An official administrative declaration with jurisdiction and effective date. A calculated percentage crossing is not itself that declaration. |

USDM example indicator percentile bands are **D0 20.01–30, D1 10.01–20, D2 5.01–10, D3 2.01–5, D4 0–2**. D0 is abnormally dry. These bands are not a single-variable algorithm for computing an official drought category or a municipal restriction. County area percentages in a drought category are also not indicator percentiles. [Official classification](https://droughtmonitor.unl.edu/About/AbouttheData/DroughtClassification.aspx).

## 4. Policy and modeling corrections

The supplied policy's ordinance refers to **Chapter 55, Article XII**, not Article VII. The PDF is a supplied snapshot, not proof of today's active stage. Page 60 visibly records Ordinance 033940 approved June 2, 2026 and an effective-date stamp June 8, 2026. [Supplied plan](sources/wat-drought-contingency-plan.pdf).

Use the complete [reviewed policy table](review_findings.md#supplied-city-policy-snapshot):

- Watch begins below 50%; termination above 50% for 15 consecutive calendar days.
- Stage 1 begins below 40%; termination above 50%.
- Stage 2 begins below 30%; termination above 40%, returning to Stage 1.
- Stage 3 begins below 20%; termination above 30%, returning to Stage 2.
- Level 1 emergency is a City determination of supply failing to meet demand within 180 days, with discretion involving alternative supplies. It is not a fixed 15% threshold.
- Level 2 emergency concerns an actual supply emergency and imminent pressure failure under specified conditions; it must not be omitted from a purported complete policy summary.

These points summarize PDF pages 9–11. Preserve managerial discretion and initiation/termination differences. Remove the extra handoff's unsupported “active Stage 1 as of September 6” and its causal story that a particular pipeline expansion caused a historical renaming. The current dashboard is a place to verify status, not a permanent dated record embedded in this document.

Restrictions have customer-class exceptions, variances and approval conditions. “Drip/hand watering only” is too broad to explain Stage 3: turf and other uses have different rules. Emergency demand-reduction targets are not proven savings or automatically universal mandatory reductions; surcharges are not automatically imposed in every situation. Consult the cited sections rather than an abbreviated enforcement table.

The supplied PDF contains an unresolved Appendix C monthly-release inconsistency and historical capacity tables. Those remain source questions, not values approved for simulation. The details and page references are recorded in review_findings.md.

The Region N adoption index and technical memorandum are distinct evidence. Existing-system CCWSM approvals do not establish that WAM is used only for new rights, that every strategy must use one model without exception, or that BASIN's recipient must use CCWSM. The previously inspected correspondence distinguishes existing-system and strategy analyses and allows separately approved variances. Verify the adopted chapters and applicable approval before model-specific claims. Do not claim the entire older memorandum is invalid or that the unseen adopted plan's chapters were audited. Exact naturalized-flow file coverage, end year and version remain unverified.

## 5. Corrected case studies

**Case A — aggregation illustration.** Using the imported packet's quoted inputs, 378,337 / 918,882 is 41.17%; 517,292 / 1,077,857 is 47.99%. The first groups two reservoirs and the second three. This is a reproducible arithmetic example, not proof of simultaneous independent observations or perfect publisher agreement. At rounded 41.2%, the difference from 40% is 1.2 percentage points. Both 41.2% and 48% are above 40%; the example does not itself demonstrate a Stage 1 crossing. It also does not prove why the app uses a 2024-labeled 48% scenario assumption. Do not substitute live storage into that assumption automatically.

**Case B — code versus supplied policy.** The code has a fixed 15% emergency category; the supplied plan describes a supply-demand horizon for Level 1. This is an established mismatch. The precise historical transition and reason for it are not established. A research review does not repair the code.

**Case C — hypothetical geography/variable mismatch.** Coastal rain and reservoir inflow can represent different places and quantities. No reproduced, aligned series here establishes the claimed near-normal coastal rainfall, below-fifth-percentile flow, or concurrent falling storage. Present this only as a proposed test case, or omit it from a factual demo until the observations are obtained.

## 6. Current code audit and implementation boundary

Inspected at repository commit 965d010. Links use file paths and function names rather than the pasted handoff's potentially stale line numbers.

| File / location | Established finding | Disposition |
|---|---|---|
| [analysis.py](../basin_core/analysis.py), simulate_reservoir_drawdown | Hardcoded 15% emergency category and threshold-only stage classification do not implement the supplied plan's full discretion, recovery rules or emergency criteria. | B08 implementation task; not repaired by this document. |
| Same function | Initial 0.48 and capacities 257,300 / 662,600 acre-feet are code assumptions. The UI labels the 48% choice with 2024. | Require provenance/versioning; remove the unsupported assertion that today's three-reservoir metric caused the default. |
| Same function | Negative net_loss is clipped into zero losses, so modeled surplus does not refill storage. | Confirmed code-path defect; keep B08 regression/fix task. Scientific calibration is a separate issue. |
| Same function | Linear rainfall-to-inflow, evaporation, demand and allocation constants are heuristic. | Do not promote results into validated yield or time-to-danger evidence. |
| [app.py](../app.py), architecture card and reservoir caption | Generalized WAM engineering/Run 3 claims exceed demonstrated compatibility and model applicability. | B08 wording/behavior reconciliation. |
| app.py, pipeline copy | One card says the pipeline supplies reservoirs while another description routes to O.N. Stevens WTP. | Internal inconsistency; verify authoritative routing and correct product copy during B08. |

Capacity differences alone do not prove “sedimentation drift.” Confirm measurement definitions, source vintages and revisions before explaining a discrepancy. A code constant differing from a portal value is not sufficient causal evidence.

## 7. Proposed evidence workflow and corrected acceptance criteria

These are proposed requirements for B03/B05/B08, not descriptions of existing functionality. Agree the schema with its owner before implementing.

1. Display evidence ID, publisher, direct URL, artifact/version, geographic scope, dates, units, qualifiers and inspection status. S01–S11 in the source shortlist correspond to imported E001–E011; use E identifiers for evidence references and do not mix naming silently.
2. Compare evidence with explicit numerator, denominator, assets, observation interval and definitions. Permit unresolved, not comparable and explained dispositions; preserve the original claims.
3. Keep rainfall revision approval separate from evidence review. A note-only edit need not alter rainfall values, but a change to evidence or interpretation used by the exported decision must invalidate or require renewed approval of the affected packet. Do not promise that scenario approval is always retained for every conflict edit.
4. Save/load must preserve permitted evidence links, dispositions and provenance. Define privacy treatment for free-text rationale as well as a field literally named notes; free text is not automatically safe to export because it is called a disposition.
5. Export must identify the exact rainfall revision and reviewed evidence snapshot, include source hashes only for bytes obtained, exclude private free text by default, and replay-check the agreed manifest. Proposed names such as daily_rainfall.csv, audit.json and hydrologist_brief.md are not verified existing export contracts.
6. Demonstrate one traceable historical case and one clearly hypothetical rainfall scenario. A teammate must reproduce the arithmetic and explain why this is not an official restriction prediction.

## 8. Usable source directory

These are actual links, not the lost hyperlink labels in the pasted transcript. Discovery links do not imply all linked content was read or that downloads will always remain available.

| ID | Direct source links | Status / intended use |
|---|---|---|
| S01 | [NOAA daily readme](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt) | Format and flag documentation reviewed. |
| S02 | [Station registry](https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt), [element inventory](https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt) | Metadata discovery; inventory does not prove daily completeness. |
| S03 | [2026 plan index](https://www.twdb.texas.gov/waterplanning/rwp/plans/2026/index.asp) | Follow Region N; actual adopted chapters remain to be reviewed. |
| S04 | [Region N](https://www.twdb.texas.gov/waterplanning/rwp/regions/n/index.asp) | Administrative planning context. |
| S05 | [Technical memorandum PDF](https://www.twdb.texas.gov/waterplanning/rwp/planningdocu/2026/projectdocs/Tech_Memos/RegionN_TechnicalMemorandum.pdf) | Earlier relevant approval passages inspected; not a substitute for the adopted plan. |
| S06 | [Area reservoir dashboard](https://waterdatafortexas.org/reservoirs/municipal/corpus-christi), [Choke Canyon](https://waterdatafortexas.org/reservoirs/individual/choke-canyon) | Storage context; obtain history through the publisher and record the actual returned URL/query. No unverified CSV endpoint is invented here. |
| S07 | [City dashboard](https://www.corpuschristitx.gov/department-directory/corpus-christi-water/water-supply-dashboard/), [supplied policy PDF](sources/wat-drought-contingency-plan.pdf) | Current-status discovery versus a hashed supplied policy snapshot. |
| S08 | [USGS APIs](https://api.waterdata.usgs.gov/), [08210000 identity](https://pubs.usgs.gov/dds/wqn96cd/html/wqn/wq/region12/08210000.htm) | Identity checked; discharge availability and suitability not approved. |
| S09 | [USGS WBD](https://www.usgs.gov/national-hydrography/watershed-boundary-dataset) | Official geometry starting point; no approved local HUC mapping yet. |
| S10 | [Extended naturalized flow and evaporation](https://www.twdb.texas.gov/surfacewater/data/ExtendedNatFlow/index.asp) | Discovery only for individual model-input versions and periods. |
| S11 | [USDM explanation](https://droughtmonitor.unl.edu/About/WhatistheUSDM.aspx), [classification](https://droughtmonitor.unl.edu/About/AbouttheData/DroughtClassification.aspx) | Context and methodology, not local operational authority. |

The source PDF hash is in [import_manifest.json](import_manifest.json). The extra handoff's “SHA-256 logged,” “all verified” and live download claims are not adopted as our audit record. See [source_review.json](source_review.json) for inspection limits. We did not verify a fresh remote copy against the supplied PDF hash.

## 9. Research closeout and next work

This replacement resolves the extra handoff's unsupported factual presentation. Remaining external verification is bounded: actual adopted Region N chapters/approvals, gauge/catchment suitability, current policy applicability, Appendix C release inconsistency and a reproduced historical comparison. These questions do not block building source metadata, comparison controls, privacy handling or the executable baseline.

Proceed with the four owner-specific work lists in [review_findings.md](review_findings.md#work-the-group-can-start-now). The next deliverable is one reproducible evidence packet; avoid another broad research collection round before that workflow works.
