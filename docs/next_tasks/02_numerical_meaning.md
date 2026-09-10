# Task 2 — Numerical meaning across surfaces (Opus)

Read repository instructions, TODO.md's newest checkpoint and the relevant handoff before editing. Inspect current Git status and fetch origin. Work in a separate worktree and task branch from current origin/main; record its SHA. Do not modify the main checkout or another agent's worktree. Treat older checked TODO claims as historical until supported by current evidence.

Complete the bounded task, run focused behavioral checks, and commit on your branch. Do not merge or push main. Do not edit TODO.md or HANDOFF.md; write a task-specific handoff with changed files, exact commands/results, limitations, base/commit SHA and worktree path. Astra will review and integrate. Never invent expert approval, participant feedback, organizer requirements or successful manual checks. Do not broadly upgrade dependencies or alter unrelated features.

Audit remaining B15 and B18 argument-semantics items against the latest implementation. Read basin_core/analysis.py, tools.py, assistant.py, pdf_report.py and relevant app.py call sites. Trace original observations -> transformed scenario -> spectrum -> UI/tool/PDF. A 100% tier of an already-stressed scenario must not be presented as unstressed historical observations.

Fix concrete reference-label and input-interpretation errors. Check fraction/percent boundaries, rainfall depth versus storage volume, ac-ft/day versus MGD, threshold equality, requested dates/years/IDs and revision identity. Reject or clarify ambiguous input; never silently choose an unrelated first scenario or substitute 2011. Retain the existing numerical model unless an actual implementation bug is demonstrated. Do not invent calibrated restriction forecasts or domain validation.

Create hand-calculable regression fixtures for a transformed scenario, non-default rainfall tier, absent requested year, invalid percentage and threshold boundary. Confirm UI, deterministic assistant tools and PDF agree about the same selected inputs. Keep Qwen grounding and security tests intact. Record each old/new interpretation and any proposed physics change requiring human review.

This task overlaps report/UI files: do not run it concurrently with Task 3 or 4. Write docs/numerical_meaning_handoff.md. Acceptance is specific corrected semantics with reproducible examples, not a blanket scientific-validity claim.
