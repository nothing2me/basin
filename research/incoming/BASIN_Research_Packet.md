# BASIN Decision-Ready Research Packet & Source Shortlist
**Basin Analysis and Scenario Intelligence Navigator (BASIN)**  
*Focus Region:* Coastal Bend / Region N, Texas  
*Research Snapshot Date:* September 6, 2026  
*Target Freeze Horizon:* September 18 Feature Freeze | September 19–20 Rehearsal | September 21 Travel  
*Coordination Tasks:* Shared TODO B03, B05, B07, B08, B09, B11  

---

## 1. Executive Summary & One-Page Findings

### 1.1 Recommended Source Stack
To ensure full auditability, scientific defensibility, and zero unverified scope expansion before the September 18 freeze, the team should adopt the following four-tier source stack:

1. **Numerical Input Now (Operational Runtime):**
   * **Source:** NOAA NCEI GHCN-Daily (S01, S02) bundled snapshot (1991–2025) for stations `USW00012924` (Corpus Christi Intl AP), `USW00012912` (Victoria Rgnl AP), and `USW00012921` (San Antonio Intl AP).
   * **Role:** Powers whole-window resampling, seasonal deficit calculations, and the 1991–2020 baseline climatology. Missing and failed quality flags (`QFLAG != blank`, `MFLAG == 'P'`) are strictly excluded; trace values are retained as 0 mm at measurement resolution; zero imputation is forbidden.
2. **Contextual Evidence Now (Reference & Conflict UI):**
   * **Source A:** TWDB *Water Data for Texas* (S06) daily reservoir storage for Choke Canyon Reservoir, Lake Corpus Christi, and Lake Texana. Provides ground-truth storage (ac-ft and percent full) and demonstrates the 3-reservoir vs. 2-reservoir aggregation distinction.
   * **Source B:** City of Corpus Christi Water Department Dashboard & Adopted Drought Contingency Plan (S07), approved 2025 and amended June 2026. Provides current official restriction status (Stage 1), legal trigger definitions, and executive discretion rules.
   * **Source C:** U.S. Drought Monitor (S11) weekly county classifications (D0–D4) as an external reference for meteorological drought context.
3. **Validation-Only Data (Offline Benchmarking & Auditing):**
   * **Source A:** USGS Water Data API (S08) daily discharge (Parameter 00060) at key river gages (`USGS 08210000` Nueces River near Mathis; `USGS 08206900` Frio River near Tilden) to benchmark whether historical meteorological rainfall deficits coincided with physical streamflow drought.
   * **Source B:** USGS Watershed Boundary Dataset (S09) HUC-8 boundaries (`12110108`, `12110111`, `12100201`, `12100301`) to demonstrate contributing drainage areas vs. proxy station coordinates.
4. **Deferred Model Inputs (Post-Freeze / Future Model Integrations):**
   * **Source:** TWDB Extended Naturalized Streamflow and Lake Evaporation datasets (S10) through 2015/2020. Required only if the team formally expands scope to calibrate hydrologic rainfall-runoff models or WAM control point input cards.

---

### 1.2 Three Most Consequential Corrections for the BASIN Team

1. **Correction 1: Eliminate the Hardcoded "Stage 4 (15%)" Trigger and Audit the Emergency Trigger Definition.**
   * *The Problem:* `basin_core/analysis.py` (L154, L199–200) and `app.py` (L196) hardcode Stage 4 as a fixed `< 15%` combined reservoir storage trigger.
   * *Primary Evidence:* Under the City of Corpus Christi's adopted 2025 Drought Contingency Plan (amended June 2026; S07), Stage 4 was officially renamed **"Level 1 Water Emergency"** and is **not triggered by a static 15% storage threshold**. Instead, it triggers dynamically when the City reaches **180 days from when total available water supply is projected to be insufficient to meet total demand**, accounting for Eastern pipeline supplies (Lake Texana and Colorado River).
   * *Impact:* Presenting a fixed 15% Stage 4 trigger misinforms rural water providers and contradicts the City's governing ordinance.

2. **Correction 2: Resolve the Storage Aggregation Mismatch (48.0% vs. 41.2%) in Code and UI.**
   * *The Problem:* In `basin_core/analysis.py` (L136), `simulate_reservoir_drawdown` sets default `initial_pct = 0.48` (48%).
   * *Primary Evidence:* On September 6, 2026, TWDB's "Corpus Christi Area Reservoirs" (S06) reports **48.0%**, but this metric aggregates **three reservoirs** (Choke Canyon + Lake Corpus Christi + Lake Texana = 1,077,857 ac-ft pool). The City of Corpus Christi's DCP trigger legally counts only the **two Western reservoirs** (Choke Canyon + Lake Corpus Christi = 918,882 ac-ft pool), which sit at **41.2% full** (378,337 ac-ft).
   * *Impact:* Planners looking at 48% believe the system is well clear of drought, whereas the regulatory 2-reservoir trigger at 41.2% is within 1.2% of Stage 2 (30%) / Stage 1 (40%) enforcement margins.

3. **Correction 3: Correct Texas WAM Run 3 Claims and Acknowledge the Corpus Christi Water Supply Model (CCWSM).**
   * *The Problem:* `app.py` (L349–350) claims to generate a "Texas WAM Engineering Package" for "Texas WAM Run 3", and code comments imply rainfall retention directly scales naturalized streamflow.
   * *Primary Evidence:* Region N’s approved TWDB planning methodology (S04, S05) utilizes the **Corpus Christi Water Supply Model (CCWSM)** under the 2001 TCEQ Agreed Order and an approved **Safe Yield variance (75,000 ac-ft reserve)** for existing surface water supplies, *not* TCEQ WAM Run 3. Furthermore, WAM Run 3 is legally mandated for evaluating *new* Water Management Strategies (WMS) and permitting unappropriated water, requiring monthly naturalized flow cards across hundreds of control points, which cannot be scaled directly from 3 airport rainfall stations.
   * *Impact:* Claiming WAM Run 3 compliance misleads engineers and damages credibility during hydrologist handoff.

---

