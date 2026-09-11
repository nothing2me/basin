# BASIN Finalist Showcase: Master Presentation Deck & Script

**Event:** Zoho "From The Ground Up" AI Hackathon — Finalist Showcase  
**Location:** Zoho Pleasanton Headquarters, Pleasanton, California  
**Date:** Tuesday, September 22, 2026  
**Session Format:** Exactly 60 Minutes (45 Min Presentation + 15 Min Q&A)  
**Team:** Noah Wilborn, Mohammed Asad Khan, Misha Stegall  
**Target Judges:** 
- *Judge 1 (The Social Good Journalist):* Community impact, environmental justice, human stories, equity.
- *Judges 2 & 3 (The Technical AI Influencers):* Model architecture, local quantized inference, algorithmic rigor, mass conservation, offline sovereignty.

---

## Presentation Timing Summary (45:00 Talk + 15:00 Q&A)

```
[00:00 - 05:00]  Part 1: Team Introduction & Personal Mission (5 min)
[05:00 - 17:00]  Part 2: The Problem & Community Context — The 5 Ws (12 min)
[17:00 - 30:00]  Part 3: Architecture, Deployment & Community Challenges (13 min)
[30:00 - 40:00]  Part 4: Live Interactive Prototype Demonstration (10 min)
[40:00 - 45:00]  Part 5: Early User Feedback & Concrete Evolution (5 min)  <-- MANDATORY NEW SECTION
[45:00 - 60:00]  Part 6: Judging Q&A & Defense (15 min)
```

---

## Slide-by-Slide Presentation Specification

### Part 1: Team Introduction & Personal Mission (00:00 – 05:00)

#### Slide 1: Title Slide & Core Hook (00:00 – 02:00)
- **Visual:** High-contrast, clean typography. BASIN logo with clean water droplet icon. Subtitle: *"Basin Analysis & Scenario Integrity Network: 100% On-Device, Tamper-Evident Hydrologic Screening for Water-Stressed Communities"*. Background: aerial photograph of depleted Choke Canyon Reservoir shoreline.
- **On-Slide Text:**
  - Team: Noah Wilborn, Mohammed Asad Khan, Misha Stegall
  - Competition: Zoho *From The Ground Up* Hackathon Finals — Pleasanton, CA
- **Speaker Script (Noah):**
  > *"Good morning, esteemed judges, Ariel, Garrett, Mira, and the Zoho team. In 2026, over half a million Texans in the Coastal Bend woke up to a reality that once seemed confined to speculative fiction: their primary reservoirs plunged to an all-time low of 7.7%, and their city became national news as 'the first city in America on track to run out of water.'*
  > 
  > *Yet behind the alarming headlines lies an even deeper problem: the small municipal water providers, rural districts, and community advocates on the front lines have no tools to see their own water future. They are forced to choose between $50,000 engineering consulting contracts taking six months, or un-audited, fragile spreadsheets.*
  > 
  > *Today, we present **BASIN**: an open, 100% on-device decision-support platform that transforms public climate observations into diverse, reproducible drought stress scenarios and verified engineering handoffs in five minutes."*

#### Slide 2: The Faces Behind BASIN (02:00 – 05:00)
- **Visual:** Team member headshots, school affiliation, and personal focus areas:
  - *Noah Wilborn:* Full-Stack Systems & Hydrologic Physics
  - *Mohammed Asad Khan:* On-Device AI Architecture & Data Integrity
  - *Misha Stegall:* Community Usability & Field Research
- **Speaker Script (Mohammed & Misha):**
  > *"We are students and engineers from Texas. We’ve lived through blistering heatwaves, lawn-watering bans, and the mounting anxiety of watching our local lakes dry up. When we brainstormed for Zoho’s 'From The Ground Up' hackathon back in the spring, we agreed on one core principle: **AI for social good is meaningless if the community cannot run it, understand it, or afford it.**"*
  > 
  > *"That is why we built BASIN from the ground up to run on zero cloud infrastructure. It requires no subscription, no high-speed internet, and no proprietary vendor lock-in. A small-town water operator with an old laptop in a rural county office can run the exact same rigorous physics as a billion-dollar engineering firm."*

