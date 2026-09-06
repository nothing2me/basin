# BASIN methodology v1

BASIN prepares rainfall stress scenarios for professional review. It does not estimate water supply, reservoir levels, restriction dates, future probabilities, or the hydrologic drought of record. Numerical checks are not expert validation.

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

Select each group's highest-scoring candidate (ID breaks ties), order representatives by score, then fill remaining slots globally. If fewer slots than groups, highest-scoring representatives win. Rejected candidates are excluded on explicit rebuilding. Priority changes update scores immediately but leave the reviewed shortlist intact until the user rebuilds it. Manual swaps and priority values are logged. Show group coverage, average pairwise feature distance, and mean priority score against score-only and seeded random selection. No universal improvement claim: show the measured tradeoffs for this run. Human review is still needed to determine whether clusters reflect meaningful distinctions.

## Revisions, privacy, and replay

Edit or replace actual rainfall; require complete finite nonnegative values on the same scenario dates/stations. Recompute all features, clustering and scores. Increment revision and clear approval. Users must accept or reject every shortlisted item; at least one exact current revision must be accepted. Rejected items remain in the audit, not in rainfall exports. Export checks the latest approval's rainfall hash in addition to revision.

ZIP: daily rainfall (mm/day), summary CSV, full candidate audit, source snapshot and manifest, method, software versions, and file checksums. Replayer verifies file hashes, approval revision, transformations from source windows through every edit, and all exported features. Run-level seed/settings allow regeneration with the pinned software; edited and custom revisions include their transformation history. The ZIP has integrity checks, not a digital signature or protection from deliberate coordinated tampering.

Provider notes and all free-text review notes are local and excluded by default. One explicit export opt-in includes both. Input uploads stay in the local process. Session JSON and append-only review logs are in gitignored local/. The local process binds loopback and has telemetry disabled; no automatic fetching, cloud inference, or utility connections. Local storage is not encrypted. This is a single-operator tool, not an authenticated shared server.

## Footprint and limitations

Measure pipeline wall time, CPU time, process resident memory at completion (not peak), and pipeline network calls. Energy range = elapsed seconds × illustrative whole-laptop 15–65 W / 3600. This is an assumption-based estimate, not a meter measurement, and excludes installation, development, idle time and embodied impacts. Water impact is not quantified because location-specific electricity and embodied water data are missing. Do not claim zero total water impact.

Source documentation: https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt
Dataset DOI: https://doi.org/10.7289/V5D21VHZ
Planning context (not a rainfall benchmark): https://www.twdb.texas.gov/waterplanning/rwp/planningdocu/2026/projectdocs/Tech_Memos/RegionN_TechnicalMemorandum.pdf
