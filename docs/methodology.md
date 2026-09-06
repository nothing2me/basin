# BASIN methodology v2

BASIN prepares rainfall stress scenarios and traceable evidence for professional review. The rainfall packet does not estimate water supply, reservoir levels, restriction dates, future probabilities, or the hydrologic drought of record. A separately labeled reservoir experiment is illustrative and excluded from the packet. Numerical checks are not expert validation.

## Data contract

The bundled NOAA NCEI GHCN-Daily snapshot covers 1991-01-01 through 2025-12-31. The manifest identifies actual stations, coordinates, download time, dataset version, original payload hashes, normalized CSV hash, completeness, and flags. Corpus Christi, Victoria and San Antonio airport observations are **provisional regional station proxies**. They are not validated catchment precipitation or an area-weighted basin product. No inferred catchment mapping is claimed. Station selection and aggregation require practitioner review before operational use.

Read PRCP only, divide tenths of millimeters by 10. Exclude negative/missing values, every nonblank quality flag and MFLAG P (missing presumed zero). Retain reported trace precipitation as zero at dataset resolution, preserving the flag. Do not use multi-day totals (MDPR), interpolate, or turn gaps into zeros. Reindex to a complete daily calendar. Require complete simultaneous windows at every selected station, with at least five matched windows ending by 2015. Monthly 1991–2020 climatology requires at least 600 valid daily observations per station/month. Valid daily measurements outside a complete window can contribute to climatology. Source days are observational days, which may have differing station observation times; not synchronized hourly measurements.

## Generator

Algorithm: synchronized-season-matched-whole-window-v1. NumPy PCG64 uses the recorded seed. Choose uniformly among eligible (onset month, duration) settings, then uniformly among complete historical windows starting on that month's first day, then a uniform retained-rainfall fraction in the configured interval. Use the same historical dates at all selected stations. Keep actual source dates as day labels, including leap days. No artificial block joins, independent station resampling, or extrapolated future dates.

Multiply daily precipitation by the retained fraction at all stations, one randomly chosen station, or a 50/50 mix of those two constructions. This is a deliberate stress test; scaling precipitation is not scaling hydrologic drought severity. An all-station perturbation does not guarantee concurrent stress; achieved concurrence is measured separately. Retention 100% is an unmodified historical resample. Fingerprint and skip duplicate rainfall arrays with the same onset month; stop at 20 times requested count attempts and report actual count and excluded settings. This intentionally replaces the design draft's unspecified multi-block bootstrap with an auditable whole-window method. It cannot invent new within-window sequencing; reduced diversity is a real limitation.

## Features and references

Expected rainfall is each station's monthly mean daily rainfall over 1991–2020, repeated on the scenario calendar. Station deficit = max(0, sum(expected minus scenario rainfall)); displayed deficit = arithmetic mean of station deficits, in mm per station. Stations receive equal weight; this is not a basin water volume. Wet periods offset dry periods within a window before clipping. Dry spell is the maximum consecutive run below 1 mm/day at any selected station.

Concurrence: sum expected-minus-rainfall in complete 30-day windows per station. A station is stressed when this exceeds its 75th percentile of complete rolling deficits in 1991–2020. Concurrence is the fraction of eligible windows where every selected station is stressed. Exclude the first 29 days from numerator and denominator. Strict exceedance is used; equality is not stress. With one station this measures that station's stress frequency, not multi-station concurrency.

Rainfall benchmark: the maximum equal-station mean deficit among complete historical windows with **the same onset month, selected stations and duration**, beginning in 1991 or later and ending on or before 2015-12-31. Expected rainfall is computed on each window's own calendar. Historical percentile = fraction of these matched deficits <= the candidate's deficit. This is a small empirical reference, not a return period or occurrence probability. The sample count is displayed. It is independent of candidate pool size. Exceedance is informational and never invalidates a scenario. It is not comparable to a hydrologic drought-of-record benchmark. This snapshot does not cover the model's entire 1934–2015 hydrology.