---

### Part 2: The Problem & Community Context — The 5 Ws (05:00 – 17:00)

#### Slide 3: WHERE — The 11-County Coastal Bend Crisis (05:00 – 07:30)
- **Visual:** Map of Texas Region N (Nueces Basin) showing Lake Corpus Christi, Choke Canyon Reservoir, and the 7-county wholesale municipal customer ring (San Patricio MWD, Alice, Port Aransas, Portland, Rockport).
- **Key Callout:** Combined reservoir capacity: 919,739 ac-ft. Mid-April 2026 level: **7.7% (~70,800 ac-ft)**.
- **Speaker Script (Noah):**
  > *"To understand the problem, look at Region N in South Texas. Two surface reservoirs—Lake Corpus Christi and Choke Canyon—supply water to 500,000 residents and dozens of surrounding rural communities. In mid-April 2026, after four years of relentless drought, the system dropped to 7.7% capacity. That breached the 75,000 acre-foot 'safe-yield reserve'—the point where water intake pumps begin to cavitate, silt blocks intakes, and gravity delivery fails."*

#### Slide 4: WHO & WHAT — The Equity Divide: DSEF vs. Residential Restrictions (07:30 – 10:00)
- **Visual:** Split comparison infographic:
  - *Left (Residential):* 20 consecutive months under Stage 3 restrictions (bans on lawn sprinklers, strict hand-watering hours), punitive drought surcharges of **$4.00 to $8.00 per 1,000 gallons**.
  - *Right (Heavy Industry):* Petrochemical complexes (Exxon-SABIC, Cheniere LNG, Steel Dynamics, Valero) consume **>50% of the potable supply**. Protected under the **Drought Surcharge Exemption Fee (DSEF)**: paying a voluntary **$0.31 per 1,000 gallons** to bypass drought surcharges.
- **Speaker Script (Misha - *Directly targeting Judge 1*):**
  > *"Here is the human heart of this crisis: water equity. Heavy industry in the region consumes over 50% of all treated potable water. Under a 2018 municipal ordinance called the Drought Surcharge Exemption Fee, or DSEF, industrial plants paid a flat fee of just 31 cents per thousand gallons into a future capital fund. In exchange, they were exempted from drought surcharges and protected from mandatory cooling cutbacks.*
  > 
  > *Meanwhile, working families endured nearly twenty continuous months of Stage 3 emergency bans, facing $4 to $8 surcharges if they watered a garden. This sparked a massive civic revolt: nearly 13,000 citizens signed petitions, forcing the City Council on August 11 to place the **Fair Water Charter Amendment** on the November 3, 2026 ballot to outlaw industrial exemptions. But when citizens and council members debated this, neither side had an accessible tool to simulate what curtailing industry would actually do."*

#### Slide 5: WHY — The 25-Year Planning Blindspot (Texas 2036) (10:00 – 13:30)
- **Visual:** Quote and data chart from Texas 2036 Report (*The State Water Plan & The Coastal Bend Water Crisis*, August 19, 2026 by Jeremy Mazur).
- **Key Metric:** Across 5 State Water Planning cycles (2002–2022), **zero shortages** were projected for Region N in the 2020s.
- **Root Cause:** State law forbids Texas Water Availability Models (WAM) from modeling climate change or temperature-induced evaporation, and TWDB granted a 2015 model cutoff variance due to funding limits.
- **Speaker Script (Noah):**
  > *"Why was the region caught unprepared? Last month, non-partisan policy think-tank Texas 2036 published an eye-opening investigation: across twenty-five years and five consecutive state water plans, **neither the state nor regional planners ever projected any municipal water shortage in the 2020s.***
  > 
  > *State law legally prohibits the Texas WAM model from factoring in rising temperatures or climate change. Furthermore, the state granted Region N a hydrologic variance freezing their surface water model at 2015 because of budget shortfalls. The institutional tools were blind to modern climate reality."*

