"""Probe an installed Ollama Python client for the options BASIN's assistant relies on.

Run inside a virtualenv that has one exact ``ollama`` version installed:

    python scripts/probe_ollama_client.py

The probe never contacts an external service and never downloads a model. It starts a
throwaway HTTP listener on 127.0.0.1 and checks three things against it:

1. ``ollama.Client`` accepts the host/trust_env/follow_redirects/timeout options BASIN
   passes, and those options reach the underlying transport.
2. The client refuses to follow an HTTP redirect, so a daemon that answers with a
   redirect to somewhere else cannot pull the request off the loopback interface.
3. ``list()`` returns the response shape ``check_ollama`` reads (``.models[].model``).

Exit status is 0 only when every check passes. Results print as JSON.
"""
from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
TAGS_PAYLOAD = json.dumps({
    "models": [
        {"model": "qwen2.5:3b", "name": "qwen2.5:3b", "size": 1, "digest": "d" * 64,
         "modified_at": "2026-01-01T00:00:00Z",
         "details": {"family": "qwen2", "parameter_size": "3B", "quantization_level": "Q4_0",
                     "format": "gguf", "families": ["qwen2"], "parent_model": ""}},
    ]
}).encode()


class Recorder(BaseHTTPRequestHandler):
    """Answers /api/tags, and redirects anything else to a second local port."""

    mode = "ok"
    redirect_to = ""
    seen: list[str] = []

    def log_message(self, *args):  # keep the probe output clean
        pass

    def do_GET(self):
        type(self).seen.append(self.path)
        if type(self).mode == "redirect":
            self.send_response(307)
            self.send_header("Location", type(self).redirect_to)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(TAGS_PAYLOAD)))
        self.end_headers()
        self.wfile.write(TAGS_PAYLOAD)


def serve(handler_cls):
    server = HTTPServer((HOST, 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]


def build_client(ollama, port):
    """Exactly the construction basin_core.assistant.local_client uses."""
    return ollama.Client(host=f"http://{HOST}:{port}", trust_env=False,
                         follow_redirects=False, timeout=30.0)


def main() -> int:
    results = {}
    try:
        import ollama
        from importlib.metadata import version
        results["ollama_version"] = version("ollama")
        try:
            results["httpx_version"] = version("httpx")
        except Exception:
            results["httpx_version"] = None
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 1

    # 1. Construction and option propagation -------------------------------------------
    server, port = serve(type("OkHandler", (Recorder,), {"mode": "ok", "seen": []}))
    try:
        client = build_client(ollama, port)
        transport = getattr(client, "_client", None)
        results["accepts_options"] = True
        results["base_url"] = str(getattr(transport, "base_url", ""))
        results["trust_env"] = getattr(transport, "trust_env", None)
        results["follow_redirects"] = getattr(transport, "follow_redirects", None)
        timeout = getattr(transport, "timeout", None)
        results["timeout_read"] = getattr(timeout, "read", None)

        # 3. Response shape check --------------------------------------------------------
        listed = client.list()
        results["list_models"] = [m.model for m in listed.models]
        results["response_shape_ok"] = results["list_models"] == ["qwen2.5:3b"]
    except Exception as exc:
        results["accepts_options"] = False
        results["construction_error"] = f"{type(exc).__name__}: {exc}"
        results["response_shape_ok"] = False
    finally:
        server.shutdown()

    # 2. Redirect refusal --------------------------------------------------------------
    sink_handler = type("SinkHandler", (Recorder,), {"mode": "ok", "seen": []})
    sink, sink_port = serve(sink_handler)
    redirect_handler = type("RedirectHandler", (Recorder,), {
        "mode": "redirect", "redirect_to": f"http://{HOST}:{sink_port}/api/tags", "seen": [],
    })
    redirector, redirect_port = serve(redirect_handler)
    try:
        client = build_client(ollama, redirect_port)
        try:
            client.list()
            results["redirect_followed_or_error"] = "no error raised"
        except Exception as exc:
            results["redirect_followed_or_error"] = f"{type(exc).__name__}"
        results["redirect_target_contacted"] = bool(sink_handler.seen)
        results["redirect_refused"] = not sink_handler.seen
    finally:
        redirector.shutdown()
        sink.shutdown()

    results["all_checks_passed"] = bool(
        results.get("accepts_options")
        and results.get("response_shape_ok")
        and results.get("redirect_refused")
        and results.get("trust_env") is False
        and results.get("follow_redirects") is False
    )
    print(json.dumps(results, indent=2, default=str))
    return 0 if results["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
