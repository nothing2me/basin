# Post-2015 Corpus Christi Hydrology & Advanced Visual Simulation Architecture

**Authoritative Research, Regulatory Fact-Base, and Implementation Blueprint for BASIN**  
*Date: September 2026 | Baseline Repository: `basin-latest`*

---

## 1. Executive Summary & Problem Framing

The City of Corpus Christi and the 11-county Coastal Bend Regional Water Planning Area (**Region N**) face a severe hydrologic and institutional disconnect:
1. **The 2015 Planning Void:** The primary regulatory water planning instrument for Region N—the **Corpus Christi Water Supply Model (CCWSM)**, developed using the Texas Water Availability Modeling (WAM) framework—**stops its hydrologic calibration at 2015**. In January 2024, the Texas Water Development Board (TWDB) granted Region N a formal **hydrologic variance** allowing the 2026 Regional Water Plan to evaluate surface water supplies using this pre-2015 dataset and an assumed 75,000 acre-foot "safe yield" reserve, explicitly because **there was insufficient state and regional funding to extend the model through current conditions**.
2. **The Unmodeled 2020–2026 Drought Reality:** Because official planning was frozen at 2015, the model treats the 2007–2013 drought as the baseline "Drought of Record" (DOR). In reality, the region endured an **exceptional drought from 2020 to 2026** that was longer, drier, and hotter. By **mid-April 2026**, combined storage of the two western reservoirs (**Choke Canyon Reservoir** and **Lake Corpus Christi**) dropped to an unprecedented **7.7% of conservation capacity (~70,800 ac-ft)**, breaching the 75,000 ac-ft inactive reserve. Corpus Christi was trapped under **Stage 3 Critical Drought Restrictions for nearly 20 consecutive months** (mid-December 2024 to August 2026).
3. **Financial, Political, and Regulatory Fallouts:**
   - On **May 20, 2026**, S&P Global Ratings revised Corpus Christi's debt rating outlook to **Negative**, citing depleted water reserves and delayed infrastructure execution.
   - Texas Governor Greg Abbott publicly raised the prospect of a **state takeover** of the city's water governance.
   - On **August 19, 2026**, Texas 2036 published a landmark evaluation (*The State Water Plan & The Coastal Bend Water Crisis* by Jeremy Mazur) revealing that across 25 years and five planning cycles, **neither the state water plan nor Region N plans projected any municipal water shortage in the 2020s**.
4. **The Industrial Baseload Reality:** Heavy industrial buildouts in San Patricio and Nueces counties (Gulf Coast Growth Ventures / Exxon-SABIC, Cheniere LNG, Steel Dynamics) consume **over 50% of the regional potable water supply**. The City established the **Drought Surcharge Exemption Fee (DSEF)**, allowing industrial facilities to pay alternative compliance fees to fund long-term water supplies rather than curtail cooling water, while residential households faced strict sprinkler bans and steep surcharges ($4–$8/kGal).
5. **The Need for BASIN Visual Simulation:** BASIN fills this institutional void. By enabling transparent, community-driven "what-if" simulations combining recent post-2015 climate data, custom user-uploaded gauge records, and configurable infrastructure shocks (pipeline bottlenecks, evaporation spikes, Stage 1–4 curtailments, dead storage limits), BASIN empowers regional planners and local stakeholders to model dire, strict hydrologic conditions with mathematical rigor and zero proprietary black-box dependencies.

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
| **Stage 4 (Emergency)** | **< 10%** (or physical delivery failure) | City Council action | **Level 1 Water Emergency**. Complete ban on non-essential water; mandatory 25%+ curtailments; residential/commercial surcharges ($4.00/kGal over baseline, $8.00/kGal over secondary tier). |