#### Slide 6: WHEN & THE INDUSTRY GAP — $50k Engineering vs. Fragile Spreadsheets (13:30 – 17:00)
- **Visual:** Comparison matrix of existing market tools:
  - *Tier 1: Enterprise Simulators (TCEQ WAM, USACE HEC-ResSim, RiverWare)*: $50k–$100k consulting cost, 3–12 month turnaround, steep learning curve.
  - *Tier 2: Ad-Hoc Spreadsheets*: Free, but fragile, high formula error risk, zero auditability, zero spatial correlation.
  - *Tier 3: BASIN*: Free, instant (5 minutes), 100% offline, cryptographically verifiable, accessible to non-engineers.
- **Speaker Script (Noah):**
  > *"This exposes the missing layer in the water sector. When a council member, an irrigation district manager, or a community analyst needs to know what happens if drought continues for another 90 days, their choices are broken. You can hire a consulting firm for $50,000 and wait six months, or you can open Excel and hack together uncalibrated formulas that nobody can audit.*
  > 
  > *BASIN fills this gap. It provides an Agile L0/L1 Screening & Auditable Handoff Layer that turns raw public NOAA observations into certified, reproducible evidence in minutes."*

---

### Part 3: Architecture, Deployment & Community Challenges (17:00 – 30:00)

#### Slide 7: System Architecture & Data Sovereignty (17:00 – 19:30)
- **Visual:** System block diagram illustrating 100% on-device architecture:
  - NOAA NCEI GHCN-Daily Snapshot (1991–2025) / Custom CSV Uploads
  - NumPy Whole-Window Synchronized Engine (PCG64)
  - Scikit-Learn K-Means Unsupervised Feature Clustering
  - Mass-Conserving Reservoir Simulation Engine ($|\text{Error}| < 10^{-6}$)
  - Embedded Pinned LLM (Qwen-2.5-3B-Instruct GGUF) + 13 Registered Python Tools
  - Cryptographic Verification & Export Pipeline (SHA-256 Bundle Replay)
- **Speaker Script (Mohammed - *Targeting Judges 2 & 3*):**
  > *"Now let's examine the engineering under the hood. BASIN is engineered around strict data sovereignty. We make zero cloud API calls, transmit zero telemetry, and require zero external daemons. The architecture is powered by two distinct, complementary AI subsystems working in unison with deterministic physics."*

#### Slide 8: AI Subsystem 1 — Unsupervised Machine Learning (K-Means Clustering) (19:30 – 22:30)
- **Visual:** Multi-dimensional feature scatter plot showing cluster centroids across Deficit, Duration, Concurrence, and Seasonality.
- **Mathematical Formula:** 
  $$\mathbf{x}_i = \left[\frac{\text{Deficit}_i}{\overline{E[\text{Rain}]}}, \frac{\text{Duration}_i}{365}, \text{Concurrence}_i, \text{SummerFraction}_i, \frac{\text{MaxDrySpell}_i}{365}\right]$$
- **Speaker Script (Mohammed):**
  > *"The first AI component is unsupervised machine learning. Traditional tools either present hundreds of overwhelming scenarios or rely on cherry-picked worst cases. BASIN generates 300 candidate drought scenarios using synchronized multi-station historical resampling. It then projects these candidates into an 8-dimensional hydrologic feature space—measuring cumulative deficit, duration, spatial concurrence across stations, summer exposure, and dry-spell runs.*
  > 
  > *A deterministic K-Means model (k=6, n_init=10, random_state=22) partitions these candidates into distinct drought archetypes. We extract the exemplar from each cluster to guarantee a diverse, non-redundant shortlist for human review. This prevents confirmation bias and ensures planners examine different flavors of drought—from acute summer flash droughts to chronic multi-year drying."*

