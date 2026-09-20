# Watershed-representativeness review checklist

**Purpose:** one-page checklist for a domain reviewer (hydrologist / water planner) to
evaluate whether the bundled NOAA gauge network adequately represents the Nueces /
Frio / Atascosa drainage basins for BASIN's screening purpose. Sign-off below does
**not** certify BASIN as a calibrated watershed model — it reviews whether the gauge
selection and fill policy are defensible for rainfall-stress scenario screening.

Prepared: 2026-09-19 | Snapshot SHA-256: `f2d07169…` | Full provenance: `data/manifest.json`

## 1. The gauge network by sub-basin

| Sub-basin / reach | Gauges | Raw completeness (1991–2025) |
|---|---|---|
| Nueces headwaters (Hill Country) | Leakey, Camp Wood | 60.6% / 50.8% |
| Hondo Creek (Nueces tributary) | Hondo | 66.5% |
| Upper Nueces (Winter Garden) | Crystal City, Carrizo Springs | 51.1% / 85.7% |
| Frio River | Pearsall | 56.2% |
| Frio at Choke Canyon Reservoir | **Choke Canyon Dam** | **99.6%** |
| Atascosa River | Pleasanton | 77.9% |
| Frio/Nueces confluence | Three Rivers 9 NE | 59.3% |
| Lower Nueces at Lake Corpus Christi | Mathis 4 SSW | 58.2% |

All 10 gauges reach **100% analysis coverage** via declared fill chains that stay
inside the watershed (headwater gauges fill downstream; never coastal proxies).

## 2. Questions for the reviewer

1. **Coverage adequacy per sub-basin.** Is one gauge per reach (two for headwaters /
   upper Nueces) sufficient to represent sub-basin rainfall variability for scenario
   screening? Which sub-basins would benefit most from additional gauges?
2. **Fill-chain defensibility.** Missing days fill from declared watershed chains
   (e.g., Pearsall → Choke Canyon Dam → Mathis → Hondo → Carrizo Springs). Are the
   orderings hydrologically defensible? Is the upstream-fill fallback (used for the
   October 2003 lower-basin gap) acceptable, or should those days be flagged
   differently?
3. **Equal-weight averaging.** Scenarios average station deficits with equal weights
   (no area weighting). For a screening layer this is disclosed as provisional. Is
   equal weighting acceptable at this stage, and what weighting would you recommend
   before operational use?
4. **Watershed vs. regional footprints.** The builder offers Regional (coastal
   airports), Watershed (these 10), and combined presets. Is the Watershed preset
   the appropriate default for reservoir-relevant screening?
5. **Gap handling.** Excluded days (nonblank QFLAG / MFLAG P / negative) are dropped
   and filled; traces are treated as zero. Acceptable for screening?
6. **Missing headwater reach.** No gauge exists for the upper Frio above Pearsall
   (Dilley/Pearsall northward). Is that a material gap for Choke Canyon inflow
   screening?

## 3. Review disposition

| Reviewer | Affiliation / role | Date | Disposition |
|---|---|---|---|
| *(name)* | *(organization)* | *(date)* | Approved as screening-representative / Approved with comments / Not approved |

Comments:

---

*This checklist is advisory input, not engineering certification. BASIN remains an
exploratory screening layer; calibrated catchment rainfall and runoff remain
post-presentation work.*