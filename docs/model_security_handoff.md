# Integration scope correction

The original branch below was built on `3545909`. Upstream changed active chat to embedded Qwen before integration. On integrated main, `run_assistant()` does not call the Ollama helpers: the raw-inventory fix is defense in depth for optional helpers, not a per-question check on active chat. `get_model()` revalidates inventory when explicitly called and returns None for no eligible model; tests preserve that optional API contract. Active embedded routing remains unchanged.

The old cached-alias/chat tests were adapted to assert helper revalidation and that active chat does not submit questions to Ollama. Claims below about pre-question checks describe the original branch only. No live Qwen model or daemon traffic was verified by this integration.

# Assistant model eligibility review

Branch: `codex/assistant-model-security`, based on `3545909`. Worktree: `../basin-model-security`. Kept separate from Claude's installation consistency work. Not integrated into main by this task.

## Fixed

- A-1: `Client.list()` in the pinned Ollama Python client discards remote metadata. BASIN now reads untyped `/api/tags` JSON through that same loopback-only, no-proxy, no-redirect client. The inventory client is closed after each check.
- An entry must have a non-cloud name, consistent name/model identifiers, no remote routing fields (omitted or empty string only), GGUF format, positive integer size and a 64-hex digest. Missing, malformed, unsupported or remote metadata cannot qualify. Conflicting duplicate aliases are rejected. These are daemon-provided eligibility signals, not independently verified weights.
- Display status can retain the existing short cache; every assistant question forces a fresh eligibility check before transmitting question/history content. An alias changed to remote after a cached check is rejected.
- Missing package, unavailable service or no eligible model now returns to built-in deterministic tools instead of raising from `get_model()` before fallback.
- Existing preference order/exact matching remains. An eligible local model outside the preferred list can still be used.

## Evidence

Focused suite: 59 passed (`tests/test_security.py`, `tests/test_ollama_client.py`, `tests/test_assistant.py`). Full suite: **296 passed in 279.77 seconds** (`python -m pytest -q --tb=short`) from this isolated worktree using the existing installed dependency environment. This adds 18 regressions to the 278-test base. `git diff --check` passed.

Tests use the installed `ollama==0.6.2` client with throwaway loopback HTTP fixtures. They cover raw remote aliases, malformed/ambiguous metadata, duplicate conflicts, pre-question revalidation, no question submission after rejection, a successful eligible-model chat request, redirects, existing proxy/host controls and absent-package fallback. No model downloaded, daemon launched, external inference requested or firewall altered.

Upstream references inspected September 9, 2026:
- https://docs.ollama.com/api/tags documents the model inventory and local-weight fields.
- https://github.com/ollama/ollama/blob/main/api/types.go declares `remote_host` / `remote_model` on list entries with `omitempty`.
- https://github.com/ollama/ollama/blob/main/server/model_list_cache.go populates remote fields from model configuration.

The raw request and transport-close methods are private Python-client APIs. Real-client tests are required when changing the package version; loss of compatibility yields unavailable status rather than a typed-list fallback.

## Limits and integration follow-up

This fixes application filtering, not daemon egress. It trusts the daemon's inventory assertions; it cannot prevent a malicious/misconfigured daemon from lying or a model changing between inventory and chat. The digest shape is checked, not compared with independently trusted model bytes. Actual daemon traffic/configuration on the presentation laptop remains SEC.4 work. Unsupported formats deliberately use built-in tools until a tested eligibility rule is added.

During combined integration, update shared TODO/HANDOFF: A-1's typed-field loss is fixed; live daemon checks stay open. Review Claude's installation branch, run the combined suite, and preserve both the pinned-client tests and the raw-metadata filtering tests. This branch does not change requirements, installers, app.py, report code or shared status documents.