### 2.2. The 2024–2026 Drought Timeline & Mid-April 2026 Low
- **Mid-December 2024:** Western reservoir combined storage dipped below 20%, officially triggering **Stage 3 Critical Drought Restrictions**.
- **Mid-April 2026 (Historic Low):** Combined storage reached an all-time low of **7.7% (~70,800 ac-ft)**. This was lower than the 75,000 ac-ft safe-yield inactive pool reserved for worst-case drought scenarios.
- **May 20, 2026:** S&P Global Ratings placed Corpus Christi's debt on Negative outlook.
- **August 4, 2026:** Heavy tropical moisture in the Nueces and Frio river basins lifted storage above 30%, easing restrictions to **Stage 2**.
- **August 27, 2026:** Continued runoff lifted storage above 40%, easing restrictions to **Stage 1** (1-day/week watering).
- **September 10, 2026 Status (Extreme Asymmetry):**
  - **Lake Corpus Christi:** **87.1% full** (~223,000 ac-ft)
  - **Choke Canyon Reservoir:** **22.9% full** (~151,900 ac-ft)
  - **Combined Storage:** **47.6% full** (~374,900 ac-ft)
  - *Hydrologic Insight:* Lake Corpus Christi catches downstream Nueces runoff rapidly due to smaller capacity and responsive catchment, whereas Choke Canyon (on the Frio/Atascosa sub-basin) experiences severe upstream interception from thousands of private stock ponds, brush cover, and Carrizo-Wilcox aquifer recharge.

### 2.3. The Mary Rhodes Pipeline (MRP) — Regional Lifeline
To offset western reservoir vulnerability, Corpus Christi imports water from eastern river basins:
- **Lake Texana (Phase 1):** Firm "take-or-pay" contract for **31,440 acre-feet per year** (LNRA), plus supplemental interruptible water (4,500 to 11,000 ac-ft/yr).
- **Colorado River / Garwood Rights (Phase 2):** High-priority senior agricultural water rights of **35,000 acre-feet per year** pumped from the Colorado River into Lake Texana.
- **March 2025 Pump Expansion:** Upgraded pipeline transmission capacity from ~45 MGD to **70–72 MGD (~221 ac-ft/day)**.
- **Drought Impact:** During the 2024–2026 crisis, the Mary Rhodes Pipeline delivered **~70% of the entire region's daily drinking and industrial water**, preventing complete Day Zero dry-pipe collapse.

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

### 2.5. Environmental Inflows: TCEQ Emergency Order of September 9, 2026
The reservoir system is legally bound by the **2001 Agreed Order** to release freshwater to Nueces Bay:
- **2001 Agreed Order Baseline:** Mandates monthly pass-through releases when combined storage is $> 30\%$, scaling up to 138,000 ac-ft/yr when storage is $\ge 70\%$. Below 30%, pass-through is suspended.
- **TCEQ Emergency Order (September 9, 2026):**
  - TCEQ commissioners unanimously affirmed an emergency order **raising the pass-through suspension threshold from 30% to 50% combined storage**.
  - Effective for **120 days through December 23, 2026**.
  - Contains an **automatic 60-day extension** through late February 2027 if combined storage remains $\le 50\%$ on December 23.
  - Allows the City, Nueces River Authority, and Three Rivers to impound 100% of inflows, saving an estimated **2.4 billion gallons** (~7,360 ac-ft) in municipal storage.

### 2.6. Evaporation Science: TWDB On-Lake Buoys vs. Terrestrial Pan Evaporation
- TWDB deployed **NexSens CB-650 floating meteorological buoys** on Choke Canyon Reservoir to collect real-time water surface temperature, wind speed, solar radiation, and humidity.
- Demonstrates that terrestrial Class A evaporation pans overestimate winter reservoir evaporation and misjudge peak summer thermal lag compared to aerodynamic energy-balance methods.

### 2.7. The "First American City to Run Out of Water" Phenomenon: National Media, City Rebuttal, and the Fair Water Ballot Battle