## Priorities and learning

Weighted score 0–100: normalize user weights by their sum; multiply by historical severity percentile, duration/365, achieved concurrence, and fraction of days in June–September. The summer profile is an illustrative user-selectable priority through its weight, not a verified local demand curve. No score rewards later month numbers. Fixed duration inputs make duration contribution constant; the interface encourages varied durations. Reject all-zero weights.

KMeans is the only learned component: random_state=22, n_init=10, single native computation thread. Features are the four normalized scoring features, maximum dry spell/365, and each station deficit / mean expected rainfall (clipped to 0–1). Domain scales are fixed; equal-station spatial dimensions grow with station count. Cluster count is capped by distinct feature vectors. Canonicalize group labels by sorted centroids. Silhouette is descriptive, not evidence of usefulness or scientific validity.

Select each group's highest-scoring candidate (ID breaks ties), order representatives by score, then fill remaining slots globally. If fewer slots than groups, highest-scoring representatives win. Rejected candidates are excluded on explicit rebuilding. Priority changes update scores immediately but leave the reviewed shortlist intact until the user rebuilds it. Manual swaps, selection reasons and explicit before/after weight changes are logged. Saved alternative-weight comparisons record their candidate revision/digest pool and both configurations without changing the active run. Show group coverage, average pairwise feature distance, and mean priority score against score-only and seeded random selection. No universal improvement claim: show the measured tradeoffs for this run. Human review is still needed to determine whether clusters reflect meaningful distinctions.

## Revisions, privacy, and replay

Edit or replace actual rainfall; require complete finite nonnegative values on the same scenario dates/stations. Recompute all features, clustering and scores. Increment revision and clear approval. Users must accept or reject every shortlisted item; at least one exact current revision must be accepted. Rejected items remain in the audit, not in rainfall exports. Export checks the latest approval's rainfall hash in addition to revision.

ZIP: daily rainfall (mm/day), summary CSV, full candidate audit, public evidence/conflict records, source snapshot/manifest, method, implementation source hashes, library versions and file checksums. Replay reconstructs every candidate and checks the transformation sequence, each revision digest, exact exported dates/station order/units, selected/accepted identities, current approval, features, score components and summaries. The readable brief must match audited content. Evidence links and privacy defaults are validated. Group labels, selection history, saved comparisons, performance values and source truth are outside semantic verification; they are recorded and hash-checked only. See verification_scope.md.

Schema 2.0 uses canonical rainfall CSV digests with the index label `date`. Schema 1.0 sessions validate legacy digests before in-memory migration; originals remain untouched until saved. Legacy bundles must be re-exported, not silently certified with the new verifier. Unsigned hashes do not prevent coordinated tampering.

Provider notes and all free-text review notes are local and excluded by default. One explicit export opt-in includes both. Input uploads stay in the local process. Session JSON and append-only review logs are in gitignored local/. The local process binds loopback and has telemetry disabled; no automatic fetching, cloud inference, or utility connections. Local storage is not encrypted. This is a single-operator tool, not an authenticated shared server.

## Footprint and limitations

Measure pipeline wall time, CPU time, process resident memory at completion (not peak), and process resident memory in MiB. Network counters are not instrumented; a separate test blocks Python sockets and a browser rehearsal blocks nonlocal requests. Energy range = elapsed seconds × illustrative whole-laptop 15–65 W / 3600. This is an assumption-based estimate, not a meter measurement, and excludes installation, development, idle time and embodied impacts. Water impact is not quantified because location-specific electricity and embodied water data are missing. Do not claim zero total water impact.

Source documentation: https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt
Dataset DOI: https://doi.org/10.7289/V5D21VHZ
Planning context (not a rainfall benchmark): https://www.twdb.texas.gov/waterplanning/rwp/planningdocu/2026/projectdocs/Tech_Memos/RegionN_TechnicalMemorandum.pdf


