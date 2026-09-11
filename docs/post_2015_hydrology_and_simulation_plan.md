# Post-2015 Corpus Christi context and storage-experiment proposal

**Exploratory research and implementation proposal for BASIN**
*Date: September 2026 | Baseline Repository: `basin-latest`*

> **Status and boundary.** This document mixes dated public context with proposed modeling assumptions. It is not part of BASIN's verified evidence registry and is not an authoritative regulatory fact base. The application must present the 75,000 ac-ft inactive-storage value, sector shares, curtailment schedule, 7.8% context marker, pipeline cases and simplified pass-through formula as configurable assumptions. Primary sources verified during integration include the City's [April 24 water-supply memo](https://www.corpuschristitx.gov/media/btvn01mr/20260424_memo_water-supply-update.pdf), [August 25 pass-through announcement](https://www.corpuschristitx.gov/news/posts/tceq-approves-request-to-pause-reservoir-pass-through-requirements/), [March 25, 2025 pipeline release](https://www.corpuschristitx.gov/news/posts/city-council-approves-critical-infrastructure-upgrades-for-mary-rhodes-pipeline/), and [water-supply dashboard](https://www.corpuschristitx.gov/department-directory/corpus-christi-water/water-supply-dashboard/). Other claims below require source-by-source review before public use.

---

## 1. Executive Summary & Problem Framing

The City of Corpus Christi and the 11-county Coastal Bend Regional Water Planning Area (**Region N**) face a severe hydrologic and institutional disconnect:
1. **The 2015 Planning Void:** The primary regulatory water planning instrument for Region N—the **Corpus Christi Water Supply Model (CCWSM)**, developed using the Texas Water Availability Modeling (WAM) framework—**stops its hydrologic calibration at 2015**. In January 2024, the Texas Water Development Board (TWDB) granted Region N a formal **hydrologic variance** allowing the 2026 Regional Water Plan to evaluate surface water supplies using this pre-2015 dataset and an assumed 75,000 acre-foot "safe yield" reserve, explicitly because **there was insufficient state and regional funding to extend the model through current conditions**.
2. **Recent drought context:** The bundled BASIN observation snapshot extends through 2025, while the planning-model history discussed here may use a different cutoff. The City's April 24, 2026 memo reports that on April 16 Lake Corpus Christi was at 8.8%, Choke Canyon at 7.5%, and combined storage at **7.8%**. The memo does not establish that 75,000 ac-ft is a physical intake-failure threshold.
3. **Financial, Political, and Regulatory Fallouts:**
   - On **May 20, 2026**, S&P Global Ratings revised Corpus Christi's debt rating outlook to **Negative**, citing depleted water reserves and delayed infrastructure execution.
   - Texas Governor Greg Abbott publicly raised the prospect of a **state takeover** of the city's water governance.
   - On **August 19, 2026**, Texas 2036 published a landmark evaluation (*The State Water Plan & The Coastal Bend Water Crisis* by Jeremy Mazur) revealing that across 25 years and five planning cycles, **neither the state water plan nor Region N plans projected any municipal water shortage in the 2020s**.
4. **The Industrial Baseload Reality:** Heavy industrial buildouts in San Patricio and Nueces counties (Gulf Coast Growth Ventures / Exxon-SABIC, Cheniere LNG, Steel Dynamics) consume **over 50% of the regional potable water supply**. The City established the **Drought Surcharge Exemption Fee (DSEF)**, allowing industrial facilities to pay alternative compliance fees to fund long-term water supplies rather than curtail cooling water, while residential households faced strict sprinkler bans and steep surcharges ($4–$8/kGal).
5. **Role of the BASIN experiment:** BASIN can compare transparent, user-selected rainfall and infrastructure assumptions. Its mass-balance experiment is uncalibrated and does not replace the City's supply model, establish operational feasibility, or predict restriction dates.

---

## 2. Updated Real-World Context: Post-2015 Hydrology & Policy

### 2.1. The Western Reservoir System & Combined Storage Triggers
The core surface storage serving Corpus Christi and wholesale customers (San Patricio Municipal Water District, Port Aransas, Ingleside, Portland, Rockport, Alice) consists of two impoundments:
- **Choke Canyon Reservoir (CCR):** Conservation capacity of ~663,400 acre-feet (elevation 220.5 ft MSL).
- **Lake Corpus Christi (LCC):** Conservation capacity of 256,339 acre-feet (elevation 94.0 ft NGVD29 per TWDB 2016 Volumetric Survey).
- **Combined Conservation Capacity:** **~919,460 to 919,739 acre-feet** (historically rounded to 919,300–919,900 ac-ft).

The City of Corpus Christi Drought Contingency Plan (DCP) indexes mandatory conservation stages to the combined percentage of this system:

| Stage | Trigger Threshold (Combined Storage) | Clear Threshold (15 Consecutive Days) | Key Measures & Mandatory Restrictions |
|---|---|---|---|
| **Stage 1 (Mild)** | **< 40%** | **> 50%** | Lawn irrigation limited to 1 day/week based on trash collection schedule. |
| **Stage 2 (Moderate)** | **< 30%** | **> 40%** | Lawn irrigation restricted to 1 day every 2 weeks; commercial car washes restricted; voluntary 10% reductions. |
| **Stage 3 (Critical)** | **< 20%** | **> 30%** | **Total ban on automated lawn irrigation and sprinklers**. Drip irrigation and hand watering only within narrow time windows; pool filling banned. |
| **Level 1 Water Emergency** | The City's current dashboard describes a 180-day supply-versus-demand condition, not a fixed 10% trigger. | See the current adopted plan. | BASIN's 10% line is an illustrative marker and must not be labeled as adopted policy. |

### 2.2. The 2024–2026 Drought Timeline & Mid-April 2026 Low
- **Mid-December 2024:** Western reservoir combined storage dipped below 20%, officially triggering **Stage 3 Critical Drought Restrictions**.
- **April 16, 2026:** The City's April 24 memo reports **7.8% combined storage** (Lake Corpus Christi 8.8%; Choke Canyon 7.5%). BASIN uses 7.8% only as a context marker.
- **May 20, 2026:** S&P Global Ratings placed Corpus Christi's debt on Negative outlook.
- **August 4, 2026:** Heavy tropical moisture in the Nueces and Frio river basins lifted storage above 30%, easing restrictions to **Stage 2**.
- **August 27, 2026:** Continued runoff lifted storage above 40%, easing restrictions to **Stage 1** (1-day/week watering).
- **September 9, 2026 status shown on the City's Stage 1 page:**
  - **Lake Corpus Christi:** **87.2% full**
  - **Choke Canyon Reservoir:** **22.9% full** (~151,900 ac-ft)
  - **Combined Storage:** **40.8% full**
  - The causal explanation for the different reservoir responses requires hydrologic evidence and is not inferred by BASIN.

### 2.3. The Mary Rhodes Pipeline (MRP) — Regional Lifeline
To offset western reservoir vulnerability, Corpus Christi imports water from eastern river basins:
- **Lake Texana (Phase 1):** Firm "take-or-pay" contract for **31,440 acre-feet per year** (LNRA), plus supplemental interruptible water (4,500 to 11,000 ac-ft/yr).
- **Colorado River / Garwood Rights (Phase 2):** High-priority senior agricultural water rights of **35,000 acre-feet per year** pumped from the Colorado River into Lake Texana.
- **March 2025 Pump Expansion:** The City's March 25 release reports operation at **72–79 MGD**. BASIN stores 72 MGD as context metadata; the current experiment does not directly convert that value into inflow.

### 2.4. Seawater Desalination vs. Brackish Groundwater Reality
- **Seawater Desalination Deadlock (September 1, 2026):**
  - Even though the 30 MGD Inner Harbor plant obtained TCEQ TPDES discharge permits (March 13, 2025) and USACE permits (March 26, 2025), the Corpus Christi City Council voted **5–3 against the design-build contract** on **September 1, 2026**.
  - *Drivers:* Capital costs ballooned to **$700M–$1B**; environmental justice claims under Title VI (Hillcrest/North Beach brine discharge); and temporary rain relief. No seawater desalination will be operational before **2029–2031**.
- **Brackish Groundwater RO at O.N. Stevens ($175 Million):**
  - The City's real near-term hedge is the **21.3 MGD Brackish Groundwater Reverse Osmosis Project** at the O.N. Stevens Water Treatment Plant (ONSWTP).
  - Phased delivery schedule:
    - Phase 1: 3.91 MGD (Feb/March 2027)
    - Phase 2: 5.3 MGD (May 2027)
    - Phase 3: 5.3 MGD (September 2027)
    - Phase 4: 6.7 MGD (March 2028)
  - Draws from the **Western Well Field** in the Gulf Coast Aquifer via a dedicated raw-water pipeline directly to ONSWTP (bypassing the Nueces River to avoid bed and evaporation losses).

### 2.5. Environmental inflow context
The reservoir system is legally bound by the **2001 Agreed Order** to release freshwater to Nueces Bay:
- **2001 Agreed Order Baseline:** Mandates monthly pass-through releases when combined storage is $> 30\%$, scaling up to 138,000 ac-ft/yr when storage is $\ge 70\%$. Below 30%, pass-through is suspended.
- **Emergency order reported by the City on August 25, 2026:** The TCEQ Executive Director approved a temporary pause in pass-through requirements at or below 50% combined storage, effective for 120 days through December 23 with a stated 60-day extension condition. The City's release said Commission consideration was scheduled for September 9; this document does not independently establish the outcome of that later meeting.
- BASIN's daily `35% of modeled inflow, capped at 100 ac-ft/day` formula is an illustrative placeholder. It does not reproduce the monthly targets in the 2001 Agreed Order or quantify water retained under the emergency order.

### 2.6. Evaporation Science: TWDB On-Lake Buoys vs. Terrestrial Pan Evaporation
- TWDB deployed **NexSens CB-650 floating meteorological buoys** on Choke Canyon Reservoir to collect real-time water surface temperature, wind speed, solar radiation, and humidity.
- Demonstrates that terrestrial Class A evaporation pans overestimate winter reservoir evaporation and misjudge peak summer thermal lag compared to aerodynamic energy-balance methods.

### 2.7. Dated public narrative and model boundary

Public reporting used "Day Zero" language during the 2026 drought, while the City disputed claims that the community would completely run out of water. Those positions are public context, not outputs from BASIN. The City's April 24 memo reports 7.8% combined storage on April 16; it does not identify the configured 75,000 ac-ft floor as an intake-failure threshold. The City's current dashboard defines Level 1 through a projected 180-day supply-versus-demand condition rather than BASIN's illustrative 10% band.

The Mary Rhodes Pipeline, customer contracts, drought surcharges, ballot proposals and environmental orders each have operational or legal conditions that this experiment does not encode. The sector shares and storage-dependent curtailments in the modern-stress preset are user-visible assumptions for sensitivity analysis. They must not be described as the Fair Water proposal, an adopted drought schedule, a guarantee of supply, or a prediction that taps will run dry.

The September 9 Stage 1 page reported Lake Corpus Christi at 87.2%, Choke Canyon at 22.9%, and combined storage at 40.8%. These dated observations can be cited as context, but BASIN does not extrapolate a future restriction date or "Day Zero" trajectory from them.

---

## 3. Gap Analysis: Repository Knowledge vs. Newly Integrated Findings

| Hydrologic Dimension | Previous Codebase Baseline | Newly Discovered Official Reality | Integration into BASIN Simulation |
|---|---|---|---|
| **Model Horizon** | Frozen at **2015** (`docs/methodology.md`). | **2020–2026 Drought of Record** occurred; TWDB hydrologic variance granted due to budget shortfall. | Benchmark against true modern drought; document 2020–2026 conditions in scenarios. |
| **Drought Severity Depth** | Minimum band was 15% (`stage_bands_pct = (0.4, 0.3, 0.2, 0.15)`). | City memo reports **7.8% combined storage on April 16, 2026**. | Add an illustrative 10% band and assumed 75,000 ac-ft inactive-storage floor; neither is an adopted trigger or proven physical limit. |
| **Credit & Governance** | Unmentioned. | S&P debt outlook downgraded to **Negative (May 20, 2026)**; Gov. Abbott threatened state takeover. | Provide risk-boundary analytics for municipal debt and governance thresholds. |
| **State Planning Critique** | Not documented. | **Texas 2036 Report (Aug 19, 2026)** by Jeremy Mazur exposed 25-year forecasting failure. | Integrate Texas 2036 recommendations (stress-testing beyond DOR, tracking execution milestones). |
| **Mary Rhodes Pipeline** | Fixed toggle (370 vs 554 ac-ft/day). | City reported **72–79 MGD** operation in March 2025. | Keep 72 MGD as context metadata; the implemented toggle still compares the configured 370 versus 554 ac-ft/day demand cases. |
| **Industrial vs Municipal Demand** | Lumped uniform demand. | Heavy industry consumes **>50% of supply**; Drought Surcharge Exemption Fee protects industrial cooling. | Split demand into Tier 1 (Municipal Essential), Tier 2 (Industrial Contracted), Tier 3 (Outdoor Irrigation). |
| **Estuary Environmental Inflows** | Fixed uncalibrated inflow coefficient. | City's August 25 release reports the temporary 50% condition. | Add a clearly labeled placeholder pass-through formula; do not present it as reproduction of the order. |
| **Desalination Reality** | Assumed future baseline. | Council voted 5–3 against contract on Sept 1, 2026; 21.3 MGD Brackish RO plant at ONSWTP is real near-term hedge (2027–2028). | Model zero seawater desal through 2029; add optional phased brackish groundwater toggle. |
| **Evaporative Scaling** | Step function (June–Sept vs Oct–May). | Dynamic power-law surface area shrinkage ($\text{Area} \propto S^{0.65}$) and TWDB buoy data. | Implement power-law EAC scaling and 12-month smooth pan evaporation curve. |
| **Low-storage context and sector sensitivity** | Unmodeled. | City sources distinguish the 180-day Level 1 supply condition from a physical dry-tap claim. | Keep inactive storage, bands, sector shares and curtailments configurable and visibly illustrative; do not label them as adopted policy. |

---

## 4. Visual Simulation Technical Architecture & Dire Problem Solutions

When simulating reservoir drawdown under extreme drought, the mathematical model and UI must gracefully handle **strict dire conditions** without producing mathematical absurdities (negative storage, infinite loops, or phantom evaporation from dry mud).

```
   +-------------------------------------------------------------------------------+
   |                             Daily Rainfall Series                             |
   |              (Bundled NOAA Airport Stations OR Custom User Gauge CSV)         |
   +---------------------------------------+---------------------------------------+
                                           |
                                           v
   +-------------------------------------------------------------------------------+
   |                             Inflow Calculation                                |
   |     I(t) = Inflow_base + Runoff_sens * max(0, Precip(t) - Interception)       |
   |     Environmental Pass-Through Deduction (2001 Agreed Order vs 2026 50% Rule) |
   +---------------------------------------+---------------------------------------+
                                           |
                                           v
   +-------------------------------------------------------------------------------+
   |                   Elevation-Area-Capacity (EAC) Evaporation                   |
   |    Area(t) = Area_0 * (S(t) / S_cap)^0.65  |  E(t) = Pan_Evap(m) * Area(t)    |
   |    Actual_Evap = min(E(t), Total_Storage)                                     |
   +---------------------------------------+---------------------------------------+
                                           |
                                           v
   +-------------------------------------------------------------------------------+
   |                    Multi-Sector Priority Demand Curtailment                   |
   |   - Tier 1: Essential Domestic Baseload (Protected)                           |
   |   - Tier 2: Contracted Industrial Demand (DSEF Surcharge / Emergency Cuts)    |
   |   - Tier 3: Outdoor Irrigation (Curtailed: Stg 1 -15%, Stg 2 -50%, Stg 3 -100%)|
   |   Offset by: Mary Rhodes Pipeline Delivery (0 to 72 MGD)                      |
   +---------------------------------------+---------------------------------------+
                                           |
                                           v
   +-------------------------------------------------------------------------------+
   |                   Mass Balance Storage Update & Invariants                    |
   |        S(t) = clip(S(t-1) + I(t) - Evap(t) - Served_Demand(t), 0, Cap)       |
   |        Spill(t) = max(0, S_raw(t) - Cap)                                      |
   |        Invariant: Balance Error == 0.0 ac-ft on EVERY daily time step         |
   +---------------------------------------+---------------------------------------+
                                           |
                                           v
   +-------------------------------------------------------------------------------+
   |                             Dire Crisis Detectors                             |
   |   - Stage 1 (40%), Stage 2 (30%), Stage 3 (20%), Stage 4 (10%) Threshold Days |
   |   - Assumed inactive-storage floor (preset: 75,000 ac-ft)                     |
   |   - Modeled active-storage exhaustion / unmet demand                          |
   |   - Runaway Acceleration Factor (Days lost under Pipeline Outage)             |
   +-------------------------------------------------------------------------------+
```

### 4.1. Assumed inactive-storage floor and unmet demand
- **Model assumption:** The optional preset treats 75,000 ac-ft as inactive storage. No reviewed source in this integration establishes that value as the point where gravity head, sediment or pumps cause delivery failure.
- **Model Implementation:**
  ```python
  DEAD_STORAGE_THRESHOLD_ACFT = 75000.0  # TWDB Region N Variance Reserve
  active_storage = max(0.0, total_storage - DEAD_STORAGE_THRESHOLD_ACFT)
  deliverable_water = min(active_storage, requested_demand)
  unmet_demand = requested_demand - deliverable_water
  ```
- **Automated handling:** When modeled storage reaches the assumed inactive floor, the experiment stops withdrawals and tracks unmet acre-feet. The UI describes this as a modeled active-storage limit.

### 4.2. Solution to Dire Problem 2: Multi-Sector Hierarchical Curtailment
- **Model assumption:** The preset divides demand into domestic, industrial and outdoor categories and applies a hypothetical priority schedule. The shares and reductions are not observed deliveries or adopted allocations.
- **Model Implementation:**
  ```python
  # Split base demand (370 ac-ft/day net of pipeline)
  demand_domestic = 150.0   # Essential indoor municipal (40%)
  demand_industrial = 185.0 # Contracted industrial baseload (50%)
  demand_outdoor = 35.0     # Outdoor lawn / aesthetic (10%)

  # Dynamic Stage Rules:
  if storage_pct <= 10.0:   # Illustrative band 4
      curtailed_outdoor = 0.0
      curtailed_industrial = demand_industrial * 0.70  # 30% cut
      curtailed_domestic = demand_domestic * 0.80      # 20% cut
  elif storage_pct <= 20.0: # Illustrative band 3
      curtailed_outdoor = 0.0                          # 100% ban
      curtailed_industrial = demand_industrial         # Protected by DSEF
      curtailed_domestic = demand_domestic * 0.90      # Voluntary savings
  elif storage_pct <= 30.0: # Illustrative band 2
      curtailed_outdoor = demand_outdoor * 0.50        # 1 day every 2 weeks
      curtailed_industrial = demand_industrial
      curtailed_domestic = demand_domestic
  elif storage_pct <= 40.0: # Illustrative band 1
      curtailed_outdoor = demand_outdoor * 0.85        # 1 day per week
      curtailed_industrial = demand_industrial
      curtailed_domestic = demand_domestic
  ```
- **Automated handling:** Displays modeled delivery by category under the preset schedule. It does not prove an operational outcome.

### 4.3. Solution to Dire Problem 3: Mary Rhodes Pipeline Outage Shock
- **Model assumption:** Pipeline availability selects between configured total-demand cases of 370 and 554 ac-ft/day. The 72 MGD field is context metadata and is not the arithmetic basis of that difference.
- **Model Implementation:**
  ```python
  requested_demand = 370.0 if pipeline_active else 554.0
  ```
- **Automated handling:** Compares the two configured demand cases and reports differences in reaching illustrative bands. It does not simulate pipeline hydraulics, outage probability or actual deliveries.

### 4.4. Solution to Dire Problem 4: Dynamic Surface-Area Evaporation (EAC Scaling)
- **Physical Reality:** Fixed evaporation rates over-penalize near-empty reservoirs. As lakes contract, surface area drops.
- **Model Implementation:**
  Using the Texas Water Development Board Elevation-Area-Capacity power curve for shallow dendritic reservoirs:
  $$\text{Area}(t) = \text{Area}_{\text{full}} \times \left(\frac{S(t)}{S_{\text{full}}}\right)^{0.65}$$
  $$\text{Evaporation}_{\text{actual}}(t) = \min\left(S(t), \text{Evaporation}_{\text{pot}}(t) \times \left(\frac{S(t)}{S_{\text{full}}}\right)^{0.65}\right)$$
- **Automated Handling:** Pre-built into the simulation loop with an automatic fall-through to preserve 100% numerical mass conservation without division-by-zero.

### 4.5. Solution to Dire Problem 5: Universal Ingestion of Custom User CSVs
- **Physical Reality:** Users may upload a CSV containing:
  - 365 days of 0.0 mm rainfall (extreme stress test)
  - Flash-flood spikes (e.g. 300 mm in 24 hours)
  - Missing dates, trailing NaNs, or negative numbers
- **Guardrail Implementation:**
  1. *Sanitization:* Enforces `np.clip(values, 0.0, 1000.0)` and verifies full contiguous daily DatetimeIndex.
  2. *Spill Conservation:* When a 300 mm deluge occurs, storage fills to capacity, and the remainder is explicitly accounted for as `spill_acft` (which feeds downstream bay freshwater targets).
  3. *Mass Conservation Check:*
     $$\text{Error}(t) = S(t) - \left(S(t-1) + I(t) - E_{\text{actual}}(t) - \text{Served}(t) - \text{Spill}(t)\right) \equiv 0.0$$
     If $|\text{Error}(t)| > 10^{-6}$ ac-ft, the run is rejected by assertion.

---

## 5. Implementation & UI Visualization Blueprint

1. **Preset Parameterization (`basin_core/water_system.py`):**
   - Refine `REGION_N_PRESET` with exact post-2015 capacities:
     - Lake Corpus Christi: 256,339 ac-ft (TWDB 2016 survey)
     - Choke Canyon Reservoir: 663,400 ac-ft
     - Total: 919,739 ac-ft (or 919,460 ac-ft)
   - Add `dead_storage_acft = 75000.0` (TWDB 2024 Hydrologic Variance Reserve).
   - Add `stage_bands_pct = (0.40, 0.30, 0.20, 0.10)` with an illustrative fourth band at 10%.
   - Add Mary Rhodes Pipeline delivery parameters: 72 MGD (221 ac-ft/day) modern, 45 MGD legacy.
   - Add Brackish Groundwater RO parameter: 21.3 MGD (phased 2027–2028).
2. **Simulation Logic Hardening (`basin_core/analysis.py`):**
   - Implement dead storage protection and Day Zero flagging.
   - Implement multi-sector demand tracking (Domestic, Industrial, Outdoor).
   - Implement TCEQ Emergency Inflow 50% threshold logic.
   - Assert mass conservation $|\text{Error}| < 10^{-6}$ on every time step.
3. **Interactive Visual UI (`app.py`):**
   - Multi-tier drawdown trajectory chart:
     - Storage curve with Stage 1 (40%), Stage 2 (30%), Stage 3 (20%), Stage 4 (10%), and Dead Storage (75k ac-ft / 8.2%) guide lines.
     - Context marker: 7.8%, matching the City's reported April 16, 2026 combined value.
     - Day Zero alert badge when active storage breaches zero.
   - Sector delivery breakdown stacked bar chart: Domestic vs. Industrial vs. Outdoor served vs. curtailed.
   - Pipeline availability comparison: compare the configured 370 and 554 ac-ft/day demand cases and report illustrative-band timing differences.
   - Estuary pass-through card: show the placeholder formula and modeled volume separately from the dated regulatory context.