During the spring and summer of 2026, the City of Corpus Christi became the focal point of national media coverage framing it as being on track to become **"the first city in America to run out of water"** (or America's first modern "Day Zero" metropolis). The escalation of this narrative, the municipal administration's formal pushback, and the ensuing political showdown over water equity represent a case study in modern municipal water risk.

#### 2.7.1. National Media Framing & The "Day Zero" Countdown
- **Media Outlets & Projections:** Extensive investigative reports by *Inside Climate News* (Dylan Baddour), *The Texas Tribune*, *Deceleration News* (Gaige Davila, *"The Corpus Christi Water Countdown to 'Day Zero'"*), *Circle of Blue*, and *Futurism* reported throughout early 2026 that the city was hurtling toward complete reservoir depletion. Parallels were drawn internationally to Cape Town, South Africa’s 2018 Day Zero crisis and recent municipal crises in Johannesburg.
- **The 7.7% Historic Low & Safe-Yield Breach:** In **mid-April 2026**, combined storage in Lake Corpus Christi and Choke Canyon Reservoir dropped to an all-time record low of **7.7% of conservation capacity (~70,800 ac-ft)**. This volume fell below the 75,000 ac-ft inactive safe-yield pool historically reserved by hydrologists as an emergency cushion for dead pool sedimentation and intake gravity loss.
- **Wholesale Emergency Declarations:** The crisis rippled across the 7-county service region. Neighboring wholesale municipal customers who purchase treated water from Corpus Christi—including the San Patricio Municipal Water District, the City of Alice, Port Aransas, Ingleside, Portland, and Rockport—declared local drought emergencies.
- **The `corpusdayzero.com` Watchdog:** Independent civic technologists launched `corpusdayzero.com`, an open-access monitoring platform aggregating real-time USGS streamflow, TWDB reservoir gauges, and NOAA climate data. The tracker published a live countdown of "days remaining to dead pool," projecting that without substantial runoff, reservoir gravity intake failure could occur between **May and September 2026**.

#### 2.7.2. City Administration Pushback: The "Misinformation" Rebuttal
In March 2026 and across subsequent City Council briefings, Corpus Christi City Manager Peter Zanoni and the City Water Department issued formal press releases and public statements directly countering national headlines, categorizing claims that the city would "run out of water next year" as **untrue** and **misinformation**:
1. **The Mary Rhodes Pipeline (MRP) Firm Baseload:** The city’s central rebuttal is that Corpus Christi does not rely solely on the western reservoirs. The Mary Rhodes Pipeline delivers a continuous **70–72 MGD (~221 ac-ft/day)** from Lake Texana and high-priority senior Colorado River rights (Garwood rights) directly to the O.N. Stevens Water Treatment Plant. Because regional consumption averages ~100–110 MGD, the MRP meets approximately **70% of total regional demand**. Therefore, even if western reservoirs dropped to absolute dead pool (0 ac-ft usable), the city would retain a firm 72 MGD pipeline supply. While severe rationing would occur, residential taps would not run completely dry in a catastrophic "Day Zero" total delivery failure.
2. **Administrative Meaning of "Level 1 Water Emergency":** The city clarified that the anticipated "Level 1 Water Emergency" (formerly designated as Stage 4) is an administrative trigger initiated **180 days before total supply is projected to be insufficient to meet demand**. Triggering Level 1 is a statutory protocol designed to enforce maximum conservation and activate emergency powers six months in advance, not a declaration that taps have run dry.
3. **$1.1 Billion Drought-Proof Capital Program:** The city underscored its active capital execution to deliver 66 MGD of diversified supplies, notably the **$175M Brackish Groundwater RO Plant at ONSWTP** (21.3 MGD phased from Feb 2027 to March 2028), the Evangeline and ERF well fields, and wastewater reclamation for industrial cooling.

#### 2.7.3. The Equity Conflict: The Drought Surcharge Exemption Fee (DSEF)
Despite official reassurances, public frustration reached an inflection point over the issue of **water equity and industrial allocation**:
- **Industrial Consumption Volume:** Heavy industrial facilities—including petrochemical complexes (Gulf Coast Growth Ventures / ExxonMobil-SABIC, consuming up to 20 MGD), liquefied natural gas export terminals (Cheniere Energy), steel mills (Steel Dynamics), and refineries (Valero, Citgo, LyondellBasell, and Flint Hills Resources)—consume **over 50% of the potable water produced by Corpus Christi**.
- **The DSEF Exemption (2018):** Under city ordinance, large industrial customers were permitted to enroll in the **Drought Surcharge Exemption Fee (DSEF)**. By paying a fee of **$0.31 per 1,000 gallons ($0.31/kGal)** into a restricted city fund (generating ~$6 million annually for future water projects like desalination), industrial facilities were **exempted from drought surcharges** and shielded from mandatory volumetric production curtailments during drought stages.
- **Residential Disparity:** In stark contrast, residential households and small businesses were subjected to **nearly 20 consecutive months of Stage 3 Critical Drought Restrictions** (mid-December 2024 to August 2026). Residents faced complete bans on lawn watering with sprinklers, strict hand-watering limits, and punitive drought surcharges ranging from **$4.00 to $8.00 per 1,000 gallons** for water used beyond baseline thresholds.
- **Statutory Tension (Wagstaff Act):** Under the Texas Wagstaff Act (*Tex. Water Code § 11.024*), domestic and municipal uses hold statutory priority over manufacturing and industrial uses. However, because Corpus Christi itself holds the senior municipal water rights and delivers water to industrial clients via utility contracts, the City treated industrial supply as a protected economic contract rather than exercising municipal priority to curtail industrial cooling water.

#### 2.7.4. The Citizen Revolt: The Fair Water Charter Amendment (November 3, 2026 Ballot)
- **Petition Drive:** A grassroots coalition organized by *For the Greater Good*, *Texas Campaign for the Environment*, and community advocates collected nearly **13,000 certified signatures** to amend the Corpus Christi City Charter.
- **City Council 6–2 Vote (August 11, 2026):** After intense municipal debates over whether the amendment could be blocked under state statutes restricting climate-related charter initiatives, the Corpus Christi City Council voted **6–2** on August 11, 2026, to formally place the **Fair Water Amendment** on the **November 3, 2026 general election ballot**.
- **Core Provisions of the Fair Water Amendment:**
  1. *Abolish Surcharge Exemptions:* Prohibits any program (including DSEF) that allows large industrial water users to pay a fee to bypass drought surcharges.
  2. *Mandate Surcharges on Industry:* Requires large industrial users to pay drought surcharges at parity with established council rates.
  3. *Enforce Mandatory Curtailment:* Mandates that large industrial facilities comply with all drought conservation, allocation, and curtailment schedules in the City's Drought Contingency Plan.
  4. *Wholesale Parity:* Extends identical drought curtailment and surcharge mandates to wholesale utility customers (e.g., San Patricio MWD).

#### 2.7.5. Institutional Critique: The Texas 2036 Report (August 19, 2026)
On August 19, 2026, policy think-tank Texas 2036 published a foundational assessment authored by Jeremy Mazur: *The State Water Plan & The Coastal Bend Water Crisis*:
- **25 Years of Unseen Crisis:** Across five consecutive state water planning cycles (2002, 2007, 2012, 2017, and 2022), **neither the Texas State Water Plan nor Region N regional plans ever projected a municipal water shortage in the 2020s**.
- **Root Causes:**
  - *Statutory Prohibition:* Texas Water Availability Models (WAM) are legally prohibited from incorporating climate change projections or rising temperature-driven evaporation rates.
  - *2015 Planning Freeze:* TWDB granted Region N a formal hydrologic variance freezing surface water data at 2015 due to funding shortages, blinding planners to the true severity of the 2020–2026 drought.
  - *Recommendations:* Texas 2036 urged state water planners to adopt plausible stress-testing scenarios that model droughts worse than the historical Drought of Record and dynamically evaluate infrastructure delay risks.

#### 2.7.6. September 2026 Reprieve vs. The Persistent Day Zero Trajectory
- **Temporary Breathing Room:** Runoff from late-summer storms in August and September 2026 filled Lake Corpus Christi to ~87–90%, lifting combined storage to **47.6%** and prompting the City to ease restrictions from Stage 3 to Stage 1. City Manager Peter Zanoni announced that the projected date for a Level 1 Water Emergency had been pushed back to **September 2028**.
- **The Desalination Rejection:** However, on **September 1, 2026**, the Corpus Christi City Council voted **5–3 against** the $700M–$1B design-build contract for the 30 MGD Inner Harbor seawater desalination plant, citing runaway costs and environmental justice concerns. As a result, no seawater desalination can be online before 2029–2031.
- **Structural Vulnerability:** Choke Canyon Reservoir remains severely depleted at **22.9%**. Because Lake Corpus Christi has a smaller capacity and high evaporative loss, any return to persistent hot, dry weather will rapidly drain the system back below 20% (Stage 3) and toward the 7.7% record low.
- **The Role of BASIN:** BASIN bridges this planning gap by providing an open, reproducible workbench where operators and citizens can simulate the Fair Water Amendment policy (curtailing industrial baseload during Stage 4), test Mary Rhodes Pipeline shock scenarios, and analyze true multi-sector drawdown without regulatory blind spots.

---

## 3. Gap Analysis: Repository Knowledge vs. Newly Integrated Findings

| Hydrologic Dimension | Previous Codebase Baseline | Newly Discovered Official Reality | Integration into BASIN Simulation |
|---|---|---|---|
| **Model Horizon** | Frozen at **2015** (`docs/methodology.md`). | **2020–2026 Drought of Record** occurred; TWDB hydrologic variance granted due to budget shortfall. | Benchmark against true modern drought; document 2020–2026 conditions in scenarios. |
| **Drought Severity Depth** | Minimum band was 15% (`stage_bands_pct = (0.4, 0.3, 0.2, 0.15)`). | System hit **7.7% in mid-April 2026**; Stage 3 endured for **20 continuous months**. | Add explicit **Stage 4 (10% Emergency)** and **Physical Dead Storage (75,000 ac-ft reserve)**. |
| **Credit & Governance** | Unmentioned. | S&P debt outlook downgraded to **Negative (May 20, 2026)**; Gov. Abbott threatened state takeover. | Provide risk-boundary analytics for municipal debt and governance thresholds. |
| **State Planning Critique** | Not documented. | **Texas 2036 Report (Aug 19, 2026)** by Jeremy Mazur exposed 25-year forecasting failure. | Integrate Texas 2036 recommendations (stress-testing beyond DOR, tracking execution milestones). |
| **Mary Rhodes Pipeline** | Fixed toggle (370 vs 554 ac-ft/day). | March 2025 upgrade reached **70–72 MGD (~221 ac-ft/day)**; carried 70% of municipal/industrial load. | Parameterize pipeline throughput: 0 MGD (outage), 45 MGD (legacy), 72 MGD (modern). |
| **Industrial vs Municipal Demand** | Lumped uniform demand. | Heavy industry consumes **>50% of supply**; Drought Surcharge Exemption Fee protects industrial cooling. | Split demand into Tier 1 (Municipal Essential), Tier 2 (Industrial Contracted), Tier 3 (Outdoor Irrigation). |
| **Estuary Environmental Inflows** | Fixed uncalibrated inflow coefficient. | 2001 Agreed Order and **TCEQ Sept 9, 2026 Emergency Order (50% threshold)** govern releases. | Add Estuary Pass-Through toggle: deducts monthly inflow targets when $>50\%$; captures 100% when $\le 50\%$. |
| **Desalination Reality** | Assumed future baseline. | Council voted 5–3 against contract on Sept 1, 2026; 21.3 MGD Brackish RO plant at ONSWTP is real near-term hedge (2027–2028). | Model zero seawater desal through 2029; add optional phased brackish groundwater toggle. |
| **Evaporative Scaling** | Step function (June–Sept vs Oct–May). | Dynamic power-law surface area shrinkage ($\text{Area} \propto S^{0.65}$) and TWDB buoy data. | Implement power-law EAC scaling and 12-month smooth pan evaporation curve. |
| **Day Zero & Fair Water Policy** | Unmodeled. | National media dubbed Corpus Christi "first city in America to run out of water"; City pushback (Level 1 = 180-day lead time, MRP = 70% supply); Fair Water Charter Amendment on Nov 3, 2026 ballot (Aug 11 Council 6–2 vote) to abolish DSEF. | Add Day Zero indicator, dead storage cutoff, and Fair Water policy simulation (industrial curtailment vs status-quo exemption). |

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
   |   - Physical Dead Storage Breach (TWDB 75k ac-ft Reserve)                     |
   |   - Day Zero (Active Storage == 0 ac-ft / Unmet Demand > 0)                   |
   |   - Runaway Acceleration Factor (Days lost under Pipeline Outage)             |
   +-------------------------------------------------------------------------------+
```

### 4.1. Solution to Dire Problem 1: Day Zero & Physical Dead Storage Protection
- **Physical Reality:** Below 10% combined capacity (~91,900 ac-ft) or the 75,000 ac-ft TWDB reserve, treatment plant gravity head fails, sedimentation blocks intakes, and pumps cavitate.
- **Model Implementation:**
  ```python
  DEAD_STORAGE_THRESHOLD_ACFT = 75000.0  # TWDB Region N Variance Reserve
  active_storage = max(0.0, total_storage - DEAD_STORAGE_THRESHOLD_ACFT)
  deliverable_water = min(active_storage, requested_demand)
  unmet_demand = requested_demand - deliverable_water
  ```
- **Automated Handling:** When storage enters the 75k ac-ft reserve, the simulation flags an immediate **"Day Zero: Intake Gravity Failure"** alert, ceases treating dead storage as consumable water, and tracks cumulative unmet acre-feet.

### 4.2. Solution to Dire Problem 2: Multi-Sector Hierarchical Curtailment
- **Physical Reality:** In a crisis, cutting outdoor lawn watering is painless, but cutting refinery cooling water halts fuel production.
- **Model Implementation:**
  ```python
  # Split base demand (370 ac-ft/day net of pipeline)
  demand_domestic = 150.0   # Essential indoor municipal (40%)
  demand_industrial = 185.0 # Contracted industrial baseload (50%)
  demand_outdoor = 35.0     # Outdoor lawn / aesthetic (10%)

  # Dynamic Stage Rules:
  if storage_pct < 10.0:    # Stage 4 Emergency
      curtailed_outdoor = 0.0
      curtailed_industrial = demand_industrial * 0.70  # 30% cut
      curtailed_domestic = demand_domestic * 0.80      # 20% cut
  elif storage_pct < 20.0:  # Stage 3 Critical
      curtailed_outdoor = 0.0                          # 100% ban
      curtailed_industrial = demand_industrial         # Protected by DSEF
      curtailed_domestic = demand_domestic * 0.90      # Voluntary savings
  elif storage_pct < 30.0:  # Stage 2 Moderate
      curtailed_outdoor = demand_outdoor * 0.50        # 1 day every 2 weeks
      curtailed_industrial = demand_industrial
      curtailed_domestic = demand_domestic
  elif storage_pct < 40.0:  # Stage 1 Mild
      curtailed_outdoor = demand_outdoor * 0.85        # 1 day per week
      curtailed_industrial = demand_industrial
      curtailed_domestic = demand_domestic
  ```
- **Automated Handling:** Works automatically with any user input. Displays sector-by-sector delivery breakdown and proves the exact survival delay achieved by each curtailment level.

### 4.3. Solution to Dire Problem 3: Mary Rhodes Pipeline Outage Shock
- **Physical Reality:** If the 72 MGD pipeline breaks or Colorado River senior rights are curtailed, western reservoirs must supply an extra **221 ac-ft/day**.
- **Model Implementation:**
  ```python
  pipeline_delivery_acft = 221.0 if pipeline_active else 0.0
  net_western_demand = max(0.0, total_regional_demand - pipeline_delivery_acft)
  ```
- **Automated Handling:** Compares the active pipeline run against an instantaneous "Pipeline Outage" counterfactual run. Generates the **"Pipeline Vulnerability Metric"**: the exact number of days sooner the region enters Stage 3, Stage 4, and Day Zero if the pipeline fails.

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
   - Add `stage_bands_pct = (0.40, 0.30, 0.20, 0.10)` including Stage 4 Emergency at 10%.
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
     - Record low marker: Mid-April 2026 (7.7% historic mark).
     - Day Zero alert badge when active storage breaches zero.
   - Sector delivery breakdown stacked bar chart: Domestic vs. Industrial vs. Outdoor served vs. curtailed.
   - Pipeline Outage Counterfactual: Overlay showing the drawdown curve if the Mary Rhodes Pipeline suffers a shock, reporting the exact number of days lost to Stage 3 and Day Zero.
   - Estuary Inflow Retention card: Showing acre-feet conserved under the TCEQ September 2026 50% emergency order.