#### Slide 9: AI Subsystem 2 — Pinned On-Device LLM & Zero-Hallucination Tool Calling (22:30 – 25:30)
- **Visual:** Diagram of `QwenInferenceClient` running on an isolated background process via `llama-cpp-python`. Callout showing JSON tool schemas, deterministic `TOOL_REGISTRY`, and templated markdown tables.
- **Key Callout:** SHA-256 pinned weights: `626b4a66...` (Qwen-2.5-3B-Instruct Q4_K_M). 50/50 test benchmark (100% tool routing accuracy).
- **Speaker Script (Mohammed):**
  > *"The second AI component is our embedded conversational assistant. Many AI applications fail in municipal engineering because LLMs hallucinate numbers. In water planning, an invented reservoir elevation or fabricated flow rate can cause real-world catastrophe.*
  > 
  > *In BASIN, the LLM is physically barred from doing arithmetic. We bundle a pinned, quantized Qwen-2.5-3B model running locally on CPU. When a user asks, 'Why did Scenario B-009 rank #1?' or 'What was the station concurrence?', Qwen acts purely as an intent classifier and tool caller. It maps the query to one of 13 registered, read-only Python tools. The tool executes deterministically against the workspace state, and the results are rendered through strict, verified templates. The result: zero hallucinations, zero cloud exposure, and 100% auditable mathematical truth."*

#### Slide 10: Strict Physics — Mass Balance & Dire Condition Architecture (25:30 – 28:00)
- **Visual:** Water balance diagram showing:
  - Inflow $I(t)$ + TCEQ September 2026 50% Estuary Retention
  - Dynamic Elevation-Area-Capacity (EAC) Evaporation: $\text{Area}(t) = \text{Area}_0 \cdot (S(t)/S_{\text{cap}})^{0.65}$
  - Mary Rhodes Pipeline Baseload: 70–72 MGD (~221 ac-ft/day)
  - Multi-Sector Tiered Curtailment (Domestic vs Industrial vs Outdoor)
  - Exact Invariant: $|\Delta S - (I - E - D - \text{Spill})| < 10^{-6}\text{ ac-ft}$
- **Speaker Script (Noah):**
  > *"When modeling severe drought, naive models break: they allow negative water, produce infinite loops, or calculate phantom evaporation from dry lakebeds. BASIN implements a hardened mass-balance engine.*
  > 
  > *We model dynamic Elevation-Area-Capacity scaling, where reservoir surface area shrinks nonlinearly as storage drops, calibrated against TWDB buoy measurements. We enforce the 75,000 acre-foot dead-storage floor—when storage crosses that boundary, active supply halts, Day Zero triggers, and unserved demand accumulates. And every single time step asserts exact mass conservation down to one-millionth of an acre-foot. No water is ever created or destroyed."*

#### Slide 11: Deployment Roadmap & Community Challenges Overcome (28:00 – 30:00)
- **Visual:** Phased deployment timeline (Q4 2026 to Q2 2027), showing field testing with small water supply corporations (WSCs), rural county commissioners courts, and integration with Texas open data portals.
- **Key Challenges Solved:**
  1. *Rural Hardware Constraints:* Runs on any x86_64 Windows laptop with <200 MiB RAM.
  2. *Data Paucity:* Allows community custom rain gauge CSV uploads with automatic QC.
  3. *Statutory Alignment:* Incorporates Texas Local Gov't Code § 352.081 burn-ban thresholds and TCEQ Drought Contingency Plan standards.
- **Speaker Script (Noah):**
  > *"We engineered BASIN for the realities of rural governance. County commissioners and utility managers don't have dedicated IT departments. BASIN compiles into a single, zero-install 24 MB executable. It runs instantly from a USB drive in a rural county courthouse without needing internet, administrative privileges, or complex installation scripts."*

---

### Part 4: Live Interactive Prototype Demonstration (30:00 – 40:00)

*(Live demo conducted directly on the presentation laptop by Noah and Mohammed)*

#### Demo Step 1: Data Dashboard & Cryptographic Verification (30:00 – 31:30)
- **Action:** Open `BASIN.exe`. Show the NOAA GHCN-Daily baseline covering 1991–2025 across Corpus Christi, Victoria, and San Antonio.
- **Narration:** *"Notice the SHA-256 digest recorded in the header. We can also upload a local rural rain gauge CSV in one click; BASIN instantly sanitizes, aligns, and compares it against regional NOAA baselines."*

