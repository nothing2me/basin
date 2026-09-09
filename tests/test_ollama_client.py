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
    """The remote_host/remote_model guards in check_ollama cannot fire on real data.

    test_security.py::test_cloud_models_excluded_and_exact_tag_selected feeds
    SimpleNamespace objects, where ``getattr(m, "remote_host", None)`` works. The pinned
    client parses responses into pydantic models that ignore unknown fields, so those two
    guards are inert against a real daemon and only the ``"cloud"`` name check applies.
    This test pins the real behaviour so the gap is not mistaken for coverage.
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

    # The name-based check is the control that actually works today.
    assert a.local_model("alias:latest") is True
    assert a.local_model("gpt-oss:120b-cloud") is False
