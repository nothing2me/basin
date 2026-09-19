# BASIN: Basin Analysis & Scenario Intelligence Navigator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2064--bit-0078D6.svg?logo=windows&logoColor=white)](https://github.com/nothing2me/basin/releases)
[![Execution: 100% Offline](https://img.shields.io/badge/Execution-100%25%20Offline-10B981.svg)](https://nothing2me.github.io/basin/)
[![Competition: Finalist](https://img.shields.io/badge/Zoho%20Hackathon-Finalist%202026-F59E0B.svg)](https://nothing2me.github.io/basin/)

> **Transparent, On-Device Hydrologic Screening and Drought Scenario Intelligence for Regional Water Authorities, Municipalities, and River Basins.**

🌐 **Official Showcase Website & Technical Documentation:** [https://nothing2me.github.io/basin/](https://nothing2me.github.io/basin/)

---

## 📑 Table of Contents

- [Why BASIN? (Regional Context)](#-why-basin-regional-context)
- [Quick Start: 1-Click Desktop Installer](#-quick-start-1-click-desktop-installer-recommended)
- [Developer & Hydrologist CLI Setup](#-developer--hydrologist-cli-setup)
- [Architecture & Analytical Pipeline](#-architecture--analytical-pipeline)
- [Core Capabilities](#️-core-capabilities)
- [Repository Structure](#-repository-structure)
- [Verification & Test Suite](#-verification--test-suite)
- [Data Provenance & Citations](#-data-provenance--citations)
- [Team Attribution](#-team-attribution)
- [License & Engineering Disclaimer](#-license--engineering-disclaimer)

---

## 🌊 Why BASIN? (Regional Context)

In mid-April 2026, the primary surface water reservoirs supplying approximately 500,000 residents and heavy industry across the Texas Coastal Bend (Region N)—**Lake Corpus Christi** and **Choke Canyon Reservoir**—fell to an all-time historical low of **7.7% combined capacity**. This brought the reservoir system near its 75,000 acre-foot dead-storage threshold, the physical level where intake pumps cavitate, silt intrusion threatens water quality, and gravity conveyance fails.

While substantial summer rainfall partially replenished the basin to **~39.9% combined capacity** by mid-September 2026 (Lake Corpus Christi ~85.1%, Choke Canyon ~22.5%), the regional water system remains near the **Stage 1 / Band 1 drought threshold (40%)**, underscoring ongoing structural vulnerability.

### The Decision Gap

1. **Statutory Model Observation Lag:** Official regulatory tools, such as the Texas Commission on Environmental Quality (TCEQ) Water Availability Models (WAM Run 3), are vital for statutory water rights permitting but typically operate on multi-year observation release cycles. They are not structured for rapid, iterative exploratory screening during emerging drought periods.
2. **The Pre-Engineering Screening Void:** Municipal utilities, regional water planning groups, and Water Control & Improvement Districts (WCIDs) facing supply stress need a way to screen and shortlist plausible worst-case rainfall patterns before contracting multi-month engineering studies.
3. **Ad-Hoc Spreadsheets:** Informal spreadsheet models frequently lack spatial synchrony across sub-basins, risk computational corruption, and provide no cryptographic audit trail for public accountability.

**BASIN fills this gap.** It acts as an **Agile L0/L1 Screening Layer** that transforms 35 years of verified NOAA climate observations into defensible, reproducible drought stress scenarios and verified engineering handoff bundles.

---

## ⚡ Quick Start: 1-Click Desktop Installer (Recommended)

For municipal water managers, utility directors, consulting hydrologists, and civic leaders who want to run BASIN locally without installing Python, Git, or developer tooling:

1. Download **[Setup-BASIN.exe (v1.0.0)](https://github.com/nothing2me/basin/releases)** (~191 MB standalone installer).
2. Run the installer wizard. It installs directly to your local user directory (`%LOCALAPPDATA%\Programs\BASIN`) and requires **zero administrator privileges**.
3. Launch **BASIN** from your Windows Start Menu or Desktop shortcut. The application runs natively in an accelerated local WebView2 window with 35 years of NOAA regional climate records pre-indexed.

---

## 💻 Developer & Hydrologist CLI Setup

For hydrologists, data scientists, and developers running from source or extending the analytical pipeline:

### Prerequisites
* Windows 10 / 11 (64-bit)
* Python 3.12 (64-bit)
* Git

### Installation & Local Execution

```powershell
# 1. Clone the repository
git clone https://github.com/nothing2me/basin.git
cd basin

# 2. Create an isolated virtual environment
py -3.12 -m venv .venv

# 3. Install pinned dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Launch BASIN in your local browser
.\.venv\Scripts\python.exe scripts/start_browser.py
```

The application will bind strictly to loopback (`http://127.0.0.1:8501`) with **zero external telemetry or network calls**.

> **Note on Optional Local AI Assistant:** The core BASIN engine, mass-balance simulation, agronomics, and export modules function 100% offline out-of-the-box. An optional ~2.1 GB quantized GGUF model (`Qwen-2.5-3B-Instruct-Q4_K_M.gguf`) can be placed into the `models/` directory to enable the offline natural language analyst assistant.

---

## 📐 Architecture & Analytical Pipeline

```
[NOAA GHCN-Daily Climate Dataset (1991–2025)]
                      │
                      ▼
[Synchronized Historical Window Resampling (PCG64)]
                      │
                      ▼
[5-Dimensional Hydrologic Feature Extraction]
(Severity, Duration, Basin Concurrence, Summer Ratio, Dry-Spell Persistence)
                      │
                      ▼
[Local Unsupervised K-Means Clustering (k=6)]
                      │
                      ▼
[Scenario Shortlist Exemplar Selection]
                      │
                      ▼
[Mass-Conserving Multi-Reservoir Storage Simulation]
(Daily Inflow, Evaporative Losses, Demand Policy Interventions)
                      │
                      ▼
[Replayable Cryptographic Audit Bundle (.zip) & Companion Executive Brief (.pdf)]
```

The original three-station baseline and the expanded NOAA station network are **provisional rainfall proxies**, including 10 gauges placed inside the Nueces/Frio/Atascosa watersheds. BASIN screens rainfall scenarios; it does **not** predict reservoir inflow or freshwater availability. Calibrated catchment rainfall, streamflow integration, and expert-reviewed source-watershed suitability remain roadmap work requiring domain review.

---

## 🛠️ Core Capabilities

* **Synchronized Historical-Window Screening:** Resamples continuous multi-station weather windows from the 1991–2025 analysis snapshot using deterministic pseudo-random seeds (PCG64). The snapshot preserves a per-day distinction between valid NOAA observations and declared proxy fills. Constructed stress tests scale those inputs; they are not synthetic weather forecasts or validated catchment rainfall.
* **Multi-Factor Scenario Clustering:** Groups candidates using rainfall-deficit rank, duration, selected-station concurrence, summer timing, dry-spell persistence, and station-level deficits to create a varied review shortlist. Group labels organize the candidate pool; they do not establish drought probabilities.
* **Mass-Conserving Reservoir Simulation:** Simulates multi-reservoir joint storage drawdown with strict physical mass conservation (arithmetic $|\text{Error}| < 10^{-6}$ acre-feet), accounting for dynamic net surface evaporation, elevation-area curves, and inflows.
* **Demand Policy & Intervention Modeling:** Evaluates municipal drought stage triggers (Bands 1–4) and models policy decisions, such as comparing industrial exemptions (Drought Surcharge Exemption Fee / DSEF) against mandatory industrial curtailment schedules.
* **Illustrative Agronomic & Wildfire Indicators:** Applies monthly regional reference-ET normals and fixed crop coefficients to show a simplified daily rainfall–ET imbalance for cotton, sorghum, corn, pasture, and a general row crop. It also computes an approximate KBDI stress indicator. These screens omit a calibrated field soil-water balance and do not prescribe irrigation or determine burn bans.
* **Interconnected Water–Fire Screening:** Because the same rainfall deficit that draws down reservoirs also drives deep-soil moisture deficits, the reservoir drawdown, crop-stress, and approximate Keetch–Byram Drought Index (KBDI) screens all read from the same validated rainfall scenario — one offline pass connects municipal water stress, agricultural demand, and wildfire-season dryness without separate datasets or cloud services.
* **Cryptographic Replay Bundle & Companion Brief:** Generates portable `.zip` bundles containing run configuration metadata, input datasets, and SHA-256 verification manifests. Changing a reviewed rainfall revision invalidates its recorded inclusion decision until it is reviewed again. Replay verifies packet integrity and internal calculations; it is not a digital signature or scientific validation. An automated companion **Executive Technical Brief (PDF)** supports professional follow-up.
* **Deterministic Bounded Analyst Assistant:** Features an on-device, quantized 3B LLM (via `llama-cpp-python`) mapped strictly to **13 deterministic Python analytical tools**. The language model does not generate ungrounded arithmetic; it translates user inquiries into tool executions against verified simulation data.

---

## 📁 Repository Structure

```text
basin/
├── app.py                      # Main Streamlit application entry point
├── basin_ui.py                 # Multi-tab UI view orchestration & workflows
├── basin_theme.py              # Theme styling, CSS tokens, and layout configs
├── basin_core/                 # Core analytical screening engine
│   ├── agronomics.py           # Monthly ET-normal crop screen and approximate KBDI
│   ├── analysis.py             # Statistical calculations and feature metrics
│   ├── data.py                 # Verified snapshot loading and station indexing
│   ├── engine.py               # Scenario generation and feature extraction
│   ├── analysis.py             # Ranking, clustering, and comparative calculations
│   ├── exporter.py             # Bundle packing and SHA-256 replay verification
│   ├── assistant.py            # Bounded analyst routing and response assembly
│   ├── simulation.py           # Mass-conserving multi-reservoir drawdown engine
│   └── tools.py                # Deterministic analytical tools for LLM assistant
├── data/                       # Bundled NOAA climate records & historical baselines
├── docs/                       # Technical briefs, methodology notes, and specs
├── models/                     # Storage directory for optional local GGUF models
├── scripts/                    # Helper utilities, verification, and desktop launcher
│   ├── demo_smoke.py           # Offline socket-blocked smoke test
│   ├── replay_bundle.py        # Independent cryptographic replay verifier
│   └── start_browser.py        # Headless local browser launcher
└── tests/                      # Automated regression test suite
```

---

## 🧪 Verification & Test Suite

BASIN includes an automated regression test suite covering physical mass conservation, scenario determinism, and cryptographic replay verification:

```powershell
# Run the complete test suite
.\.venv\Scripts\python.exe -m pytest -q

# Verify cryptographic replay of an exported scenario bundle
.\.venv\Scripts\python.exe scripts/replay_bundle.py output/BASIN-sample-bundle.zip

# Run offline socket-blocked smoke verification
.\.venv\Scripts\python.exe scripts/demo_smoke.py
```

---

## 📚 Data Provenance & Citations

Underlying public records come from the sources below. BASIN also creates explicitly labeled proxy fills and illustrative derived calculations; those transformations are recorded in the snapshot and export metadata.

* **NOAA National Centers for Environmental Information (NCEI):** Global Historical Climatology Network - Daily (GHCN-Daily). The bundled registry contains **21 point stations**: 11 regional stations in the Corpus Christi, Victoria, San Antonio, Kingsville, Rockport/Aransas, and Alice footprints, plus **10 watershed gauges inside the Nueces / Frio / Atascosa drainage basins** (Leakey, Camp Wood, Hondo, Crystal City, Carrizo Springs, Pearsall, Choke Canyon Dam, Pleasanton, Three Rivers, Mathis) that feed Choke Canyon Reservoir and Lake Corpus Christi. Exact identifiers, coordinates, raw coverage, proxy-fill counts, source URLs, and snapshot hashes are recorded in `data/manifest.json`. Watershed gauges are point observations, not calibrated catchment rainfall or runoff.
* **Texas Water Development Board (TWDB):** Water Data for Texas historical reservoir elevations, storage capacities, and surface area curves.
* **Texas Commission on Environmental Quality (TCEQ):** Nueces River Basin Water Availability Model (WAM Run 3) parameter baselines.

---

## 🏛️ Team Attribution

BASIN was engineered for the **Zoho Corporation "From The Ground Up" AI Hackathon 2026** (Finalist Showcase, Pleasanton, CA) by student engineers from **Texas A&M University–Corpus Christi (TAMU-CC)**:

* **Noah Wilborn:** Full-Stack Architecture, Hydrologic Modeling & Systems Integration
* **Mohammed Asad Khan:** On-Device AI Architecture, Verification & Data Integrity
* **Misha Stegall:** User Experience, Field Research & Community Water Utility Analysis

---

## 📄 License & Engineering Disclaimer

* **License:** Distributed under the [MIT License](LICENSE).
* **Engineering Boundary & Licensure Disclaimer:** BASIN is an agile exploratory screening workbench designed for decision support, scenario discovery, and technical handoff. It produces empirical rainfall-stress scenarios and illustrative storage drawdowns, **not** certified water-availability models, official safe-yield forecasts, or sealed engineering reports under Texas Occupations Code Chapter 1001 (Texas Engineering Practice Act). Formal infrastructure and permitting determinations require evaluation by a licensed Professional Engineer (PE).
