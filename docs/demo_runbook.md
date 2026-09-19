# September 22 Demo Runbook

Updated: September 19, 2026 | Product baseline: source checkout on `main` + `BASIN.exe` native launcher

> **Read this before anything else:** the previous version of this runbook (Sept 8)
> carried claims the 2026-09-15 independent audit flagged for removal — hardcoded
> B-009 numbers, "$50k and 6 months", "30×–50× acceleration", "Verified:" wording,
> and operational Stage-3 timing. They are gone. Any on-screen number quoted below
> must be **re-read from the live run on the target laptop**, not recalled from
> memory. See [Positioning & Judge Q&A](#positioning--judge-qa) for the honest framings.

## Three-Minute Product Demonstration Sequence

1. **Sidebar / Launch (`BASIN.exe`)**:
   - Show native desktop execution (EdgeChromium WebView2, no terminal flashing).
   - Use default settings: three provisional stations (`USW00012924`, `USW00012912`, `USW00012921`); 90, 180, 270 days; Jan/Apr/Jul/Oct; 35–85% retention; 300 candidates; 6 shortlisted; seed 22.
   - Explain the missing layer: statutory and engineering models (WAM / HEC-ResSim) take substantial time and specialized funding to update — the 2026 Region N plan itself notes the supply model's hydrology stops in 2015. BASIN screens drought scenarios *before* commissioning that work. Generate.

2. **Workspace / Clustering & Ranking**:
   - Point out synchronized whole-window resampling (maintaining physical cross-station correlation across the basin).
   - Show how KMeans groups diverse stress patterns across duration, deficit, and season — then the explainable weighted ranking (severity/duration/concurrence/season) picks a diverse shortlist.

3. **Grounded AI Assistant Interrogation**:
   - Click the vertical **AI Assistant** tab. Note the smooth hardware-accelerated drawer.
   - Ask: *"Why did `<top scenario>` rank first?"* — use the **live scenario ID** on screen, not a memorized one. Show the weight breakdown.
   - Explain that the embedded intent engine maps supported questions to **13 deterministic Python tools and fixed templates** — no language model or inference server is used for these answers.
   - Ask a follow-up like *"What was station concurrence in `<id>`?"* and read the value from the screen.

4. **Review / 1-Click Multi-Tier Stress Spectrum**:
   - Switch Series to **Reservoir simulation → Multi-Tier Stress Spectrum (100% · 80% · 60% · 40%)**.
   - Set Initial Storage to a value and **read the countdown matrix off the screen** (do not quote a memorized day).
   - Move Emergency Conservation up and show the breach day extends. Read both values aloud.
   - Frame the physics honestly: *"In this screening run, summer reservoir surface evaporation dominates the drawdown relative to the conservation savings — the exact ratio is on screen."*
   - If asked: this is an **illustrative mass-balance screening run, not a forecast** — see the positioning section.

5. **Review & Verified Export**:
   - Accept the scenario and log a hydrologist note (*"Reviewed: acute summer concurrent deficit"* — use "Reviewed", not "Verified").
   - Open **Exports** and click **Build verified export**.
   - Spotlight the **Executive Technical Brief (PDF)** and the companion deliverables: full replay ZIP bundle, verified Markdown brief, and **Open Output Folder** with green SHA-256 verification.
   - Say: *"The ZIP is replay-verified end-to-end. The PDF is the readable companion and is stamped as outside that verification contract."* — that honesty is a feature, not a caveat.

6. **Close on Impact & Usefulness**:
   - The A/B benchmark exists in `research/benchmark_no_basin_packet/` (audit trail, checksums, scenario outputs). You may describe it as *"an internal benchmark comparing from-scratch coding against BASIN"* — **do not cite a multiple unless you re-measure it on the target laptop first**. Lead with correctness and provenance instead: *"the exported packet lets a hydrologist trace every scenario back to its inputs."*

---

## Positioning & Judge Q&A

### The reservoir simulation question (most likely hard question)

> **Judge:** *"Your submission says BASIN does NOT predict reservoir levels. You're
> showing me reservoir drawdown charts. Which is it?"*

**Answer (memorize the shape, adapt the words):**
> "We kept that promise — BASIN doesn't predict. What you're seeing is an
> *illustrative* mass-balance screening run: the same rainfall-stress scenario fed
> through a strict conservation equation with evaporation and demand, to show which
> shortlisted scenarios would be worth deep modeling. It is stamped inside the PDF
> as an exploratory sensitivity tool, not an operational forecast, and it is not a
> safe-yield or restriction-date claim. The exportable artifact — the thing a
> hydrologist takes away — is the replay-verified rainfall-stress scenario bundle.
> The simulation is a visualization aid for triage, which is exactly the screening
> layer we proposed."

Backing you can point to: the PDF stamps "exploratory sensitivity tool, not an
operational delivery forecast" and "PDF NOT VERIFIED"; `basin_core/scientific_contract.py`
auto-rejects overclaims; the export has **no verdict field**.

### The survey question (second likely question)

> **Judge:** *"You said you surveyed professionals. How many? Can I see it?"*

**Answer:**
> "We ran a discovery survey with Region N professionals before the finalist round.
> Three consented responses, consistently pointing at the same pain: not a lack of
> data, but conflicting data with no trustworthy way to tell what's credible. We
> treat that as directional input — not a representative study — and it directly
> shaped the product's provenance guarantees. The raw responses stay private; the
> evidence record is in the repo (`research/survey_evidence.md`), and we're running
> an uncoached intended-user exercise this week to build on it."

**Do not say:** "a survey showed", "many professionals", "verified with professionals."

### Demo discipline (from the audit)

- **Lead with the deterministic assistant, keep Qwen optional.** The optional 2.1 GB
  model adds weight and failure modes to a demo that does not need it for correctness.
- Do not claim energy numbers as measured — the footprint panel reports an estimated
  15–65 W range. If you want a "measured" label, run one no-model pass on the target
  laptop and record wall/CPU time and energy first.
- Any Stage/Band breach day, percentage, or ratio quoted on stage must be read from
  the live run.

---

## Before Travel Checklist

- **Presentation Laptop:** 64-bit Windows with BASIN and its documented runtime prerequisites.
- **Offline Smoke Test:** run the full suite once on the target laptop:
  `.venv\Scripts\python.exe -m pytest -q` (817 passed / 2 expected skips as of 2026-09-19).
- **Re-measure on the target laptop:** (a) one no-model run time + energy for the footprint panel, (b) the A/B benchmark multiple if you intend to cite it, (c) the exact breach-day values used in the demo.
- **Projector Rehearsal:** connect external display at 1920×1080 and 1600×900 to ensure high-DPI scaling and split-pane layout render sharply.
- **Backup Assets:** USB stick containing:
  1. `BASIN.exe` standalone build (rebuilt from current `main`).
  2. Offline `.venv` wheelhouse.
  3. A pre-exported verified `BASIN-Export-*.zip`.
  4. Video recording of the 3-minute sequence.

---

## Recovery Procedures

- If a question is not recognized by the assistant: use a Quick Query or the Direct Tool Runner. Include scenario IDs and ask a complete question.
- If port 8501 is occupied: the native launcher cycles through ports 8501–8550 to find the first open port.
- On browser/webview refresh: saved sessions persist in `output/workspaces/` and can be reloaded in one click.

---

## Quick Judge Reference

- **AI Method:** Unsupervised KMeans clustering + deterministic intent routing to 13 read-only tools and fixed templates.
- **Grounded Responses:** numbers come from workspace calculations; routing accuracy still needs evaluation.
- **Why Not Existing Tools:** WAM / HEC-ResSim are heavy, static engineering models requiring months and specialized funding to update. BASIN is the missing agile, replay-verified screening and handoff layer before that investment.
- **Evidence of Usefulness:** internal A/B benchmark in `research/benchmark_no_basin_packet/` (re-measure the multiple before citing); provenance guarantees are the primary differentiator.
- **Community Evidence:** `research/survey_evidence.md` — three consented discovery responses, directional; uncoached intended-user exercise pending.