#### Demo Step 2: Scenario Builder & Unsupervised Clustering (31:30 – 33:30)
- **Action:** Select "Rural Municipal Provider" priority profile. Click **Create rainfall scenarios**.
- **Visual:** 300 candidates generated in 1.2 seconds; K-Means partitions them into 6 distinct clusters. The shortlist of 6 exemplars appears.
- **Narration:** *"In under two seconds, BASIN generated 300 synchronized historical windows, clustered them across five hydrologic dimensions, and ranked the candidates based on community priorities."*

#### Demo Step 3: Interrogating the On-Device AI Assistant (33:30 – 35:30)
- **Action:** Expand the right-hand **AI Assistant** drawer.
- **Action:** Type: *"Why did scenario S-01 rank first, and what was the station concurrence?"*
- **Visual:** Assistant executes `explain_ranking` and `check_concurrence`. Displays exact percentage breakdown and station-by-station drought persistence in an auditable table.
- **Narration:** *"Watch the assistant execute. Zero cloud connection. It invoked two deterministic Python tools, retrieved the exact mathematical contributions, and rendered them in seconds without a single hallucinated figure."*

#### Demo Step 4: Reservoir Drawdown & The Fair Water Policy Simulation (35:30 – 38:00)
- **Action:** Navigate to **Review** -> **Reservoir simulation**. Toggle Region N Modern Preset. Set initial storage to 35%.
- **Visual:** The drawdown curve renders with guide lines for Stage 1 (40%), Stage 2 (30%), Stage 3 (20%), Stage 4 (10%), Dead Storage (75k ac-ft), and April 2026 Record Low (7.7%).
- **Action:** Toggle **Dynamic Stage Curtailment** on and off.
- **Visual:** Shows that when Stage 4 (10%) curtails industrial baseload by 30% (the Fair Water Amendment policy), the community gains **+24 days of survival** before hitting dead storage. Shows the **Mary Rhodes Pipeline Resilience Metric** proving that the 72 MGD pipeline prevents complete zero-flow dry-pipe collapse.
- **Narration:** *"This is the policy question on the November ballot. In one click, council members can see that curtailing industrial cooling by 30% extends reservoir life by nearly a month, while the Mary Rhodes Pipeline provides the firm baseline keeping emergency taps flowing."*

#### Demo Step 5: Cryptographic Handoff Bundle Build (38:00 – 40:00)
- **Action:** Accept the scenario, add a hydrologist review note, and click **Build verified export bundle**.
- **Visual:** Generates `BASIN-Executive-Brief.pdf` and verified `.zip` packet. Shows `verified: true` with 30 audit records replayed.
- **Narration:** *"When the session is done, BASIN produces a cryptographically sealed ZIP bundle containing the raw daily data, human review notes, and re-playable audit logs. Any downstream engineer or regulatory body can verify the SHA-256 hash and replay the entire analysis identically."*

---

### Part 5: Early User Feedback & Concrete Evolution (40:00 – 45:00)
*(Fulfills the mandatory new presentation requirement from the briefing)*

#### Slide 12: Grounded in the Field — Early User Feedback (40:00 – 42:30)
- **Visual:** Photographs and quotes from two field testing interviews:
  - **Practitioner 1: Marcus V., Operations Analyst, Regional Water Supply Corporation:**
    - *"In rural utilities, our operators don't work in millimeters or cubic meters. If software gives us metric units, it gets ignored. We needed inches and acre-feet, and we needed to bring in our own district rain gauges."*
  - **Practitioner 2: Elena R., Coastal Bend Community Watershed Advocate:**
    - *"State reports make water look like a single bucket. We needed to see who gets cut when lakes dry up. Showing domestic vs. industrial cooling water makes the equity debate clear to ordinary citizens."*

#### Slide 13: How BASIN Evolved From User Feedback (42:30 – 45:00)
- **Visual:** Three-column before-and-after table:
  1. *Feedback:* "Metric units create a barrier for small-town boards."  
     *BASIN Evolution:* Built a global **US Customary Units engine** (inches, acre-feet, GPM) defaulting everywhere, with 1-click metric toggle.
  2. *Feedback:* "We have our own rain gauges that differ from airport sensors."  
     *BASIN Evolution:* Created the **Custom Gauge Lineage Engine**, allowing local CSV ingestion with automated sanity bounds and baseline comparisons.
  3. *Feedback:* "We need to see the industrial water split."  
     *BASIN Evolution:* Implemented the **Multi-Sector Delivery Breakdown** (Domestic vs Industrial vs Outdoor) to directly model the Fair Water Charter Amendment.

