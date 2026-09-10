# Task 3 — Report rendering failure and privacy checks (Sonnet)

Read repository instructions, TODO.md's newest checkpoint and the relevant handoff before editing. Inspect current Git status and fetch origin. Work in a separate worktree and task branch from current origin/main; record its SHA. Do not modify the main checkout or another agent's worktree. Treat older checked TODO claims as historical until supported by current evidence.

Complete the bounded task, run focused behavioral checks, and commit on your branch. Do not merge or push main. Do not edit TODO.md or HANDOFF.md; write a task-specific handoff with changed files, exact commands/results, limitations, base/commit SHA and worktree path. Astra will review and integrate. Never invent expert approval, participant feedback, organizer requirements or successful manual checks. Do not broadly upgrade dependencies or alter unrelated features.

Finish B17.3's remaining renderer-failure/degraded-output handling and B17.4 automated cross-output consent checks. Read current pdf_report.py, app export call sites and docs/report_device_acceptance.md. Most PDF content/layout work is already complete: do not rewrite it or undo configuration/revision identity safeguards.

Make actual renderer selection and degraded/fallback output visible to the user. Handle browser renderer missing/failing and file-write failures without reporting a full report as successfully produced when it was not. Preserve valid fallback output and disclose its limitations. Do not label the standalone PDF cryptographically verified by the rainfall ZIP contract.

Test available and failing render paths using isolated fixtures, long notes and private sentinel text. Check consent on/off/revocation and stale preview/packet removal. Verify rendered pages where a renderer is available; distinguish text extraction from visual inspection. Native browser download destination/recovery tests on the presentation laptop remain manual until actually run.

Own narrowly scoped PDF/export handling and tests, plus docs/pdf_failure_handoff.md. Run after Task 2 integration because both touch report code; not concurrently with Task 4's app.py edits.
