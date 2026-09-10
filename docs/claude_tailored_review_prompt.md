# Claude task: tailored Review

Implement Noah's tailored Review UI for BASIN. Base main e35a57b; create a separate worktree and feat/tailored-review branch. Do not edit main or another agent's worktree. Read repository instructions and docs/tailored_review_proposal.md. If origin/main advances, inspect it before choosing the base.

Add a short skippable setup: goal (compare rainfall / illustrative storage / reviewed handoff), data (regional observations / own rainfall data / example), and guidance (guided / technical). Show relevant tools first. Provide Change focus and Show all tools. Reuse existing upload/example flows; never imply data is uploaded or validated merely because a preference was selected.

Changing focus must preserve calculations, weights, simulation inputs, selected/accepted scenarios, private-note consent and export eligibility. Always retain source identity, uncertainty and illustrative-model limitations. Keep preferences separate from ExperimentConfig. Preserve navigation state and older saved runs. Follow the proposal's persistence contract.

You own app.py, a new dedicated Review-preferences/UI module, focused tests and docs/tailored_review_handoff.md. Keep edits localized. Do not modify basin_core/assistant.py, basin_core/qwen_runtime.py, basin_ui.py, model setup/downloads, dependencies, calculation modules, PDF rendering, TODO.md or HANDOFF.md. Astra is auditing the assistant concurrently. Describe any need for a protected-file change instead of editing it.

Test skipped setup, every focus, Show all tools, navigation, save/reopen and unchanged numerical/consent state. Inspect light/dark, keyboard and narrow-screen behavior where tools permit. Report untested cases honestly; automated tests are not community validation.

Commit on your branch; do not merge or push main. Return base SHA, commit SHA, worktree, changed files, test results, visual evidence where available and remaining limitations. Astra will review and integrate both branches.
