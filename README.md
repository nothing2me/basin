# BASIN: Basin Analysis & Scenario Intelligence Navigator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2064--bit-0078D6.svg?logo=windows&logoColor=white)](https://github.com/nothing2me/basin/releases)
[![Offline: 100% Air-Gapped](https://img.shields.io/badge/Execution-100%25%20Offline-10B981.svg)](https://nothing2me.github.io/basin/)
[![Competition: Finalist](https://img.shields.io/badge/Zoho%20Hackathon-Finalist%202026-F59E0B.svg)](https://nothing2me.github.io/basin/)

> **100% On-Device, Tamper-Evident Hydrologic Screening and Drought Scenario Intelligence for Rural Communities.**

🌐 **Official Showcase Website & Technical Documentation:** [https://nothing2me.github.io/basin/](https://nothing2me.github.io/basin/)

---

## ⚡ Quick Start: 1-Click Desktop Installer (Recommended)

For water district managers, rural municipal staff, and city council members who want to run BASIN immediately without installing Python, Git, or developer tools:

1. Download **[Setup-BASIN.exe (v1.0.0)](https://github.com/nothing2me/basin/releases)** (~191 MB standalone installer).
2. Double-click to run the setup wizard. It installs directly to your local user profile (`%LOCALAPPDATA%\Programs\BASIN`) and requires **zero administrator privileges**.
3. Launch **BASIN** directly from your Windows Desktop icon or Start Menu. It runs as a native desktop application in an accelerated WebView2 window with 35 years of NOAA regional climate observations pre-indexed.

---

## 💻 Developer & Hydrologist CLI Setup

For developers running from source or extending the analytical pipeline:

### Prerequisites
* Windows 10 / 11 (64-bit)
* Python 3.12 (64-bit)

### Installation
```powershell
# 1. Clone repository
git clone https://github.com/nothing2me/basin.git
cd basin

# 2. Create isolated virtual environment
py -3.12 -m venv .venv

# 3. Install pinned dependencies
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Launch BASIN in your local browser
.venv\Scripts\python.exe scripts/start_browser.py
```

The application will launch on `http://127.0.0.1:8501` (binding strictly to loopback with zero external network connectivity).

---

## 🌊 Why BASIN? (The Regional Crisis)

In mid-April 2026, the primary surface reservoirs supplying half a million people in the Texas Coastal Bend (Region N)—Lake Corpus Christi and Choke Canyon—dropped to an all-time low of **7.7% combined capacity**. This breached the 75,000 acre-foot safe-yield reserve, the physical point where intake pumps cavitate (suck air), silt clogs intakes, and gravity flow fails.

### The Problem:
* **The 2015 State Model Freeze:** The official Texas Water Availability Model (WAM) was granted a state budget variance freezing its hydrologic dataset at **December 31, 2015**. Official state models were legally and technically blind to the recent decade-long mega-drought.
* **The $50k / 6-Month Consulting Barrier:** Small municipal water providers and rural Water Control & Improvement Districts (WCIDs) facing emergency drought cannot afford \$50,000 to \$100,000 and 6 months for engineering consulting firms to scope preliminary scenarios.
* **Fragile Spreadsheets:** Ad-hoc Excel spreadsheets lack spatial correlation, break easily, and provide zero audit trail.

**BASIN fills this void.** It provides an **Agile L0/L1 Screening & Verification Layer** that turns 35 years of raw weather observations into diverse, defensible drought stress scenarios and verified engineering handoffs in **5 minutes**.

---

## 🛠️ Core Capabilities

* **Deterministic Scenario Generation:** Resample complete synchronized historical rainfall windows (NOAA GHCN-Daily 1991–2025 across regional stations) with user-declared retention stress factors. Zero synthetic rain; zero fabricated days.
* **Unsupervised Machine Learning (K-Means):** Maps candidate droughts into an **8-dimensional hydrologic feature space** (severity, duration, multi-basin concurrence, summer fraction, dry-spell runs) and extracts balanced, non-redundant archetypes.
* **Mass-Conserving Reservoir Simulation:** Simulates daily multi-reservoir drawdown, evaporation, and municipal intake cavitation with strict physical mass conservation ($|\text{Error}| < 10^{-6}$ acre-feet).
* **Demand Policy & Equity Modeling:** Test real-world policy interventions: compare status quo industrial exemptions (the Drought Surcharge Exemption Fee / DSEF) against mandatory industrial curtailment and residential Stage 3 restrictions.
* **Agronomics & Wildfire Interoperability:** Computes daily Reference Evapotranspiration ($ET_o$) and Crop Evapotranspiration ($ET_c = ET_o \times K_c$) across regional crops (cotton, grain sorghum, corn, citrus) and tracks deep-soil moisture deficit via the Keetch-Byram Drought Index (KBDI).
* **Tamper-Evident Cryptographic Audit Trail:** Any edit or multiplier automatically revokes previous approvals. Compiles into an immutable `.zip` bundle with SHA-256 manifests and publication-ready **PDF Executive Briefs** for city council decision-makers.
* **Embedded Zero-Hallucination Assistant:** A local, quantized 3B LLM (Qwen-2.5-3B-Instruct GGUF via `llama-cpp-python`) mapped strictly to **13 deterministic Python math tools**. The model never calculates numbers; it routes queries to verified physics.

---

## 📐 Architecture Pipeline

```
[NOAA GHCN-Daily Snapshot 1991–2025] ──► [Synchronized Window Resampling (PCG64)]
                                                │
                                                ▼
[8D Feature Vectorization] ──────────────► [Local K-Means Clustering (k=6)]
                                                │
                                                ▼
[Shortlist Exemplar Selection] ──────────► [Mass-Conserving Storage Simulation]
                                                │
                                                ▼
[Cryptographic Replay Verifier] ─────────► [PDF Executive Brief & Verified ZIP]
```

---

## 🧪 Verification & Test Suite

BASIN includes an exhaustive regression test suite ensuring mathematical accuracy, mass conservation, and tamper-evidence:

```powershell
# Run the complete test suite (787+ automated tests)
.venv\Scripts\python.exe -m pytest -q

# Verify cryptographic replay of an exported data bundle
.venv\Scripts\python.exe scripts/replay_bundle.py output/BASIN-rehearsal.zip

# Run offline socket-blocked smoke test
.venv\Scripts\python.exe scripts/demo_smoke.py
```

---

## 🏛️ Project & Team Attribution

BASIN was developed for the **Zoho Corporation "From The Ground Up" AI Hackathon 2026** (Finalist Showcase, Pleasanton, CA) by student engineers from **Texas A&M University–Corpus Christi (TAMU-CC)**:

* **Noah Wilborn:** Full-Stack Systems & Hydrologic Physics
* **Mohammed Asad Khan:** On-Device AI Architecture & Data Integrity
* **Misha Stegall:** Community Usability & Field Research

---

## 📄 License & Disclaimer

* **License:** Distributed under the [MIT License](LICENSE).
* **Engineering Boundary (§ 1001 Compliance):** BASIN is an agile L0/L1 exploratory screening workbench designed for decision-support and technical handoff. It produces rainfall-stress scenarios, not statutory safe-yield declarations or licensed engineering certifications under the Texas Engineering Practice Act.
