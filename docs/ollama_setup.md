# Optional analyst assistant — setup and boundaries

BASIN's calculation engine, scenario generation, review workflow, export bundle and PDF
report all run with none of this installed. The assistant is optional throughout: when any
piece below is missing the app reports it and the deterministic tools stay usable.

## Three separate things

People often say "install Ollama" for all three. They fail independently and have to be
diagnosed separately.

| # | Piece | What it is | How it arrives | Size |
|---|---|---|---|---|
| 1 | **`ollama` Python package** | The HTTP client library BASIN imports. Pure Python. | `pip install -r requirements.txt` (pinned `ollama==0.6.2`) | ~50 KB plus dependencies |
| 2 | **Ollama service** | A separate native application that runs a local daemon, by default on `127.0.0.1:11434`. Not a Python package, not installed by pip. | Download from ollama.com and install for your OS | hundreds of MB |
| 3 | **A downloaded model** | Model weights the service serves. Nothing is bundled with BASIN. | `ollama pull qwen2.5:3b` | 2-5 GB per model |

Having (1) does not give you (2). Having (2) running does not give you (3). BASIN
distinguishes all three:

- Package missing → `check_ollama()` returns `reason: "ollama package not installed"`.
- Package present, service not running → `available: False` with the client's connection
  error. This is the state on a machine that has only run `pip install`.
- Service running, no model pulled → `available: True` with an empty `models` list and
  `selected: None`; `get_model()` then raises and tells you to pull one.

## Installing

```bash
# 1. Python client, pinned. Add the transitive closure for a reproducible install.
pip install -r requirements.txt -r requirements-assistant.txt

# 2. The service: download and install from https://ollama.com/download, then confirm
ollama --version

# 3. A model. BASIN prefers, in order:
#    qwen2.5:3b, llama3.2:3b, qwen2.5:7b, llama3.1:8b, mistral:7b
ollama pull qwen2.5:3b
```

Verify the client without the service or a model:

```bash
python scripts/probe_ollama_client.py
```

That probe starts a throwaway listener on `127.0.0.1`, checks the client honours BASIN's
host/proxy/redirect/timeout options and refuses redirects, and exits non-zero if not. It
never contacts an external service and never downloads a model.

## Why the version is pinned exactly

`requirements.txt` pinned `ollama>=0.4.0` until 2026-09-09. A range meant the client that
BASIN's security behaviour depends on could change on any fresh install. The pin is
`ollama==0.6.2`, chosen after testing 0.4.0, 0.4.9, 0.5.4 and 0.6.2 with
`scripts/probe_ollama_client.py`:

- All four accept `host`, `trust_env=False`, `follow_redirects=False` and `timeout=30.0`,
  propagate them to the underlying `httpx` client, refuse to follow a 307 redirect, and
  return the `.models[].model` response shape `check_ollama()` reads.
- **0.4.0 constrains `httpx>=0.27.0,<0.28.0`.** 0.4.9 and later relax this to `httpx>=0.27`,
  so pinning 0.4.0 would hold `httpx` back for everyone installing the assistant.
- 0.6.2 is the newest release at the pin date and resolves cleanly against the versions
  already pinned in `requirements.txt`: installing it upgraded nothing that was already
  present, adding only `httpx`, `httpcore`, `pydantic`, `pydantic-core`,
  `annotated-types` and `typing-inspection`. Those are pinned in
  `requirements-assistant.txt`.

## What the client boundary does and does not give you

The client is constructed in `basin_core/assistant.py::local_client()` as
`Client(host="http://127.0.0.1:11434", trust_env=False, follow_redirects=False, timeout=30.0)`.

Verified against the installed client in `tests/test_ollama_client.py`:

- The endpoint stays on loopback even with `OLLAMA_HOST`, `HTTPS_PROXY`, `HTTP_PROXY` and
  `ALL_PROXY` set to remote values.
- `trust_env=False` and `follow_redirects=False` reach the transport.
- A local fixture answering `307` to a second local port does not get followed: the
  redirect target is never contacted.

Not established by any of this:

- **What the Ollama daemon itself does.** It is a separate process under its own
  configuration. Constraining BASIN's client says nothing about the daemon's outbound
  connections, telemetry or model routing. Observing that requires watching real traffic
  on the presentation machine (open under SEC.4).
- **Model behaviour.** Pinning a client version is not a statement about hallucination,
  and the deterministic tools remain the only source of numbers.
- **Cloud-model filtering.** `check_ollama()` also tests `remote_host` and `remote_model`
  attributes. The pinned client parses responses into pydantic models that drop unknown
  fields, so those two checks cannot fire against a real daemon; only the `"cloud"`
  substring check on the model name applies. See
  `docs/dependency_advisories_2026-09-09.md` finding A-1.
