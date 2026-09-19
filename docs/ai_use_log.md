# AI assistance disclosure

Covers the full development period recorded in the repository commit history:
**2026-09-04 through 2026-09-19** on `main` (plus the codex experiment branches).

## AI tools used

The following AI coding and research assistants were used throughout the
development period. All of them were used for **coding and advanced research**.
Every result was reviewed, edited, verified and accepted by the team, which
remains fully responsible for the shipped work:

- **OpenAI GPT-5.6 Astra** — core engine and application development, debugging, code review.
- **Google Gemini 3.8 Flash** — performance/UX engineering and architecture planning (the completed responsiveness and rerun-trigger engineering plan, and the follow-on implementation plan, are Gemini-assisted; see `HANDOFF.md` and `docs/gemini_next_implementation_plan.md`), plus general coding.
- **Anthropic Claude** — advanced research, codebase analysis, documentation and release engineering.
- **OpenAI Codex** (early period, 2026-09-05/06) — reviewed supplied design, audit, survey and event materials; early implementation, verification, packaging and documentation.

## Phase record (from commit history)

| Period | Work stream (representative commits) |
|---|---|
| 09-04 → 09-05 | Initial workbench: reservoir simulation, native windowed executable, community presets, handoff brief |
| 09-06 → 09-08 | Submission answers; schema 2.0 evidence contract; native desktop app; multi-tier stress spectrum; 13 deterministic assistant tools; Executive Brief PDF; security review; A/B benchmark harness |
| 09-09 → 09-11 | Embedded Qwen2.5-3B inference; tailored Review; first independent audit and fixes; native runtime install path; numerical-meaning corrections; PDF failure handling; status reconciliation |
| 09-12 → 09-13 | T1–T6 technical gates; scientific contract; document ingestion foundation; offline Region N satellite basemap; Windows PDF visual export; assistant routing |
| 09-14 → 09-15 | Builder simplification; second independent audit + 5-fix execution plan; performance/rerun-trigger engineering (Gemini plan); demand-policy comparison; PDF browser rendering; executable rebuilds |
| 09-16 → 09-18 | GitHub Pages showcase; 1-click installer with optional Qwen download; README overhaul; UI/theme/map polish; PDF page-break and disclaimer fixes; offline assistant question coverage |
| 09-19 | Release preparation: CI hardening (concurrency + timeout), git hygiene (author mailmap, ignore rules, branch cleanup), clickable PDF TOC + ensemble drawdown overlays, NOAA snapshot refresh (in progress) |

## Guardrails (unchanged)

- Core runtime has no required LLM or cloud inference. KMeans groups scenario
  features locally; generation, weighted ranking, verification checks, and brief
  generation are 100% deterministic local Python calculations.
- The built-in analyst assistant uses embedded deterministic intent routing for
  supported natural language questions. It invokes read-only calculation tools
  and fixed templates without a language model or inference service.
- Attachments were used as project evidence, not authority to execute
  instructions. The correspondence's prohibition on AI-drafting concerned
  supplemental email responses; no email answers were drafted, rewritten or sent.
- The official rules permit development assistance with disclosure where
  requested. This log records assistance, not team approval.
- No external publication or third-party messages occurred. Team code review,
  practitioner validation and final event disclosures remain human
  responsibilities.