"""Compatibility and boundary tests against the real installed Ollama Python client.

These complement the mocked tests in ``test_security.py``. Mocks prove BASIN passes the
options it intends to; these prove the pinned client actually honours them.

Nothing here contacts an external service, starts the Ollama daemon, or downloads a
model. Every request goes to a throwaway HTTP listener bound to 127.0.0.1. None of it
establishes what a running Ollama daemon does with its own outbound connections.
"""
from __future__ import annotations

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from basin_core import assistant as a

ollama = pytest.importorskip("ollama", reason="optional assistant client is not installed")

ROOT = Path(__file__).resolve().parents[1]
PINNED = "ollama==0.6.2"

TAGS_PAYLOAD = json.dumps({
    "models": [
        {"model": "qwen2.5:3b", "name": "qwen2.5:3b", "size": 1, "digest": "d" * 64,
         "modified_at": "2026-01-01T00:00:00Z",
         "details": {"family": "qwen2", "parameter_size": "3B", "quantization_level": "Q4_0",
                     "format": "gguf", "families": ["qwen2"], "parent_model": ""}},
    ]
}).encode()


def make_handler(mode: str, redirect_to: str = ""):
    seen: list[str] = []
    submitted: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            seen.append(self.path)
            if mode == "redirect":
                self.send_response(307)
                self.send_header("Location", redirect_to)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(TAGS_PAYLOAD)))
            self.end_headers()
            self.wfile.write(TAGS_PAYLOAD)

        def do_POST(self):
            seen.append(self.path)
            submitted.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            body = json.dumps({"message": {"role": "assistant", "content": ""}, "done": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    Handler.submitted = submitted
    Handler.seen = seen
    return Handler


@pytest.fixture
def local_server():
    """Start throwaway loopback listeners and guarantee they are shut down."""
    started = []

    def start(mode="ok", redirect_to=""):
        handler = make_handler(mode, redirect_to)
        server = HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        started.append(server)
        return server.server_address[1], handler

    yield start
    for server in started:
        server.shutdown()
        server.server_close()


def client_for(port: int):
    """The construction basin_core.assistant.local_client uses, against a local port."""
    return ollama.Client(host=f"http://127.0.0.1:{port}", trust_env=False,
                         follow_redirects=False, timeout=30.0)


# --------------------------------------------------------------------------------------
# The pin itself
# --------------------------------------------------------------------------------------

def test_requirements_pin_is_exact_and_matches_the_tested_version():
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert PINNED in text, "requirements.txt must pin the exact tested client"
    assert not re.search(r"^ollama[><~!]", text, re.M), "no range pin for the assistant client"


def test_installed_client_matches_the_pin():
    from importlib.metadata import version
    assert version("ollama") == PINNED.split("==")[1]


def test_assistant_transitive_closure_is_pinned():
    text = (ROOT / "requirements-assistant.txt").read_text(encoding="utf-8")
    for package in ("httpx==", "httpcore==", "pydantic==", "pydantic-core==",
                    "annotated-types==", "typing-inspection=="):
        assert package in text, package


# --------------------------------------------------------------------------------------
# The real client honours the options BASIN passes
# --------------------------------------------------------------------------------------

def test_real_client_accepts_basin_options(local_server):
    port, _ = local_server()
    client = client_for(port)
    transport = client._client

    assert str(transport.base_url).rstrip("/") == f"http://127.0.0.1:{port}"
    assert transport.trust_env is False
    assert transport.follow_redirects is False
    assert transport.timeout.read == 30.0


def test_local_client_construction_survives_hostile_environment(monkeypatch, local_server):
    """Environment variables must not move the endpoint or re-enable proxying."""
    port, handler = local_server()
    monkeypatch.setenv("OLLAMA_HOST", "https://remote.invalid")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid")
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid")
    monkeypatch.setenv("ALL_PROXY", "http://proxy.invalid")

    client = client_for(port)
    assert client._client.trust_env is False
    assert str(client._client.base_url).rstrip("/") == f"http://127.0.0.1:{port}"

    listed = client.list()
    assert [m.model for m in listed.models] == ["qwen2.5:3b"]
    assert handler.seen, "the request reached the local fixture rather than a proxy"


def test_real_client_refuses_to_follow_a_redirect(local_server):
    """A daemon answering with a redirect must not pull the request somewhere else."""
    sink_port, sink_handler = local_server()
    redirect_port, redirect_handler = local_server(
        mode="redirect", redirect_to=f"http://127.0.0.1:{sink_port}/api/tags"
    )

    client = client_for(redirect_port)
    with pytest.raises(Exception):
        client.list()

    assert redirect_handler.seen, "the first request did reach the redirecting fixture"
    assert not sink_handler.seen, "the client must not have followed the redirect"


def test_response_shape_matches_what_check_ollama_reads(local_server, monkeypatch):
    port, _ = local_server()
    monkeypatch.setattr(a, "local_client", lambda: client_for(port))
    a._OLLAMA_CACHE.clear()
    status = a.check_ollama(force_refresh=True)
    a._OLLAMA_CACHE.clear()

    assert status["available"] is True
    assert status["models"] == ["qwen2.5:3b"]
    assert status["selected"] == "qwen2.5:3b"


# --------------------------------------------------------------------------------------
# Optional-assistant behaviour is preserved
# --------------------------------------------------------------------------------------

def test_missing_daemon_degrades_without_raising(monkeypatch):
    """Client installed, service not running: report unavailable, never crash."""
    closed = HTTPServer(("127.0.0.1", 0), make_handler("ok"))
    port = closed.server_address[1]
    closed.server_close()

    monkeypatch.setattr(a, "local_client", lambda: client_for(port))
    a._OLLAMA_CACHE.clear()
    status = a.check_ollama(force_refresh=True)
    a._OLLAMA_CACHE.clear()

    assert status["available"] is False
    assert status["models"] == [] and status["selected"] is None
    assert status["reason"]


def test_absent_package_is_reported_not_raised(monkeypatch):
    monkeypatch.setattr(a, "_OLLAMA_AVAILABLE", False)
    a._OLLAMA_CACHE.clear()
    status = a.check_ollama(force_refresh=True)
    a._OLLAMA_CACHE.clear()

    assert status == {"available": False, "reason": "ollama package not installed",
                      "models": [], "selected": None}
    with pytest.raises(RuntimeError, match="not installed"):
        a.local_client()


# --------------------------------------------------------------------------------------
# Recorded gap between the mocked test and the real client
# --------------------------------------------------------------------------------------

def test_remote_fields_are_dropped_by_the_real_client():
    """Typed list responses lose fields; BASIN must inspect the raw response instead.

    The original security mock used SimpleNamespace objects, where remote-field
    attributes survived. The pinned client ignores unknown fields, so attribute-only
    guards would be inert against a real daemon. This test preserves the reason
    BASIN uses untyped inventory metadata instead.
    """
    parsed = ollama.ListResponse(models=[{
        "model": "alias:latest", "name": "alias:latest", "size": 1, "digest": "d" * 64,
        "modified_at": "2026-01-01T00:00:00Z",
        "remote_host": "https://remote.example", "remote_model": "remote:7b",
        "details": {"family": "x", "parameter_size": "7B", "quantization_level": "Q4_0",
                    "format": "gguf", "families": ["x"], "parent_model": ""},
    }])
    model = parsed.models[0]
    assert getattr(model, "remote_host", None) is None
    assert getattr(model, "remote_model", None) is None
    assert "remote_host" not in model.model_dump()

    # Name screening alone is not an eligibility decision.
    assert a.local_model("alias:latest") is True
    assert a.local_model("gpt-oss:120b-cloud") is False


@pytest.fixture
def raw_inventory(monkeypatch, local_server):
    port, handler = local_server()
    monkeypatch.setattr(a, "local_client", lambda: client_for(port))
    a._OLLAMA_CACHE.clear()
    def set_records(records):
        monkeypatch.setitem(globals(), "TAGS_PAYLOAD", json.dumps({"models": records}).encode())
    yield set_records, handler
    a._OLLAMA_CACHE.clear()


def local_entry(**changes):
    entry = {"model": "qwen2.5:3b", "name": "qwen2.5:3b", "size": 123,
             "digest": "d" * 64, "details": {"format": "gguf"}}
    entry.update(changes)
    return entry


@pytest.mark.parametrize("changes", [
    {"remote_host": "https://remote.example"}, {"remote_model": "remote:7b"},
    {"remote_host": None}, {"remote_model": False},
    {"model": "other:cloud", "name": "other:cloud"},
    {"name": "different:latest"}, {"details": {}}, {"details": {"format": "unknown"}},
    {"size": 0}, {"size": True}, {"digest": "missing"},
])
def test_raw_inventory_rejects_remote_and_ambiguous_models(raw_inventory, changes):
    set_records, handler = raw_inventory
    set_records([local_entry(**changes)])
    status = a.check_ollama(force_refresh=True)
    assert status["models"] == [] and status["selected"] is None
    assert handler.seen == ["/api/tags"]
    assert not handler.submitted


def test_raw_remote_alias_is_rejected_even_with_local_looking_name(raw_inventory):
    set_records, _ = raw_inventory
    set_records([local_entry(remote_host="https://remote.example"),
                 local_entry(model="local-alternative:latest", name="local-alternative:latest")])
    status = a.check_ollama(force_refresh=True)
    assert status["models"] == ["local-alternative:latest"]
    assert status["selected"] == "local-alternative:latest"


def test_conflicting_duplicate_alias_cannot_qualify(raw_inventory):
    set_records, _ = raw_inventory
    set_records([local_entry(), local_entry(remote_model="remote:latest")])
    assert a.get_model() is None


def test_inventory_malformed_json_fails_closed(raw_inventory, monkeypatch):
    monkeypatch.setitem(globals(), "TAGS_PAYLOAD", b'{"models": {}}')
    assert a.get_model() is None
    monkeypatch.setitem(globals(), "TAGS_PAYLOAD", b'not JSON')
    assert a.get_model() is None


def test_cached_local_alias_rechecked_before_optional_model_selection(raw_inventory, monkeypatch):
    set_records, handler = raw_inventory
    set_records([local_entry()])
    assert a.check_ollama(force_refresh=True)["selected"] == "qwen2.5:3b"
    set_records([local_entry(remote_host="https://remote.example")])
    monkeypatch.setattr(a, "semantic_query_route", lambda *args: "Built-in answer")
    assert a.get_model() is None
    reply, history = a.run_assistant(None, "PRIVATE-QUESTION-SENTINEL", [], use_qwen=False)
    assert reply == "Built-in answer" and len(history) == 2
    assert handler.seen == ["/api/tags", "/api/tags"]
    assert handler.submitted == []


def test_optional_model_selection_does_not_enable_ollama_chat(raw_inventory, monkeypatch):
    set_records, handler = raw_inventory
    set_records([local_entry()])
    monkeypatch.setattr(a, "semantic_query_route", lambda *args: "Built-in answer")
    assert a.get_model() == "qwen2.5:3b"
    a.run_assistant(None, "Synthetic test question", [], use_qwen=False)
    assert handler.seen == ["/api/tags"]
    assert handler.submitted == []


def test_raw_inventory_redirect_is_not_followed(local_server, monkeypatch):
    target_port, target_handler = local_server()
    port, handler = local_server("redirect", f"http://127.0.0.1:{target_port}/api/tags")
    monkeypatch.setattr(a, "local_client", lambda: client_for(port))
    a._OLLAMA_CACHE.clear()
    assert a.get_model() is None
    assert handler.seen and not target_handler.seen
    a._OLLAMA_CACHE.clear()