## Evidence contract and compatibility

A workspace owns a single evidence registry. Every scenario has a nonempty list of evidence IDs. Required text fields: id, title, publisher, source_locator, source_date, retrieved_at, geographic_scope, kind, units, description, review_status. Unknown dates and inapplicable units may be blank. Source locators must be HTTP(S) URLs or docs/*.md references. Kinds are observation, derived calculation, user assumption, and policy statement. Review states are unreviewed, provisional, or reviewed for this exercise; none means professional approval.

Initial records reuse the NOAA manifest and identify station suitability, rainfall method, matched reference and ranking assumptions. New records append to the registry; original evidence remains intact. Each conflict links two different IDs, describes the precise disagreement and comparability limits, and records unresolved/resolved status plus a human disposition. Resolution requires text. Disposition changes retain before/after snapshots in evidence_history. No rule automatically trusts the latest publication or assigns a trust score.

Public descriptions and dispositions are intentionally exportable. `private_note` and `provider_notes` fields are recursively removed from the audit and history unless the common export opt-in is selected. Public text is not a place to enter private details. Save/load validates references, required fields, statuses and supported versions. Session 1.0 migration adds provisional baseline evidence without inventing past expert review.

## Illustrative reservoir experiment (selected Path B)

The user selected this path on September 6. Capacities are illustrative fixed parameters of 257,300 and 662,600 ac-ft, with both starting at the selected fraction. Daily inflow is `30 + 45 * equal-station mean rainfall_mm`, allocated by capacity. Potential evaporation is 750 ac-ft/day in June–September and 380 otherwise. Requested demand is 370 ac-ft/day with assumed pipeline supply, 554 without it, reduced by the conservation fraction.

Each day adds inflow, serves evaporation from available water, allocates demand (65% initially from the first pool when above 20%, otherwise 15%, with available water covering shortfalls), then spills excess capacity. Outputs report end-of-day storage, actual evaporation, served demand, unmet evaporation/demand, inflow, spill and a balance residual. The conservation identity is end storage = beginning storage + inflow - actual evaporation - served demand - spill. No water is created or silently discarded.

These coefficients, allocation rules, initial conditions and 40/30/20/15% bands are assumptions, not calibrated system behavior or current official policy. The experiment excludes estuary releases, water rights, real transfers and observed inflow calibration. It is not a validated impact model. Settings/results are transient and explicitly outside the evidence packet; changing them does not change rainfall approval.

## Geographic and time-scale limitations

The three airport stations offer long, nearly complete public regional records and a reproducible demonstration. Their convenience and completeness do not establish catchment representativeness. Station concurrence labels describe stations, and with one station measure stress frequency. Presets are illustrative archetypes without named provider endorsement. The 30–365-day windows cannot answer multi-year reservoir drawdown or drought-recovery questions. That unmet use case requires appropriate data and expert model design, not simply raising a duration limit.

NOAA's documentation was checked on September 6: PRCP is in tenths of millimeters, -9999 denotes missing values, MFLAG P means missing presumed zero, T indicates trace, and blank QFLAG indicates no failed quality check. BASIN conservatively excludes any nonblank quality flag, retains trace as zero at reported resolution with the trace flag, and does not substitute multiday totals or fill gaps. [NOAA GHCN-Daily README](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt).

The Region N technical memorandum distinguishes the Corpus Christi Water Supply Model from Nueces WAM Run 3 uses. The former includes system operations and hydrology through 2015; the document identifies different applications and limitations of Run 3. BASIN therefore provides no generic WAM work order or direct precipitation-to-streamflow scaling instruction. [Region N memorandum, printed pages 7–11 and hydrologic variance attachment](https://www.twdb.texas.gov/waterplanning/rwp/planningdocu/2026/projectdocs/Tech_Memos/RegionN_TechnicalMemorandum.pdf).
