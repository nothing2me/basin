# Embedded Qwen audit — September 9, 2026

Base: e35a57b. Scope: active assistant response boundary, worker model loading and failure handling. Separate worktree/branch codex/qwen-runtime-audit; app.py and basin_ui.py unchanged to allow concurrent tailored Review work.

## Findings fixed

- Q1: run_assistant displayed arbitrary model prose, including alongside deterministic results. System-prompt rules were not enforcement. Model output now selects tools only; displayed answers come from validated tool results or the existing deterministic fallback. General model-authored explanations are intentionally no longer displayed.
- Q2: model tool-call lists had no execution budget. Validate the entire batch before execution; reject unknown/malformed calls, cancelled responses and more than three calls. Bound streamed tool indices before allocating list entries.
- Q3: model discovery used filename and minimum size; native loading did not enforce the downloader's pin. Worker verifies exact byte count and SHA-256 before importing/loading native inference. A mutable manifest cannot override the expected digest. Verification uses the existing repository pin; this audit does not independently authenticate its upstream provenance. Rehash on each worker load, not each question. A process with local write access could still replace a file between verification and native reopening; this is not a hostile-local-admin security boundary.
- Q4: generation timeout only set a cancellation event; a stuck worker could retain later requests. Timeout now terminates the worker; restarts receive fresh IPC queues. Tests cover timeout termination, not live native cancellation latency.
- Malformed manifest JSON shape and native import OSError no longer break metadata inspection.

## Evidence

`C:/Users/moham/Documents/GitHub/basin/.venv/Scripts/python.exe -m pytest -q tests/test_qwen_security.py tests/test_qwen_inference.py tests/test_assistant.py tests/test_assistant_adversarial.py tests/test_security.py tests/test_ollama_client.py tests/test_embedded_assistant_ui.py`

Result: **90 passed, 1 skipped in 27.66s**. The skipped case needs actual model weights. Includes real deterministic workspace tool rendering, invalid-batch zero-execution tests, altered-byte rejection, native-worker protocol fixtures, and network-blocked Streamlit drawer interactions. These fixtures do not establish live model quality or actual native egress. Full-project suite not rerun for this isolated pass; run it on combined integration before merging.

`scripts/demo_smoke.py` also passed: run ecfbbccc1540, five replayed scenarios and 500 audit records, no custom comparisons. This checks the rainfall workflow, not live native inference.

## Still open

1. **Installation blocker:** Setup BASIN.cmd --with-ai downloads weights but no declared requirements installs llama-cpp-python. Package metadata is absent from the reviewed venv. The earlier TODO runtime pin is not an enforced install path. Establish a supported optional native wheel/version and install/repair flow, then test a clean Windows environment. Do not imply downloading weights alone activates inference.
2. Review native-runtime advisories and model distribution/provenance/license using verified sources. No new advisory scan, runtime installation, or model download was performed here; the old Ollama dependency report does not cover llama.cpp.
3. On the actual laptop, verify pinned model loading, missing DLL/runtime/weights, stopped/crashed/slow worker, repeat timeout recovery and core workflow availability offline. Record timings including hash verification; the initialization budget remains 30 seconds. Check browser/native network behavior separately.
4. Routing and numeric semantics still need domain-focused evaluation: valid tool arguments do not prove the model chose the intended scenario or interpreted the user's question correctly. Deterministic templates themselves still need the B15 scientific/wording audit.
5. The singleton client serializes inference. Multi-session responsiveness, queued-call waiting and cancellation responsiveness need dedicated real-runtime evaluation; this is not certified for concurrent remote users.

TODO historical teammate live-Qwen claims are not independent evidence from this environment. No scientific validation or blanket security approval is claimed.