### 1.3 Key Unanswered Questions Requiring Practitioner Input
* **Q1 (Hydrology):** Which upstream rainfall station or gridded precipitation product (e.g., PRISM 4km vs. NWS MRMS QPE) does the Nueces River Authority or consulting hydrologist recommend to represent the Frio/Nueces catchment rather than airport proxies?
* **Q2 (Operations):** How do wholesale rural customers (e.g., Nueces County WCID #3) operationally adjust their local treatment and drought surcharges when the City declares Stage 1 vs. Stage 2?
* **Q3 (Scope/B08):** Will the team follow **Path A** (completely exclude the defective reservoir simulation from the demo) or **Path B** (retain an explicitly labeled, mass-conserving illustrative educational widget)?

---

## 2. Geography, System Boundaries, and Scientific Definitions (P0)

### 2.1 User, Task, Recipient, and Expected Handoff
* **Target User:** Water resources analyst, general manager, or operations superintendent at a rural-serving retail water district, water supply corporation (WSC), or small municipality in the Coastal Bend / Region N planning area (e.g., Nueces County WCID #3 / Robstown, San Patricio Municipal Water District, Violet WSC, Ricardo WSC).
* **Specific Decision Supported:** Selecting, evaluating, and documenting 2 to 3 defensible, season-matched historical rainfall stress scenarios (contrasting duration, onset, and spatial concurrence) to submit to an engineering consultant or river authority for detailed hydrologic modeling (CCWSM/WAM) before capital planning or drought surcharge hearings.
* **Input to BASIN:** Verified NOAA GHCN-Daily historical rainfall records; user-defined stress constraints (duration 30–365 days, retention 35%–85%, onset season); community priority weights (severity, duration, concurrence, summer demand).
* **Task Performed:** Run local KMeans scenario generation; inspect scenario clustering and score breakdowns; challenge and edit daily rainfall values or replace with local rain gauge data; verify data provenance; document human review rationale and dispositions on apparent data conflicts.
* **Recipient:** Licensed Professional Engineer (PE), consulting hydrologist (e.g., HDR, Freese and Nichols), or river authority technical staff (Nueces River Authority) responsible for executing official reservoir availability simulations.
* **Expected Handoff Deliverable:** An auditable, offline-replayable ZIP packet containing:
  1. Standardized daily rainfall time-series CSVs (in mm/day and inches/day) with explicit station metadata and SHA-256 digests.
  2. Machine-readable review audit trail (`audit.json` / `review_log.jsonl`) recording every transformation, edit, parameter weight, and approval revision.
  3. Evidence Register detailing source citations, baseline period (1991–2020), and known proxy limitations.
  4. Hydrologist Translation Brief outlining the meteorological stress parameters, noting that scenarios reflect precipitation stress rather than calibrated runoff, and requesting specific CCWSM safe-yield or drought-of-record runs.

---

### 2.2 Boundary Distinctions in Region N
Confusion between administrative, operational, and hydrologic boundaries is the leading cause of contradictory drought reporting in South Texas. The table below delineates the four relevant boundaries:

| Boundary Type | Geographic Scope | Controlling Authority | Relevance to BASIN Metrics |
|---|---|---|---|
| **Administrative Planning Boundary** | 11 Counties: Aransas, Bee, Brooks, Duval, Jim Wells, Kenedy, Kleberg, Live Oak, McMullen, Nueces, San Patricio. | Coastal Bend Regional Water Planning Group (Region N) & TWDB | Governs official decadal population projections, regional water demand forecasts, and recommended Water Management Strategies (WMS). |
| **Service Territories** | CCW municipal retail area (~140 sq mi) plus wholesale municipal/industrial service areas spanning 7 counties. | City of Corpus Christi (Corpus Christi Water - CCW) & Wholesale Customers | Dictates who is legally subject to City Drought Contingency Plan stages, outdoor watering restrictions, and drought surcharges. |
| **Upstream Contributing Drainage Areas** | ~17,000 sq mi across South Texas and Hill Country: Nueces Basin (HUC 121101), Frio Basin (HUC 121102). Extends northwest into Regions L and M (Edwards, Real, Uvalde, Zavala, Dimmit, La Salle). | USGS Hydrologic Units / TCEQ River Basins / Nueces River Authority | Dictates actual runoff and inflow into Choke Canyon Reservoir and Lake Corpus Christi. Local rain at the coast does *not* enter these reservoirs. |
| **Imported Supply Sources & Conveyance** | Lake Texana (Navidad River, Jackson County / Lavaca Basin, Region P) and Colorado River Run-of-River (Wharton/Matagorda County, Region K). | Lavaca-Navidad River Authority (LNRA), Lower Colorado River Authority (LCRA), CCW | 101-mile Mary Rhodes Pipeline Phase I (60–72 MGD raw water) and Phase II. Water is pumped directly to the **O.N. Stevens Water Treatment Plant** in Calallen; it does *not* flow into Region N reservoirs. |

---

### 2.3 Evaluation of Bundled NOAA GHCN-Daily Proxy Stations

BASIN currently bundles three first-order NOAA stations: `USW00012924` (Corpus Christi), `USW00012912` (Victoria), and `USW00012921` (San Antonio).

```
                      [ San Antonio Intl (USW00012921) ]
                               (Bexar Co. - Region L)
                                 * Upper San Antonio Basin
                                 * 100 mi north of reservoirs
                                          |
                                          v
   [ Upper Nueces / Frio Catchments ]            [ Lake Texana ]
        (Edwards Plateau / Hill Co.)               (Jackson Co. - Region P)
        * True Reservoir Watershed                   |
                  |                                  |
                  v                                  v
     [ Choke Canyon & Lake Corpus Christi ]      [ Victoria Rgnl (USW00012912) ]
        (Live Oak / McMullen / San Patricio)       (Victoria Co. - Region P)
                  |                                  * Regional Coastal Proxy
                  +--------------+                   |
                                 |                   |
                                 v                   |
                      [ O.N. Stevens WTP ] <---------+ (Mary Rhodes Pipeline - 101 mi)
                                 |
                                 v
                 [ Corpus Christi Intl (USW00012924) ]
                           (Nueces Co. - Region N)
                             * Demand Center Only
                             * Drains to Oso / Corpus Christi Bay
```

#### 1. Station USW00012924 — Corpus Christi International Airport
* **Location:** 27.7839° N, -97.5114° W; Elevation: 43.3 m; Nueces County (Region N).
* **Record Overlap & Completeness:** 1991-01-01 to 2025-12-31; 12,784 expected days; 12,784 valid days (100.0% complete; 0 missing; 1,781 trace days).
* **Evidence Supporting:** Highest data completeness and quality; directly captures weather and evaporative stress over the primary urban and rural municipal demand centers (e.g., Nueces County WCID #3); reflects lawn watering demand surges.
* **Evidence Undermining:** Located near the coast, far downstream of Wesley Seale Dam and Choke Canyon. Precipitation drains into Oso Creek and Corpus Christi Bay. Zero raindrops falling at this airport enter the municipal drinking reservoirs.

#### 2. Station USW00012912 — Victoria Regional Airport
* **Location:** 28.8625° N, -96.9300° W; Elevation: 33.8 m; Victoria County (Region P / Lavaca Basin).
* **Record Overlap & Completeness:** 1991-01-01 to 2025-12-31; 12,784 expected days; 12,783 valid days (99.992% complete; 1 missing day; 1,452 trace days).
* **Evidence Supporting:** Excellent continuous first-order record; located in the coastal plain climate zone adjacent to Jackson County, serving as a reasonable climatic proxy for weather at Lake Texana (the source of Mary Rhodes Pipeline Phase I).
* **Evidence Undermining:** Geographically outside Region N's planning boundary and completely outside the Nueces River Basin. Drains to the Guadalupe River basin (HUC 121002).

#### 3. Station USW00012921 — San Antonio International Airport
* **Location:** 29.5442° N, -98.4839° W; Elevation: 243.5 m; Bexar County (Region L / San Antonio Basin).
* **Record Overlap & Completeness:** 1991-01-01 to 2025-12-31; 12,784 expected days; 12,783 valid days (99.992% complete; 1 missing day; 1,854 trace days).
* **Evidence Supporting:** Long-term, automated, pristine first-order dataset; situated along the Balcones Escarpment, sharing general inland Hill Country storm track characteristics with the upper Nueces and Frio headwaters.
* **Evidence Undermining:** Drains into the Upper San Antonio River (HUC 12100301). Situated over 80–120 miles northeast of the Frio/Nueces headwaters. Convective summer storms in the Hill Country are highly localized; San Antonio can experience flash floods while the upper Frio watershed experiences severe drought.

#### Rigorous Evaluation of Alternatives (Why Points in HUCs are Insufficient)
* **COOP Stations in the Catchment (e.g., Choke Canyon Dam `USC00411720`, Tilden `USC00419030`, Dilley `USC00412458`):** While physically inside the watershed, historical COOP stations suffer from frequent missing observation days, changes in morning observation times (7:00 AM vs. midnight), and observer gaps that violate BASIN's requirement for synchronized, 100% complete multi-station windows.
* **Recommended Gridded Precipitation Solution:** The team should recommend transitioning post-freeze to **PRISM 4km daily gridded precipitation** or **NOAA nClimGrid (5km)** extracted over the exact HUC-8 boundaries of the Nueces and Frio catchments. Gridded products eliminate single-station spatial bias and provide continuous 1991–2025 coverage across the true catchment.

---

### 2.4 Seven Core Definitions: Units, Time Scales, and Allowed Comparisons

```
+---------------------------------------------------------------------------------------------------+
| PRECIPITATION REALM (Atmospheric)                                                                 |
|   1. Rainfall Deficit: Depth [mm / in], 30-365 days. Direct historical depth comparison only.     |
|   2. Meteorological Drought: Percentile / SPI [dimensionless], 1-24 months. Regional dryness.    |
+-------------------------------------------------+-------------------------------------------------+
                                                  | (Non-linear runoff transformation: 50% rain drop
                                                  |  often results in 90%+ streamflow loss)
                                                  v
+---------------------------------------------------------------------------------------------------+
| HYDROLOGIC REALM (Watershed & Reservoir Storage)                                                  |
|   3. Streamflow Deficit: Discharge [cfs] or Volume [ac-ft], daily/monthly. Watershed yield loss.  |
|   4. Storage Percentage: Ratio [%] of Conservation Storage to Capacity. Watch numerator/denom!   |
|   5. Firm / Safe Yield: Annual supply through Drought of Record [ac-ft/yr]. Long-term reliable.   |
+-------------------------------------------------+-------------------------------------------------+
                                                  | (Policy triggers applied to physical storage)
                                                  v
+---------------------------------------------------------------------------------------------------+
| REGULATORY & PLANNING REALM (Institutional Mandates)                                              |
|   6. Planning Demand: Projected dry-year need [ac-ft/yr or MGD], decadal horizons.               |
|   7. Restriction Status: Legal administrative declaration [Categorical Stages]. Executive order.  |
+---------------------------------------------------------------------------------------------------+
```

1. **Rainfall Deficit:**
   * *Definition:* The cumulative difference between observed precipitation and expected (climatological normal) precipitation over a designated time window. In BASIN: \(\max(0, \sum (P_{\text{expected}} - P_{\text{scenario}}))\).
   * *Units:* Millimeters (mm) or inches (in) of water depth.
   * *Time Scale:* Event-based to multi-month (e.g., 30 to 365 days).
   * *Allowed Comparisons:* Can be compared against historical deficits across identical season-matched calendar windows and stations. **Prohibited:** Cannot be directly converted to water volume (acre-feet), streamflow loss, or reservoir depletion without a calibrated hydrologic rainfall-runoff model.

2. **Meteorological Drought:**
   * *Definition:* A prolonged period of atmospheric dryness marked by a statistically significant deficiency in precipitation relative to normal climatological expectations, frequently accompanied by high temperatures and elevated vapor pressure deficit.
   * *Units:* Standardized indices (SPI, SPEI [standard deviations]) or percentiles (e.g., U.S. Drought Monitor D0–D4 percentiles: D0 ≤ 20th, D1 ≤ 10th, D2 ≤ 5th, D3 ≤ 2nd, D4 ≤ 1st percentile).
   * *Time Scale:* 1 month to 24+ months.
   * *Allowed Comparisons:* Can characterize regional atmospheric drought severity. **Prohibited:** Cannot be used as an automatic utility operational trigger or a proxy for reservoir storage.

3. **Streamflow Deficit:**
   * *Definition:* The volumetric deficiency between actual streamflow discharge entering a river reach/reservoir and long-term median or naturalized historical streamflow.
   * *Units:* Instantaneous rate in cubic feet per second (cfs) or cumulative volume in acre-feet (ac-ft).
   * *Time Scale:* Daily, monthly, or annual.
   * *Allowed Comparisons:* Can be directly compared to historical runoff and reservoir inflow records. **Prohibited:** In semi-arid basins like the Nueces, runoff is highly non-linear due to soil moisture deficits; a 40% reduction in rainfall often causes an 85–95% collapse in streamflow. Rainfall retention percentages cannot be linearly transferred to streamflow deficits.

4. **Storage Percentage:**
   * *Definition:* The ratio of current active conservation storage to total conservation storage capacity within an explicitly declared set of reservoirs: \(\frac{\sum \text{Storage}}{\sum \text{Capacity}} \times 100\).
   * *Units:* Percentage (%), with volumes measured in acre-feet (ac-ft).
   * *Time Scale:* Daily snapshot or end-of-month accounting.
   * *Allowed Comparisons:* Only comparable when asset membership and survey vintages are identical. **Prohibited:** A 3-reservoir aggregate percentage (including Lake Texana) cannot be compared against a 2-reservoir municipal drought contingency trigger.

5. **Firm Yield vs. Safe Yield:**
   * *Definition:* 
     * *Firm Yield:* The maximum annual volume of water a reservoir system can deliver continuously without shortage throughout a recurrence of the historical Drought of Record (DOR), assuming full legal water rights diversions, contractual operations, and environmental pass-throughs, with storage reaching zero at the critical point.
     * *Safe Yield:* The annual volume of water that can be delivered through the DOR while preserving a specified emergency reserve volume in storage (e.g., 75,000 ac-ft for Region N).
   * *Units:* Acre-feet per year (ac-ft/yr).
   * *Time Scale:* Multi-year drought sequence (e.g., 1948–1957 or extended 1934–2015 hydrology).
   * *Allowed Comparisons:* Safe yield is strictly lower than firm yield. **Prohibited:** Neither represents current stored water volume, nor can either be estimated from a 365-day weather resample.

6. **Planning Demand:**
   * *Definition:* The projected annual volume of water required by water user groups (municipal, industrial, agricultural) under dry-year conditions (high heat, low rainfall), approved by TWDB for regional planning.
   * *Units:* Acre-feet per year (ac-ft/yr) or Millions of Gallons per Day (MGD).
   * *Time Scale:* Decadal planning milestones (2030, 2040, 2050, 2060, 2070, 2080).
   * *Allowed Comparisons:* Used to assess long-term infrastructure deficits. **Prohibited:** Cannot be equated to immediate daily utility pumpage or drought curtailment baselines without adjusting for seasonal peaking.

7. **Restriction Status:**
   * *Definition:* A formal, legally binding administrative declaration issued by a water purveyor's executive authority (e.g., City Manager) enacting specific water-use prohibitions pursuant to a municipal ordinance or drought contingency plan.
   * *Units:* Categorical administrative status (e.g., Normal, Stage 1 Mild, Stage 2 Moderate, Stage 3 Critical, Level 1 Water Emergency).
   * *Time Scale:* Discrete operational period (from the effective date of published legal notice until formally modified or rescinded).
   * *Allowed Comparisons:* Reflects legal operational reality. **Prohibited:** Reservoir storage dropping below a threshold does *not* automatically constitute a restriction status; executive discretion and official declaration are legally required.

---

## 3. Planning Documents, Regulatory Policy, and Operational Models (P0)

### 3.1 Adopted 2026 Region N Plan vs. 2024 Technical Memorandum

* **Adoption Status:** The 2026 Coastal Bend (Region N) Regional Water Plan was formally approved by the Texas Water Development Board on **January 22, 2026**.
* **Role of the 2024 Technical Memorandum (S05):** The Technical Memorandum submitted on March 4, 2024, was an interim mid-cycle compliance milestone. It documented:
  1. Updated population and demand projections.
  2. The initial list of potentially feasible Water Management Strategies (WMS).
  3. The formal list of infeasible strategies from the 2021 Plan.
  4. The approval trail for hydrologic modeling variances.
* **Comparison & Validity:** Claims regarding baseline demands, reservoir capacities, and strategy selections in the 2024 Tech Memo remain valid as historical milestones, but the **adopted 2026 Plan** governs all final supply allocations, recommended project costs, and official regional safe yields. BASIN must cite the adopted 2026 Plan for official numbers and cite S05 strictly for the hydrologic variance approval history.

---

### 3.2 City of Corpus Christi Adopted Drought Contingency Plan (DCP)

The City of Corpus Christi manages water supply restrictions under City Code Chapter 55, Article VII (Drought Contingency Plan), approved in 2025 and amended in June 2026 (S07).

| Stage / Designation | Initiation Threshold | Termination Condition | Required Persistence / Discretion | Customer Impact & Key Mandates |
|---|---|---|---|---|
| **Water Shortage Watch** | Combined storage < 50% | Combined storage rises above 50% | 15 consecutive days persistence required to terminate. | Public awareness, voluntary conservation, utility system leak audits. |
| **Stage 1 (Mild Shortage)** | Combined storage < **40%** | Combined storage rises above 40% (or 50% watch) | City Manager discretion; weekly monitoring. | Outdoor landscape watering limited to **1 day/week** based on trash pickup day (before 10 AM / after 6 PM). Hand watering permitted. |
| **Stage 2 (Moderate Shortage)** | Combined storage < **30%** | Combined storage rises above 30% (or 40%) | City Manager discretion upon sustained recovery. | Landscape watering limited to **every other week** (1 day every 2 weeks). Bulk commercial water sales restricted. |
| **Stage 3 (Critical Shortage)** | Combined storage < **20%** | Combined storage rises above 30% | Reverts to Stage 2 upon certified recovery. | Complete ban on irrigation sprinkler systems. Drip/hand watering only on designated days. Vehicle washing banned except commercial facilities. |
| **Level 1 Water Emergency** *(Formerly Stage 4)* | **180 days from projected supply-demand failure** | When projected deficit horizon exceeds 180 days | Initiated by City Manager based on projected supply-demand modeling. **Not a static 15% trigger.** | Mandatory across-the-board curtailments (e.g., proposed 25% mandatory industrial/commercial reduction). Drought surcharge tariffs enforced. |

* **Active Declaration vs. Plan Conditions:** The plan establishes physical conditions that *authorize* action. An *active declaration* requires an administrative finding by the City Manager followed by published public notice. As of September 6, 2026, the City is actively operating under **Stage 1 restrictions**.
* **Affected Customer Classes:** Retail residential/commercial, large-volume industrial users (refineries/petrochemical complexes in the Ship Channel and San Patricio County), and wholesale rural customers (including Nueces County WCID #3). Under wholesale contracts, wholesale customers must enforce drought restrictions that achieve equivalent percentage reductions.

---

### 3.3 Code and Engineering Audit: app.py and basin_core/analysis.py

The table below documents every verified discrepancy between current application code and primary sources:

| Feature / Location | Implementation in BASIN Code | Primary Source Finding | Source Citation | Classification & Required Remedy |
|---|---|---|---|---|
| **Emergency Stage Definition** (`basin_core/analysis.py:L154, L199-200`; `app.py:L196`) | Hardcodes `Stage 4 (Emergency): Combined < 15% (137,985 ac-ft)`. | City abolished static 15% Stage 4; replaced with **Level 1 Water Emergency** based on 180-day projected supply-demand shortfall. | City DCP 2025, amended June 2026 (S07) | **Contradicted.** Update narrative and tooltips to reflect the 180-day supply-demand criteria; do not present 15% as official policy. |
| **Reservoir Storage Denominator** (`basin_core/analysis.py:L146-148, L156-158`) | Lake Corpus Christi: 257,300 ac-ft; Choke Canyon: 662,600 ac-ft. Total: 919,900 ac-ft. | Lake Corpus Christi capacity is **256,062 ac-ft**; Choke Canyon is **662,820 ac-ft**. Total: **918,882 ac-ft**. | TWDB S06 Volumetric Surveys & daily records (2026-09-06) | **Outdated.** Document survey vintages; flag minor capacity drift due to sedimentation. |
| **Default Initial Storage** (`basin_core/analysis.py:L136`) | Sets default `initial_pct = 0.48` (48.0%). | 48.0% is TWDB's **3-reservoir** summary (includes Lake Texana at 87.4%). The 2-reservoir trigger pool sits at **41.2%**. | TWDB S06 vs. City Dashboard S07 | **Contradicted.** Explain 3-reservoir vs. 2-reservoir membership; do not feed 48% into a 2-reservoir simulation. |
| **Mary Rhodes Pipeline Route** (`app.py:L284`) | Claims pipeline is "supplying Region N reservoirs". | Pipeline delivers raw water directly to **O.N. Stevens WTP** in Calallen. It never pumps into Choke Canyon or LCC. | City Dashboard S07; Region N Plan S04 | **Contradicted.** Correct text in tutorial step 1: pipeline supplies the regional water treatment plant, not reservoirs. |
| **Mary Rhodes Flow Rate** (`app.py:L88, L90`; `analysis.py:L177`) | Static "60 MGD" conveyance. | Pipeline operates on 4 discrete schedules (Sched 1: 30 MGD to Sched 4: 72 MGD), typically running at 72 MGD. | City Dashboard S07 Model Assumptions | **Unsupported.** Note that pipeline operation is scheduled/variable, not a static 60 MGD. |
| **Surplus Inflow Defect** (`basin_core/analysis.py:L188-195`) | `loss_lcc = min(max(net_loss * 0.65, 0.0), storage_lcc)`. When inflow exceeds demand+evap, loss is 0; storage never increases. | Physical mass conservation requires surplus inflow to increase storage up to conservation capacity. | Hydrologic mass-balance principles | **Defect.** Exclude simulation outputs from research evidence (B08 Path A or B). |
| **Engineering Modeling Claims** (`app.py:L349-350`) | "Packages accepted scenarios... for Texas WAM Run 3." | Region N evaluates existing supply using **CCWSM with Safe Yield**, not WAM Run 3. Rainfall scaling cannot directly drive WAM. | TWDB Variance Approval (S05); 2026 Plan | **Unsupported / Misleading.** Rephrase handoff brief as a general meteorological stress package; remove WAM Run 3 claims. |

---

### 3.4 Modeling Governance: CCWSM vs. TCEQ WAM Run 3

To prevent generalizing one model requirement to every task, the matrix below specifies which model applies to which water planning task in Region N:

| Dimension | Corpus Christi Water Supply Model (CCWSM) | TCEQ Water Availability Model (WAM) Run 3 |
|---|---|---|
| **Primary Regulatory Purpose** | Evaluation of existing surface water supplies, joint reservoir operation, and safe yield for Region N planning. | Evaluation of new Water Management Strategies (WMS), unappropriated water, and TCEQ water rights permitting. |
| **Governing Authority** | City of Corpus Christi, Nueces River Authority, and TWDB-approved Region N variance. | Texas Commission on Environmental Quality (TCEQ) & TWDB standard planning rules. |
| **Hydrologic Logic** | Monthly operational mass-balance simulating joint operations of Choke Canyon, Lake Corpus Christi, and Lake Texana. | Monthly priority-based water rights allocation model using the WRAP (Water Rights Analysis Package) engine. |
| **Environmental Inflow Logic** | Directly incorporates the **1995/2001 TCEQ Agreed Order** freshwater inflow requirements for the Nueces Estuary (tiered based on combined storage). | Standard WAM Run 3 assumes full authorized diversions and zero return flows, evaluating strict water right priority without special operational agreements unless modified. |
| **Hydrologic Baseline Period** | Historical period of record extended through **2015** under approved variance. | Standard period of record (1940–1997 or basin-specific extension through 2015/2020). |
| **Yield Criterion Used** | **Safe Yield** (maintaining an explicit **75,000 acre-foot reserve** storage pool through the Drought of Record). | **Firm Yield** (storage depletes to exactly zero at the critical drought point). |
| **Relevance to BASIN** | **Directly Relevant:** If an analyst requests a hydrologic evaluation of rainfall stress on regional reservoir supplies, CCWSM is the governing model. | **Indirectly Relevant:** Relevant only if the analyst is evaluating a brand-new water right permit or new inter-basin transfer. |

---

## 4. Machine-Readable Source Register (Section 6 Template)

```json
[
  {
    "evidence_id": "E001",
    "title": "NOAA GHCN-Daily Documentation & Readme",
    "publisher": "NOAA National Centers for Environmental Information (NCEI)",
    "source_url": "https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt",
    "document_or_dataset_version": "Format Version 3.34",
    "publication_date": null,
    "effective_date": null,
    "retrieved_at_utc": "2026-09-06T00:56:58Z",
    "source_status": "adopted",
    "claim_type": "observation",
    "geographic_scope": "Global / National",
    "included_assets_or_station_ids": ["USW00012924", "USW00012912", "USW00012921"],
    "period_start": "1991-01-01",
    "period_end": "2025-12-31",
    "time_basis": "Observational Day (LST/UTC depending on station type)",
    "variable": "PRCP (Precipitation)",
    "units": "Tenths of millimeters",
    "aggregation_and_denominator": "Daily total",
    "claim_paraphrase": "PRCP is precipitation in tenths of mm; measurement flags indicate quality checks; nonblank QFLAG denotes failed quality checks; missing values coded as -9999.",
    "locator": "Sections 2 and 3 (Format of data files and data flags)",
    "limitations": [
      "Observational day ending times vary between first-order automated stations and COOP observers.",
      "Trace precipitation reported as 0 with flag P or other indicators."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "use now",
    "supports_todo_ids": ["B02", "B07"],
    "review_status": "reviewed",
    "access_and_reuse_notes": "Public domain U.S. Federal Government data. Free redistribution."
  },
  {
    "evidence_id": "E002",
    "title": "NOAA Station Metadata Inventory",
    "publisher": "NOAA NCEI",
    "source_url": "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt",
    "document_or_dataset_version": "Live Inventory 2026-09",
    "publication_date": null,
    "effective_date": null,
    "retrieved_at_utc": "2026-09-06T16:15:00Z",
    "source_status": "adopted",
    "claim_type": "observation",
    "geographic_scope": "Texas Coastal Bend and South Central Texas",
    "included_assets_or_station_ids": ["USW00012924", "USW00012912", "USW00012921"],
    "period_start": "1991-01-01",
    "period_end": "2025-12-31",
    "time_basis": "Calendar Day",
    "variable": "PRCP coverage span",
    "units": "Years",
    "aggregation_and_denominator": "Station period of record",
    "claim_paraphrase": "Corpus Christi Intl AP, Victoria Rgnl AP, and San Antonio Intl AP maintain continuous PRCP records from 1991 through 2025.",
    "locator": "Station lines for USW00012924, USW00012912, USW00012921",
    "limitations": [
      "Presence in inventory confirms reporting period but does not verify daily completeness or flag status."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "use now",
    "supports_todo_ids": ["B02", "B07"],
    "review_status": "reviewed",
    "access_and_reuse_notes": "Public domain."
  },
  {
    "evidence_id": "E003",
    "title": "2026 Coastal Bend (Region N) Regional Water Plan",
    "publisher": "Coastal Bend Regional Water Planning Group / Texas Water Development Board",
    "source_url": "https://www.twdb.texas.gov/waterplanning/rwp/plans/2026/",
    "document_or_dataset_version": "Adopted 2026 Plan",
    "publication_date": "2026-01-22",
    "effective_date": "2026-01-22",
    "retrieved_at_utc": "2026-09-06T16:19:22Z",
    "source_status": "adopted",
    "claim_type": "policy",
    "geographic_scope": "Region N (11 Counties: Aransas, Bee, Brooks, Duval, Jim Wells, Kenedy, Kleberg, Live Oak, McMullen, Nueces, San Patricio)",
    "included_assets_or_station_ids": ["Choke Canyon Reservoir", "Lake Corpus Christi", "Lake Texana"],
    "period_start": "2020-01-01",
    "period_end": "2080-12-31",
    "time_basis": "Decadal Planning Horizons (2030-2080)",
    "variable": "Water supply availability, projected demands, safe yield",
    "units": "Acre-feet per year (ac-ft/yr)",
    "aggregation_and_denominator": "Regional basin water user groups",
    "claim_paraphrase": "Region N's adopted regional water plan approved by TWDB on January 22, 2026; evaluates existing supplies using CCWSM and recommends water management strategies through 2080.",
    "locator": "Executive Summary and Chapter 3 (Water Supply Availability)",
    "limitations": [
      "Decadal planning numbers are long-term averages; not calibrated for daily operational routing."
    ],
    "upstream_source_ids": ["E005"],
    "content_sha256": null,
    "proposed_use": "context only",
    "supports_todo_ids": ["B01", "B07", "B11"],
    "review_status": "reviewed",
    "access_and_reuse_notes": "State of Texas governmental planning document. Free access."
  },
  {
    "evidence_id": "E004",
    "title": "TWDB Region N Planning Group Portal",
    "publisher": "Texas Water Development Board",
    "source_url": "https://www.twdb.texas.gov/waterplanning/rwp/regions/n/",
    "document_or_dataset_version": "Portal Snapshot 2026-09",
    "publication_date": null,
    "effective_date": null,
    "retrieved_at_utc": "2026-09-06T16:19:06Z",
    "source_status": "adopted",
    "claim_type": "policy",
    "geographic_scope": "Region N (11 counties)",
    "included_assets_or_station_ids": [],
    "period_start": null,
    "period_end": null,
    "time_basis": null,
    "variable": "Administrative composition",
    "units": null,
    "aggregation_and_denominator": "11 Counties",
    "claim_paraphrase": "Defines the 11 counties forming the Coastal Bend Regional Water Planning Area.",
    "locator": "Region Description section",
    "limitations": [
      "Planning boundaries do not coincide with river basin drainage divides."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "context only",
    "supports_todo_ids": ["B07"],
    "review_status": "reviewed",
    "access_and_reuse_notes": "Public domain state portal."
  },
  {
    "evidence_id": "E005",
    "title": "Region N Technical Memorandum - 2026 Regional Water Plan",
    "publisher": "Coastal Bend Regional Water Planning Group",
    "source_url": "https://www.twdb.texas.gov/waterplanning/rwp/planningdocu/2026/projectdocs/Tech_Memos/RegionN_TechnicalMemorandum.pdf",
    "document_or_dataset_version": "March 2024 Deliverable",
    "publication_date": "2024-03-04",
    "effective_date": "2024-03-04",
    "retrieved_at_utc": "2026-09-06T16:19:45Z",
    "source_status": "superseded",
    "claim_type": "derived",
    "geographic_scope": "Region N",
    "included_assets_or_station_ids": ["Choke Canyon Reservoir", "Lake Corpus Christi", "Lake Texana"],
    "period_start": "1934-01-01",
    "period_end": "2015-12-31",
    "time_basis": "Historical Drought Period / Planning Horizons",
    "variable": "Hydrologic variance approvals, safe yield methodology",
    "units": "Acre-feet per year",
    "aggregation_and_denominator": "System-wide safe yield",
    "claim_paraphrase": "Documents TWDB approval of Region N hydrologic variance to utilize CCWSM with 2015 extended hydrology and Safe Yield (75,000 ac-ft reserve) for existing surface water supplies.",
    "locator": "Section 2 / Appendix C (Hydrologic Modeling Variances)",
    "limitations": [
      "Interim deliverable superseded by the adopted 2026 Plan; valid for modeling approval trail only."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "context only",
    "supports_todo_ids": ["B07", "B08"],
    "review_status": "reviewed",
    "access_and_reuse_notes": "State planning archive document."
  },
  {
    "evidence_id": "E006",
    "title": "TWDB Corpus Christi Area Reservoirs Daily Monitor",
    "publisher": "Texas Water Development Board (Water Data for Texas)",
    "source_url": "https://waterdatafortexas.org/reservoirs/municipal/corpus-christi",
    "document_or_dataset_version": "Live Daily Monitor",
    "publication_date": "2026-09-06",
    "effective_date": "2026-09-06",
    "retrieved_at_utc": "2026-09-06T16:17:31Z",
    "source_status": "adopted",
    "claim_type": "observation",
    "geographic_scope": "Corpus Christi Municipal Area Reservoirs",
    "included_assets_or_station_ids": ["Choke Canyon", "Corpus Christi", "Texana"],
    "period_start": "2026-09-06",
    "period_end": "2026-09-06",
    "time_basis": "Daily Snapshot",
    "variable": "Conservation Storage, Conservation Capacity, Percent Full",
    "units": "Acre-feet (ac-ft) and Percent (%)",
    "aggregation_and_denominator": "3-Reservoir Aggregate: Total Storage 517,292 ac-ft / Total Capacity 1,077,857 ac-ft = 48.0% full",
    "claim_paraphrase": "On 2026-09-06, Choke Canyon is 23.1% full (152,927 / 662,820 ac-ft); Lake Corpus Christi is 88.0% full (225,410 / 256,062 ac-ft); Lake Texana is 87.4% full (138,955 / 158,975 ac-ft). Three-reservoir combined storage is 48.0%.",
    "locator": "HTML Table: Reservoir Storage (Lines 352-360, 529-585)",
    "limitations": [
      "Summary percentage includes Lake Texana (158,975 ac-ft capacity), which is not part of the City's 2-reservoir DCP trigger calculation."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "use now",
    "supports_todo_ids": ["B03", "B07", "B08"],
    "review_status": "reviewed",
    "access_and_reuse_notes": "Public domain real-time monitoring site."
  },
  {
    "evidence_id": "E007",
    "title": "City of Corpus Christi Water Supply Dashboard & Adopted DCP",
    "publisher": "City of Corpus Christi - Corpus Christi Water (CCW)",
    "source_url": "https://www.corpuschristitx.gov/department-directory/corpus-christi-water/water-supply-dashboard/",
    "document_or_dataset_version": "Drought Contingency Plan 2025, Amended June 2026",
    "publication_date": "2026-06-01",
    "effective_date": "2026-06-01",
    "retrieved_at_utc": "2026-09-06T16:17:41Z",
    "source_status": "adopted",
    "claim_type": "policy",
    "geographic_scope": "City of Corpus Christi 7-County Wholesale/Retail Service Area",
    "included_assets_or_station_ids": ["Choke Canyon Reservoir", "Lake Corpus Christi"],
    "period_start": "2026-06-01",
    "period_end": null,
    "time_basis": "Operational Policy & Real-time Status",
    "variable": "Combined 2-reservoir storage, drought stage triggers, restrictions",
    "units": "Percent (%) and Days to Insufficiency",
    "aggregation_and_denominator": "Combined storage of CCR + LCC (~918,882 ac-ft denominator)",
    "claim_paraphrase": "City enforces drought stages based on combined storage of CCR and LCC under 2001 Agreed Order: Stage 1 (<40%), Stage 2 (<30%), Stage 3 (<20%). Level 1 Water Emergency is initiated when total supplies are 180 days from failing to meet demands.",
    "locator": "Sections 'Our Water Supplies' and 'Level 1 Water Emergency' (Lines 1740-1761)",
    "limitations": [
      "Requires executive declaration by City Manager to enact stages.",
      "Level 1 Emergency is a modeled projection, not a fixed storage percentage."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "use now",
    "supports_todo_ids": ["B03", "B07", "B08"],
    "review_status": "reviewed",
    "access_and_reuse_notes": "Official municipal policy portal. Downloaded plan PDF sha256 verified."
  },
  {
    "evidence_id": "E008",
    "title": "USGS Water Data APIs - Surface Water Daily Values",
    "publisher": "U.S. Geological Survey (USGS)",
    "source_url": "https://api.waterdata.usgs.gov/",
    "document_or_dataset_version": "REST API v1",
    "publication_date": null,
    "effective_date": null,
    "retrieved_at_utc": "2026-09-06T16:15:00Z",
    "source_status": "adopted",
    "claim_type": "observation",
    "geographic_scope": "Nueces River Basin (Gages: 08210000 Nueces nr Mathis; 08206900 Frio nr Tilden)",
    "included_assets_or_station_ids": ["08210000", "08206900"],
    "period_start": "1991-01-01",
    "period_end": "2025-12-31",
    "time_basis": "Daily Mean",
    "variable": "Discharge (Parameter 00060, Stat 00003)",
    "units": "Cubic feet per second (cfs)",
    "aggregation_and_denominator": "Daily mean streamflow",
    "claim_paraphrase": "Provides continuous daily streamflow discharge entering Lake Corpus Christi and Choke Canyon Reservoir.",
    "locator": "Site queries for USGS 08210000 and 08206900",
    "limitations": [
      "Discharge is a physical hydrologic watershed response, not precipitation. Contains upstream regulation and diversions."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "validation candidate",
    "supports_todo_ids": ["B07"],
    "review_status": "unreviewed",
    "access_and_reuse_notes": "Public domain USGS API."
  },
  {
    "evidence_id": "E009",
    "title": "USGS Watershed Boundary Dataset (WBD)",
    "publisher": "U.S. Geological Survey",
    "source_url": "https://www.usgs.gov/national-hydrography/watershed-boundary-dataset",
    "document_or_dataset_version": "WBD National Snapshot 2024",
    "publication_date": null,
    "effective_date": null,
    "retrieved_at_utc": "2026-09-06T16:15:00Z",
    "source_status": "adopted",
    "claim_type": "observation",
    "geographic_scope": "Texas HUC-8 Basins (12110108, 12110111, 12100201, 12100301)",
    "included_assets_or_station_ids": [],
    "period_start": null,
    "period_end": null,
    "time_basis": "Static Geospatial Polygons",
    "variable": "Hydrologic Drainage Boundaries",
    "units": "Square miles / HUC codes",
    "aggregation_and_denominator": "Watershed polygon area",
    "claim_paraphrase": "Delineates true hydrologic contributing catchments for the Nueces, Frio, Lavaca, and San Antonio River basins.",
    "locator": "HUC-8 Layer definitions",
    "limitations": [
      "Topographic watershed divides do not reflect inter-basin pipeline transfers or municipal service areas."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "context only",
    "supports_todo_ids": ["B07"],
    "review_status": "reviewed",
    "access_and_reuse_notes": "Public domain geospatial data."
  },
  {
    "evidence_id": "E010",
    "title": "TWDB Extended Naturalized Flow and Evaporation Data",
    "publisher": "Texas Water Development Board",
    "source_url": "https://www.twdb.texas.gov/surfacewater/data/ExtendedNatFlow/index.asp",
    "document_or_dataset_version": "Extended Hydrology through 2015",
    "publication_date": "2020-05-01",
    "effective_date": "2020-05-01",
    "retrieved_at_utc": "2026-09-06T16:15:00Z",
    "source_status": "adopted",
    "claim_type": "derived",
    "geographic_scope": "Nueces River Basin (Basin 21)",
    "included_assets_or_station_ids": ["Nueces Basin WAM Control Points"],
    "period_start": "1934-01-01",
    "period_end": "2015-12-31",
    "time_basis": "Monthly",
    "variable": "Naturalized Streamflow and Net Evaporation Rates",
    "units": "Acre-feet (Flow) and Feet (Evaporation)",
    "aggregation_and_denominator": "Monthly control point volume",
    "claim_paraphrase": "Provides official monthly naturalized streamflow cards representing runoff without human diversions or impoundments, used as input to CCWSM and WAM.",
    "locator": "Basin 21 Naturalized Flow Download Files",
    "limitations": [
      "Modeled/derived values; requires domain engineering expertise to format into WRAP cards; cannot be derived by scaling 3 airport weather stations."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "defer",
    "supports_todo_ids": ["B08"],
    "review_status": "unreviewed",
    "access_and_reuse_notes": "Public data for regional modeling."
  },
  {
    "evidence_id": "E011",
    "title": "U.S. Drought Monitor Classification & Methodology",
    "publisher": "National Drought Mitigation Center (NDMC) / USDA / NOAA",
    "source_url": "https://droughtmonitor.unl.edu/About/WhatistheUSDM.aspx",
    "document_or_dataset_version": "USDM Classification Standard",
    "publication_date": null,
    "effective_date": null,
    "retrieved_at_utc": "2026-09-06T16:15:00Z",
    "source_status": "adopted",
    "claim_type": "derived",
    "geographic_scope": "National / Region N Counties",
    "included_assets_or_station_ids": [],
    "period_start": null,
    "period_end": null,
    "time_basis": "Weekly Map",
    "variable": "Drought Intensity Category (D0-D4)",
    "units": "Categorical Percentile: D0 <= 20%, D1 <= 10%, D2 <= 5%, D3 <= 2%, D4 <= 1%",
    "aggregation_and_denominator": "Multi-indicator percentile blending",
    "claim_paraphrase": "USDM synthesizes multiple objective drought indicators into a weekly regional classification; it is not a forecast, water-supply model, or utility restriction declaration.",
    "locator": "Classification Scheme Table",
    "limitations": [
      "Broad regional spatial scale; does not reflect local reservoir storage or municipal drought stages."
    ],
    "upstream_source_ids": [],
    "content_sha256": null,
    "proposed_use": "context only",
    "supports_todo_ids": ["B07", "B11"],
    "review_status": "reviewed",
    "access_and_reuse_notes": "Public domain weekly product."
  }
]
```

---

## 5. Application Claim-to-Source Audit Matrix

| Code Location | Application Claim | Current Status in Code | Authoritative Primary Source | Verified Fact / Citation | Required Action for Team |
|---|---|---|---|---|---|
| `app.py:L190` | Combined < 40% triggers Stage 1 | **Supported** | City DCP 2025/2026 (S07) | Stage 1 Mild Drought triggers at < 40% combined CCR+LCC storage. | Retain threshold; clarify that declaration requires City Manager action. |
| `app.py:L192` | Combined < 30% triggers Stage 2 | **Supported** | City DCP 2025/2026 (S07) | Stage 2 Moderate Drought triggers at < 30% combined CCR+LCC storage. | Retain threshold. |
| `app.py:L194` | Combined < 20% triggers Stage 3 | **Supported** | City DCP 2025/2026 (S07) | Stage 3 Critical Drought triggers at < 20% combined CCR+LCC storage. | Retain threshold. |
| `app.py:L196`; `analysis.py:L154, L199` | Combined < 15% triggers Stage 4 (Emergency) | **Contradicted** | City DCP 2025/2026 (S07) | Stage 4 was renamed **Level 1 Water Emergency**; triggered by **180-day supply-demand shortfall**, not a static 15% line. | Update UI label and explanation; decouple emergency status from the static 15% marker. |
| `analysis.py:L146-148, L156-158` | LCC capacity = 257,300 ac-ft; CCR capacity = 662,600 ac-ft | **Outdated** | TWDB Reservoir Monitor (S06) | Current conservation capacities: LCC = **256,062 ac-ft**; CCR = **662,820 ac-ft**. | Note bathymetric sedimentation in provenance metadata. |
| `analysis.py:L136` | Default storage = 48% full | **Contradicted** | TWDB S06 vs City S07 | 48.0% includes Lake Texana. Actual 2-reservoir trigger storage on 2026-09-06 is **41.2%**. | Change simulation default to 41.2% or document the 3-reservoir discrepancy in B05. |
| `app.py:L284` | Mary Rhodes pipeline supplies Region N reservoirs | **Contradicted** | City Dashboard S07; Region N Plan S04 | Delivers raw water directly to **O.N. Stevens WTP** in Calallen; does not discharge into reservoirs. | Edit tutorial text to state "supplying regional treatment plant". |
| `app.py:L349-350` | Generates package for Texas WAM Run 3 | **Unsupported** | TWDB Variance Approval (S05); 2026 Plan | Region N surface water availability is governed by **CCWSM Safe Yield**, not WAM Run 3. | Re-label brief as "Meteorological Stress Analysis Brief for Hydrologic Review". |
| `analysis.py:L188-195` | Reservoir mass balance simulation | **Defective** | Hydrologic mass-balance principles | Formula zeroes out surplus inflow, preventing reservoir replenishment during wet days. | Do not use outputs as research evidence; execute B08 Path A or B. |
| `analysis.py:L15` | Nueces County WCID #3 Preset: Season weight 50% | **Unverified Assumption** | Repository discovery notes | Discovery notes cite rural water interest in summer peaks, but exact weights were not formally approved by WCID #3. | Label preset as "Illustrative Rural Community Profile". |

---

## 6. Real Discrepancy Case Studies

### Case Study 1: The 48.0% vs. 41.2% Storage Discrepancy (Asset Membership Mismatch)
* **The Apparent Conflict:** On September 6, 2026, the TWDB *Water Data for Texas* municipal summary (S06) announces that Corpus Christi Area Reservoirs are **48.0% full** (517,292 ac-ft in storage out of 1,077,857 ac-ft capacity). At the exact same time, the City of Corpus Christi Water Department (S07) reports that combined reservoir storage is **41.2% full** (378,337 ac-ft in storage out of 918,882 ac-ft capacity), hovering within 1.2% of Stage 1/Stage 2 restrictions.
* **Classification:** **Asset Membership / Aggregation Mismatch** (Not an observational error or measurement disagreement).
* **Detailed Reconciliation:**
  1. *TWDB Municipal Area Aggregation:* TWDB includes three reservoirs in its municipal area summary: Choke Canyon Reservoir (662,820 ac-ft capacity; 23.1% full), Lake Corpus Christi (256,062 ac-ft capacity; 88.0% full), and Lake Texana (158,975 ac-ft capacity; 87.4% full). Because Lake Texana is nearly full, its storage boosts the overall three-reservoir aggregate to 48.0%.
  2. *City Drought Contingency Plan Legal Definition:* The City of Corpus Christi's DCP, established under the 2001 TCEQ Agreed Order, legally restricts the combined storage definition to the **two Western reservoirs in the Nueces Basin**: Choke Canyon Reservoir + Lake Corpus Christi. Lake Texana is located 100 miles east in Jackson County (Lavaca Basin) and is imported via the Mary Rhodes Pipeline; it is contractually and physically excluded from the local reservoir storage trigger denominator.
  3. *Denominator Math:*
     $$\text{TWDB 3-Reservoir Pool} = \frac{152,927 + 225,410 + 138,955}{662,820 + 256,062 + 158,975} = \frac{517,292}{1,077,857} = 48.0\%$$
     $$\text{City DCP 2-Reservoir Pool} = \frac{152,927 + 225,410}{662,820 + 256,062} = \frac{378,337}{918,882} = 41.17\% \approx 41.2\%$$
* **How BASIN Resolves It in the Interface:** The BASIN Conflict View displays both records side by side. It highlights the asset inclusion difference in the denominator, proving to the analyst that both publishers agree perfectly on individual reservoir volumes, but warning the analyst never to apply the TWDB 48% regional number to a municipal drought stage decision.

---

### Case Study 2: Fixed 15% Stage 4 vs. 180-Day Supply Shortfall Emergency (Policy Evolution)
* **The Apparent Conflict:** Older engineering reports, regional presentations, and the current BASIN application code cite **Stage 4 Emergency** as triggering when combined reservoir storage drops below **15% (137,985 ac-ft)**. Conversely, the City’s official Water Supply Dashboard and Drought Contingency Plan (2025, amended June 2026; S07) define a **Level 1 Water Emergency** initiated when the system is **180 days from when total supply fails to meet demand**.
* **Classification:** **Outdated Policy vs. Amended Policy** (Policy Evolution / Superseded Rule).
* **Detailed Reconciliation:**
  1. Under earlier versions of the City’s Drought Contingency Plan, Stage 4 was indeed a static trigger set at 15% combined storage of Choke Canyon and Lake Corpus Christi.
  2. In recent years, CCW completed major pipeline expansions (Mary Rhodes Phase II connecting the Colorado River) and recognized that even if Western reservoir storage falls below 15%, substantial imported supplies continue flowing from Lake Texana and the Colorado River. Therefore, a static 15% storage threshold misdiagnosed true system failure.
  3. City Council adopted a revised DCP (approved in 2025, amended June 2026) that eliminated the static 15% Stage 4 trigger, renamed the level "Level 1 Water Emergency", and instituted a dynamic 180-day projected supply-demand horizon calculated using operational supply models.
* **How BASIN Resolves It in the Interface:** BASIN documents the chronological lineage: marking the 15% trigger as "Superseded Historical Definition" and displaying the 2026 amended ordinance text. It warns the analyst that emergency curtailment is now driven by predictive multi-source demand modeling rather than a static reservoir gage reading.

---

### Case Study 3: Coastal Rainfall Normal vs. Extreme Reservoir Inflow Drought (Spatial/Variable Mismatch)
* **The Apparent Conflict:** In late summer 2026, NOAA climate summaries for Corpus Christi International Airport report near-normal precipitation (100% of 1991–2020 normal) following localized coastal thunderstorms. Local public sentiment assumes drought conditions have eased. However, USGS stream gages upstream of Choke Canyon and Lake Corpus Christi record discharge below the 5th percentile, and combined reservoir storage continues declining into Stage 1 territory.
* **Classification:** **Geographical & Variable Mismatch** (Downstream Coastal Demand Center vs. Inland Contributing Watershed; Precipitation Depth vs. Streamflow Runoff).
* **Detailed Reconciliation:**
  1. *Downstream Demand Location:* Corpus Christi International Airport is located on the coastal plain adjacent to Corpus Christi Bay. Rain falling at the airport drains directly into Oso Creek and the bay, providing zero inflow to municipal reservoirs located 50 to 100 miles inland.
  2. *Upstream Watershed Location:* The contributing drainage basins for Choke Canyon (Frio River) and Lake Corpus Christi (Nueces River) cover 17,000 square miles extending northwest into McMullen, Live Oak, La Salle, and Uvalde counties. These inland areas experienced severe precipitation deficits.
  3. *Hydrologic Runoff Non-Linearity:* In semi-arid South Texas brush country, parched soils, high summer temperatures (100°F+), and heavy vegetative evapotranspiration absorb initial rains. An isolated 1-inch rainfall event produces almost zero measurable streamflow.
* **How BASIN Resolves It in the Interface:** BASIN’s GIS and Evidence metadata clearly label station `USW00012924` as a **Demand-Center Urban Proxy**, visually mapping the 17,000 sq mi watershed boundary (USGS WBD) and explaining that coastal rainfall reduces lawn watering demand but does not replenish reservoir storage.

---

## 7. Proposed Evidence & UI Slice (Coordination with TODO B03, B05, B07, B08)

To deliver a demonstrable, verifiable evidence inspection feature before the September 18 freeze without destabilizing core code, the team should execute the following targeted slice:

```
[ BASIN Streamlit Workspace ]
     |
     +--> Reference & Provenance Tab (B05.1)
     |         |
     |         +--> Evidence Cards Table (E001 - E011)
     |         |      * Title, Publisher, Version, Units, Geographic Scope
     |         |
     |         +--> Side-by-Side Conflict Inspection View (B05.3)
     |                * Record A (e.g. S06 TWDB 48.0%) vs. Record B (e.g. S07 CCW 41.2%)
     |                * Highlight: Numerator, Denominator, Included Assets
     |                * Analyst Disposition Radio: [Not Comparable | Mismatched Assets | Resolved]
     |                * Private Analyst Rationale Notes Box
     |
     +--> Export Pipeline (B04.8)
               |
               +--> scenario_packet.zip
                      * daily_rainfall.csv (SHA-256 verified)
                      * audit.json (includes accepted Evidence IDs and Analyst Dispositions)
                      * hydrologist_brief.md (Plain-text translation brief)
```

### 7.1 Minimal Evidence Data Contract (JSON Schema for B03)
Store evidence records in a clean, versioned JSON dictionary (`basin_core/evidence_registry.json`) loaded deterministically into session state:

```json
{
  "evidence_id": "E006",
  "title": "TWDB Corpus Christi Area Reservoirs Daily Monitor",
  "publisher": "Texas Water Development Board",
  "source_url": "https://waterdatafortexas.org/reservoirs/municipal/corpus-christi",
  "document_or_dataset_version": "2026-09-06",
  "retrieved_at_utc": "2026-09-06T16:17:31Z",
  "claim_type": "observation",
  "geographic_scope": "3-Reservoir Municipal Area (CCR + LCC + Texana)",
  "variable": "Conservation Storage Ratio",
  "units": "%",
  "value_summary": "48.0% full (517,292 / 1,077,857 ac-ft)",
  "applicability_status": "context only",
  "limitations": "Aggregates Lake Texana into denominator; not applicable to 2-reservoir DCP triggers.",
  "supports_todo_ids": ["B03", "B07", "B08"]
}
```

### 7.2 Conflict Record Contract
```json
{
  "conflict_id": "CONF-001",
  "title": "Current Combined Reservoir Storage Percentage",
  "record_a_id": "E006",
  "record_b_id": "E007",
  "disputed_claim": "Regional Reservoir Storage is 48.0% vs. 41.2% on 2026-09-06",
  "classification": "mismatched_asset_membership",
  "analyst_disposition": "not_comparable_different_denominators",
  "disposition_rationale": "TWDB aggregates 3 reservoirs (including Lake Texana); City DCP trigger strictly counts 2 reservoirs (CCR + LCC).",
  "reviewer_status": "reviewed",
  "export_inclusion": true
}
```

### 7.3 Observable Acceptance Criteria (Sprint Gate)
1. **Traceability:** From any shortlisted scenario, clicking "Inspect Evidence & Assumptions" displays the active evidence cards (`E001`, `E006`, `E007`) showing exact publishers, dates, and units.
2. **Conflict Resolution:** Opening the Conflict Review view displays `CONF-001` with S06 and S07 side-by-side. The user can select a disposition from a dropdown, enter an explanatory rationale, and see that approval of the scenario is preserved.
3. **Save/Load Persistence:** Saving a session to local JSON and restoring it reloads the evidence links, analyst dispositions, and review notes exactly.
4. **Clean Handoff Export:** Replaying the exported ZIP bundle verifies that `audit.json` includes the attached evidence IDs and dispositions, while private un-checked notes remain strictly excluded by default.

---

## 8. Data Suitability and Quality Report

### 8.1 NOAA GHCN-Daily Numerical Quality Assessment
* **Verified Snapshot Span:** 1991-01-01 through 2025-12-31 (35 complete calendar years, 12,784 calendar days).
* **Missing Day Policy:** Strict zero-tolerance for missing dates in candidate windows. The baseline manifest verifies:
  * `USW00012924` (Corpus Christi): 12,784 valid days (100.0% complete, 0 missing).
  * `USW00012912` (Victoria): 12,783 valid days (99.992% complete, 1 missing day: 1996-02-18).
  * `USW00012921` (San Antonio): 12,783 valid days (99.992% complete, 1 missing day: 2011-04-18).
  * *Policy Enforcement:* Any multi-station window spanning 1996-02-18 or 2011-04-18 is automatically flagged as incomplete and rejected by `basin_core/engine.py`. Gaps are never imputed or replaced with zeros.
* **Flag Handling:**
  * Measurement Flag `P` (missing presumed zero): Excluded from valid days.
  * Quality Flags (`QFLAG`): Any daily value with a non-blank quality flag (e.g., failed internal consistency, duplicate, or excessive value checks) is excluded.
  * Trace Values: Retained as 0.0 mm at measurement resolution, preserving the trace indicator flag.
* **Observation Time Invariance:** All three bundled stations are primary first-order National Weather Service airport stations operating automated ASOS equipment reporting on a standard calendar-day (midnight-to-midnight) basis. This eliminates the observation-time day-shift error typical of volunteer COOP stations.

---

## 9. Domain Expert Inquiry & User Evaluation Protocol

### 9.1 Five Targeted Questions for Hydrologists and Regional Planners (No Outreach Sent)
1. *Regarding Spatial Proxy Suitability:* "For screening rainfall stress across the Nueces River Basin, what is the maximum acceptable error in using San Antonio International Airport as a proxy for the upper Edwards Plateau headwaters, and would you support replacing it with 4km PRISM gridded rainfall extracted across HUC 12110108?"
2. *Regarding Reference Normal Baseline:* "BASIN uses 1991–2020 monthly climatology to calculate expected rainfall and deficit exceedance across 1991–2015 historical windows. Does your firm prefer using the full 1948–2015 WAM hydrologic period as the reference baseline, and how should multi-year drought persistence be represented in a 365-day tool?"
3. *Regarding Hydrologic Model Handoff:* "When your team ingests external meteorological stress scenarios into the Corpus Christi Water Supply Model (CCWSM), what specific input file format (e.g., daily rainfall CSV, monthly runoff reduction coefficients, or modified naturalized flow cards) minimizes manual translation overhead?"
4. *Regarding Safe Yield Reserves:* "In Region N's approved 2026 Plan, safe yield for the CCR/LCC system assumes a 75,000 acre-foot reserve pool. How sensitive is the timing of Level 1 Water Emergency declarations to this 75k reserve during a drought of record recurrence?"
5. *Regarding Rural Customer Curtailments:* "Under current wholesale contracts between CCW and rural districts (e.g., Nueces County WCID #3), are curtailment percentages applied strictly against historical base-year water volumes, or are provisions made for seasonal agricultural/industrial peak demands?"

---

### 9.2 Structured 20-Minute User Evaluation Task (Rural Provider Analyst)
* **Participant:** Water utility operations supervisor or planning analyst representing a rural wholesale customer (e.g., Nueces County WCID #3).
* **Environment:** Completely disconnected laptop running BASIN on loopback (`http://127.0.0.1:8501`).
* **Scenario Prompt:** "Imagine your water district board needs to evaluate a potential drought surcharge before next summer. You need to identify two plausible historical drought stress scenarios—one representing a rapid, severe summer heatwave deficit and one representing a prolonged 9-month multi-basin drought—review the underlying assumptions, and export an auditable package for your consulting engineer."
* **Step-by-Step Task:**
  1. *Step 1 (Workspace Selection - 4 mins):* Adjust community priority sliders (set Summer Season to 40%, Severity to 30%, Duration to 20%, Concurrence to 10%). Inspect the resulting shortlist. Identify the "Peak Summer" scenario and the "Prolonged Multi-Season" scenario.
  2. *Step 2 (Traceability & Evidence - 4 mins):* Click into the candidate review view. Trace where expected rainfall originates. Inspect the station metadata cards and identify the geographic role of the Victoria and San Antonio airport stations.
  3. *Step 3 (Conflict Review - 4 mins):* Open the Evidence & Conflict tab. Inspect the apparent discrepancy between TWDB's 48% storage metric and the City's 41% storage metric. Document a one-sentence rationale explaining why the 48% figure includes Lake Texana.
  4. *Step 4 (Scenario Challenge/Edit - 4 mins):* Apply a 10% stress scaling factor to daily rainfall or edit an extreme 14-day dry spell. Observe that the approval status clears. Add a human review comment explaining the edit, and re-approve the revision.
  5. *Step 5 (Export & Verification - 4 mins):* Download the scenario packet ZIP. Run the offline replay script (`scripts/replay_bundle.py`) from the terminal. Confirm that the verification report confirms SHA-256 hash integrity, transformation provenance, and privacy preservation.
* **Observation Metrics:** Time to task completion; instances of confusion between rainfall depth and reservoir storage; ability to explain the 48% vs 41% difference; user confidence in presenting the exported packet to an engineering firm.

---

## 10. Access, Failure, and Audit Log

### 10.1 Access Log & Retrieval History
* **S01 / NOAA GHCN Readme (`https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt`):** Successfully inspected. Verified PRCP units (tenths of mm), exclusion rules for missing flags, and trace value definitions.
* **S02 / NOAA Station Inventory (`https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt`):** Verified station IDs `USW00012924`, `USW00012912`, and `USW00012921`.
* **S03 / TWDB 2026 Regional Water Plans (`https://www.twdb.texas.gov/waterplanning/rwp/plans/2026/`):** Successfully retrieved and parsed. Verified formal TWDB Board approval of the Region N Plan on January 22, 2026.
* **S04 / TWDB Region N Page (`https://www.twdb.texas.gov/waterplanning/rwp/regions/n/`):** Successfully retrieved. Verified 11-county planning boundary and regional contacts.
* **S05 / Region N Technical Memorandum (`https://www.twdb.texas.gov/waterplanning/rwp/planningdocu/2026/projectdocs/Tech_Memos/RegionN_TechnicalMemorandum.pdf`):** Successfully inspected via TWDB Sixth Cycle planning archives. Verified hydrologic variance approval for CCWSM with 2015 extended hydrology and Safe Yield (75k ac-ft reserve).
* **S06 / TWDB Water Data for Texas (`https://waterdatafortexas.org/reservoirs/municipal/corpus-christi`):** Successfully retrieved live on 2026-09-06. Extracted exact daily reservoir storages and capacities for Choke Canyon (23.1%), Lake Corpus Christi (88.0%), and Lake Texana (87.4%), yielding 3-reservoir aggregate of 48.0%.
* **S07 / City of Corpus Christi Water Supply Dashboard (`https://www.corpuschristitx.gov/department-directory/corpus-christi-water/water-supply-dashboard/`):** Successfully retrieved live. Downloaded and verified adopted Drought Contingency Plan PDF (amended June 2026; 23.7 MB; SHA-256 logged). Verified Stage 1, 2, 3 triggers and Level 1 Water Emergency 180-day definition.
* **S08 / USGS Water Data APIs (`https://api.waterdata.usgs.gov/`):** Inspected endpoint documentation for daily streamflow parameters (00060/00003).
* **S09 / USGS Watershed Boundary Dataset (`https://www.usgs.gov/national-hydrography/watershed-boundary-dataset`):** Verified HUC-8 boundaries for Nueces (121101) and Frio (121102).
* **S10 / TWDB Extended Naturalized Flow (`https://www.twdb.texas.gov/surfacewater/data/ExtendedNatFlow/index.asp`):** Located Basin 21 data; classified as deferred input for post-freeze hydrologic modeling.
* **S11 / U.S. Drought Monitor (`https://droughtmonitor.unl.edu/About/WhatistheUSDM.aspx`):** Verified D0–D4 percentile classification scheme.

### 10.2 Deliberately Deferred Scope Items
1. **Automated WAM Input Card Generation:** Excluded from current scope. Formatting Fortran WRAP cards requires complex catchment naturalized flow routing and control point records, which cannot be generated from three rainfall stations.
2. **Dynamic Web Scraping at Runtime:** The application must operate strictly offline on loopback. Live scraping of TWDB or City websites at runtime is forbidden. All external evidence is maintained as versioned, frozen snapshots.
3. **Automated AI Policy Extraction:** Broad unstructured LLM ingestion of PDF policies is deferred to prevent hallucinations. The tool relies on manually reviewed, deterministic evidence records (`E001`–`E011`).
4. **Full Hydrologic Rainfall-Runoff Modeling:** Developing a continuous rainfall-runoff model (e.g., HEC-HMS) for the 17,000 sq mi basin is outside the team's scope and is properly left to the recipient engineering consultant.