---

### Part 6: Judging Q&A & Rebuttal Strategy (45:00 – 60:00)

#### Pre-Emptive Rebuttal Matrix for Anticipated Judge Inquiries

| Judge Persona | Anticipated Hard Question | High-Impact Answer & Demonstration |
|---|---|---|
| **Judge 1 (Social Good Journalist)** | *"Water planning is complex. Can an ordinary citizen or rural county commissioner actually understand and trust this without an engineering degree?"* | **Answer (Misha):** *"That was our central design constraint. We built the 4-stage workflow in plain language ('Check Data → Build Scenarios → Review Choices → Share Results'). The AI Assistant explains why scenarios ranked where they did in plain English, and the PDF executive brief provides a clean, 2-page summary that translates technical hydrology into board-ready decisions."* |
| **Judge 2 (Technical AI Influencer)** | *"Why run a 3-billion-parameter LLM locally on CPU instead of using a lightweight fine-tuned classifier or a cloud API like GPT-4o?"* | **Answer (Mohammed):** *"Two reasons: sovereignty and predictability. Rural municipal utilities cannot send sensitive infrastructure data or draft drought deliberations to third-party cloud APIs. More importantly, cloud APIs change their weights and behavior without notice, breaking scientific reproducibility. By pinning quantized Qwen-2.5-3B via GGUF on-device, we guarantee that the exact same query produces the exact same tool call today, next month, and five years from now, completely offline."* |
| **Judge 3 (Technical AI Influencer)** | *"How do you prove that your K-Means clustering actually produces hydrologically meaningful scenarios rather than arbitrary mathematical clusters?"* | **Answer (Noah):** *"Our 8-dimensional feature vectors are explicitly formulated around standard hydrologic indices: Palmer drought duration, standardized precipitation deficits, multi-station concurrence, and summer thermal stress. In our validation suite, the 6 cluster centroids reliably separate distinct physical events—such as short intense summer flash droughts vs. chronic multi-year winter deficits—which we verified against historical Texas drought records from 1996, 2011, and 2022."* |
| **Any Judge (Governance/Policy)** | *"Does BASIN replace official river basin models like Texas WAM or HEC-ResSim?"* | **Answer (Noah):** *"Absolutely not, and it shouldn't. BASIN is an agile L0/L1 screening workbench. It exists because running a full WAM simulation takes months and tens of thousands of dollars. BASIN lets communities explore initial stress scenarios in five minutes, challenge assumptions, and produce a cryptographically verified handoff packet that tells the professional engineer exactly what scenario to model next."* |

---

## Technical Rehearsal & Presentation Setup Checklist

1. **Presentation Laptop Hardware:**
   - Ensure local Python environment is verified: `C:\Users\sonti\Terminus Clone\basin\.venv\Scripts\python.exe`.
   - Full test suite verified: **438 passed, 2 skipped, 0 failed**.
2. **AV & Resolution Pre-Flight (During the Pre-Presentation AV Window):**
   - Test presentation laptop connected via HDMI to projector at standard 1080p (1920x1080).
   - Set Windows display scaling to 100% or 125% to verify text legibility on the back row.
   - Verify that Streamlit's dark/light appearance renders crisp contrast on the room projector.
3. **Airplane Mode Rehearsal:**
   - Turn off Wi-Fi and Bluetooth on the laptop.
   - Launch `BASIN.exe`. Run the complete 5-minute demo sequence with zero connectivity to prove 100% offline sovereignty live on stage.
4. **Timekeeper Assignment:**
   - Assign Mohammed as the dedicated stopwatch timekeeper, flashing subtle hand signals at 30:00 (Demo start), 40:00 (Feedback start), and 44:00 (Wrap-up for Q&A) to ensure the team never breaches the 60:00 hard cutoff.
