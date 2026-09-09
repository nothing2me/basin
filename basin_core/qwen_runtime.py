"""Application-owned embedded Qwen2.5-3B inference runtime.

Loads GGUF weights directly from disk via embedded llama-cpp-python C++ bindings.
Runs in an application-owned worker process communicating over local IPC pipes,
keeping heavy inference off the Streamlit UI thread and enabling clean cancellation,
timeout recovery, crash isolation, and zero external services.
"""
from __future__ import annotations

import hashlib
import json
import logging
import multiprocessing as mp
from pathlib import Path
import queue
import sys
import threading
import time
from typing import Any, Callable, Generator

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = ROOT / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"
MANIFEST_PATH = ROOT / "models" / "manifest.json"

CONTEXT_WINDOW_TOKENS = 8192
MAX_OUTPUT_TOKENS = 1024

_CLIENT_LOCK = threading.Lock()
_GLOBAL_CLIENT: QwenInferenceClient | None = None


def resolve_model_path() -> Path | None:
    """Find the GGUF model file in project or app directory."""
    candidates = [
        DEFAULT_MODEL_PATH,
        Path.home() / ".basin" / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf",
        ROOT / "dist" / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf",
    ]
    for p in candidates:
        if p.is_file() and p.stat().st_size > 100_000_000:
            return p
    return None


def get_model_info() -> dict[str, Any]:
    """Return model and runtime metadata without loading weights."""
    model_path = resolve_model_path()
    manifest: dict[str, Any] = {}
    if MANIFEST_PATH.exists():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        import llama_cpp
        runtime_version = getattr(llama_cpp, "__version__", "unknown")
        runtime_installed = True
    except ImportError:
        runtime_version = "not installed"
        runtime_installed = False

    return {
        "installed": runtime_installed,
        "runtime_version": runtime_version,
        "model_path": str(model_path) if model_path else None,
        "model_exists": model_path is not None,
        "model_name": manifest.get("filename", "qwen2.5-3b-instruct-q4_k_m.gguf"),
        "model_repo": manifest.get("repo", "Qwen/Qwen2.5-3B-Instruct-GGUF"),
        "model_revision": manifest.get("revision", "7dabda4d13d513e3e842b20f0d435c732f172cbe"),
        "expected_sha256": manifest.get("sha256", "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"),
        "quantization": manifest.get("quantization", "Q4_K_M"),
        "context_tokens": CONTEXT_WINDOW_TOKENS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }


def _worker_process_main(model_path_str: str,
                         req_queue: mp.Queue,
                         resp_queue: mp.Queue,
                         cancel_event: mp.Event):
    """Background worker process executing llama.cpp inference."""
    try:
        from llama_cpp import Llama
    except ImportError as err:
        resp_queue.put({"type": "init_error", "error": f"Failed to import llama_cpp: {err}"})
        return

    try:
        n_threads = max(1, min(8, (mp.cpu_count() or 4) - 1))
        # Initialise Llama model
        llm = Llama(
            model_path=model_path_str,
            n_ctx=CONTEXT_WINDOW_TOKENS,
            n_threads=n_threads,
            n_batch=512,
            verbose=False,
        )
        resp_queue.put({"type": "init_ok", "threads": n_threads})
    except Exception as err:
        resp_queue.put({"type": "init_error", "error": f"Failed to load model: {err}"})
        return

    while True:
        try:
            req = req_queue.get()
        except (KeyboardInterrupt, EOFError):
            break

        if not req or req.get("type") == "shutdown":
            break

        if req.get("type") == "ping":
            resp_queue.put({"type": "pong"})
            continue

        if req.get("type") == "generate":
            req_id = req["id"]
            messages = req["messages"]
            tools = req.get("tools")
            temperature = req.get("temperature", 0.1)
            max_tokens = min(req.get("max_tokens", MAX_OUTPUT_TOKENS), MAX_OUTPUT_TOKENS)

            cancel_event.clear()

            try:
                # Call create_chat_completion with tools if provided
                kwargs: dict[str, Any] = {
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                stream_gen = llm.create_chat_completion(**kwargs)

                accumulated_content = []
                accumulated_tool_calls: list[dict[str, Any]] = []

                cancelled = False
                token_count = 0
                t_start = time.time()

                for chunk in stream_gen:
                    if cancel_event.is_set():
                        cancelled = True
                        break

                    delta = chunk["choices"][0].get("delta", {})
                    token_text = delta.get("content") or ""
                    if token_text:
                        accumulated_content.append(token_text)
                        token_count += 1
                        resp_queue.put({
                            "type": "token",
                            "id": req_id,
                            "delta": token_text,
                        })

                    # Handle streaming tool calls
                    if "tool_calls" in delta and delta["tool_calls"]:
                        for tc_chunk in delta["tool_calls"]:
                            idx = tc_chunk.get("index", 0)
                            while len(accumulated_tool_calls) <= idx:
                                accumulated_tool_calls.append({
                                    "id": f"call_{len(accumulated_tool_calls)}_{int(time.time()*1000)}",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                })
                            fn_delta = tc_chunk.get("function", {})
                            if "name" in fn_delta and fn_delta["name"]:
                                accumulated_tool_calls[idx]["function"]["name"] += fn_delta["name"]
                            if "arguments" in fn_delta and fn_delta["arguments"]:
                                accumulated_tool_calls[idx]["function"]["arguments"] += fn_delta["arguments"]

                elapsed = max(0.001, time.time() - t_start)
                speed = token_count / elapsed

                final_text = "".join(accumulated_content).strip()

                # Fallback parser: if model emitted markdown tool calls or JSON blocks in text
                if not accumulated_tool_calls and final_text:
                    parsed_calls = _extract_json_tool_calls(final_text)
                    if parsed_calls:
                        accumulated_tool_calls = parsed_calls

                resp_queue.put({
                    "type": "done",
                    "id": req_id,
                    "content": final_text,
                    "tool_calls": accumulated_tool_calls if accumulated_tool_calls else None,
                    "tokens_generated": token_count,
                    "elapsed_sec": elapsed,
                    "tokens_per_sec": speed,
                    "cancelled": cancelled,
                })

            except Exception as err:
                resp_queue.put({
                    "type": "error",
                    "id": req_id,
                    "error": str(err),
                })


def _extract_json_tool_calls(text: str) -> list[dict[str, Any]] | None:
    """Extract structured tool calls formatted as Qwen <tool_call> tags or JSON blocks."""
    import re
    calls = []

    # 1. Qwen native <tool_call> tags: <tool_call>\n{"name": ..., "arguments": ...}\n</tool_call>
    qwen_matches = re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL)
    for m in qwen_matches:
        raw = m.strip()
        if raw.startswith("{{") and raw.endswith("}}"):
            raw = raw[1:-1].strip()
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                fn_name = data.get("name") or data.get("tool") or data.get("action")
                args = data.get("arguments") or data.get("parameters") or data.get("args") or {}
                if fn_name and isinstance(fn_name, str):
                    calls.append({
                        "id": f"call_{len(calls)}_{int(time.time()*1000)}",
                        "type": "function",
                        "function": {
                            "name": fn_name,
                            "arguments": json.dumps(args) if isinstance(args, dict) else str(args),
                        },
                    })
        except Exception:
            continue

    if calls:
        return calls

    # 2. Markdown ```json ... ``` blocks containing action / function
    matches = re.findall(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    for m in matches:
        try:
            data = json.loads(m.strip())
            if isinstance(data, dict):
                fn_name = data.get("name") or data.get("tool") or data.get("action")
                args = data.get("parameters") or data.get("arguments") or data.get("args") or {}
                if fn_name and isinstance(fn_name, str):
                    calls.append({
                        "id": f"call_{len(calls)}_{int(time.time()*1000)}",
                        "type": "function",
                        "function": {
                            "name": fn_name,
                            "arguments": json.dumps(args) if isinstance(args, dict) else str(args),
                        },
                    })
        except Exception:
            continue
    return calls if calls else None


class QwenInferenceClient:
    """Thread-safe, process-isolated client managing the background Qwen runtime."""

    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._req_queue: mp.Queue = mp.Queue()
        self._resp_queue: mp.Queue = mp.Queue()
        self._cancel_event: mp.Event = mp.Event()
        self._worker_process: mp.Process | None = None
        self._lock = threading.Lock()
        self._status = "uninitialized"
        self._error_message: str | None = None
        self._current_req_id: int = 0
        self._init_worker()

    def _init_worker(self):
        if not self.model_path.exists():
            self._status = "model_missing"
            self._error_message = f"Model file not found at {self.model_path}"
            return

        self._status = "loading"
        self._error_message = None

        self._worker_process = mp.Process(
            target=_worker_process_main,
            args=(str(self.model_path), self._req_queue, self._resp_queue, self._cancel_event),
            daemon=True,
        )
        main_mod = sys.modules.get("__main__")
        orig_file = getattr(main_mod, "__file__", None)
        orig_spec = getattr(main_mod, "__spec__", None)
        try:
            if main_mod is not None:
                if hasattr(main_mod, "__file__"):
                    main_mod.__file__ = None
                if hasattr(main_mod, "__spec__"):
                    main_mod.__spec__ = None
            self._worker_process.start()
        finally:
            if main_mod is not None:
                if orig_file is not None:
                    main_mod.__file__ = orig_file
                if orig_spec is not None:
                    main_mod.__spec__ = orig_spec

        # Wait up to 30 seconds for init response
        try:
            msg = self._resp_queue.get(timeout=30.0)
            if msg.get("type") == "init_ok":
                self._status = "ready"
            else:
                self._status = "error"
                self._error_message = msg.get("error", "Unknown worker init error")
        except queue.Empty:
            self._status = "error"
            self._error_message = "Worker process timed out during model initialization"
            self.shutdown()

    @property
    def status(self) -> str:
        """Returns 'ready', 'loading', 'error', 'model_missing', or 'busy'."""
        if self._worker_process is not None and not self._worker_process.is_alive() and self._status == "ready":
            self._status = "crashed"
            self._error_message = "Worker process terminated unexpectedly"
        return self._status

    @property
    def error_message(self) -> str | None:
        return self._error_message

    def cancel(self):
        """Signal the worker to immediately stop active token generation."""
        self._cancel_event.set()

    def generate(self,
                 messages: list[dict[str, Any]],
                 tools: list[dict[str, Any]] | None = None,
                 temperature: float = 0.1,
                 max_tokens: int = MAX_OUTPUT_TOKENS,
                 timeout: float = 120.0,
                 token_callback: Callable[[str], None] | None = None) -> dict[str, Any]:
        """Send a chat completion request to the worker process and wait for response."""
        with self._lock:
            # If crashed, attempt clean restart once
            if self._worker_process is None or not self._worker_process.is_alive():
                self._init_worker()
                if self.status != "ready":
                    raise RuntimeError(f"Qwen runtime unavailable: {self._error_message}")

            self._current_req_id += 1
            req_id = self._current_req_id

            req = {
                "type": "generate",
                "id": req_id,
                "messages": messages,
                "tools": tools,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            self._req_queue.put(req)

            deadline = time.time() + timeout
            tokens_text = []

            while time.time() < deadline:
                try:
                    resp = self._resp_queue.get(timeout=1.0)
                except queue.Empty:
                    if not self._worker_process.is_alive():
                        self._status = "crashed"
                        self._error_message = "Worker process died during generation"
                        raise RuntimeError(self._error_message)
                    continue

                if resp.get("id") != req_id:
                    continue

                resp_type = resp.get("type")
                if resp_type == "token":
                    delta = resp.get("delta", "")
                    tokens_text.append(delta)
                    if token_callback:
                        token_callback(delta)
                elif resp_type == "done":
                    return resp
                elif resp_type == "error":
                    raise RuntimeError(resp.get("error", "Generation error"))

            self.cancel()
            raise TimeoutError(f"Generation timed out after {timeout} seconds")

    def shutdown(self):
        """Cleanly terminate the worker process."""
        try:
            self._req_queue.put({"type": "shutdown"})
        except Exception:
            pass
        if self._worker_process and self._worker_process.is_alive():
            self._worker_process.terminate()
            self._worker_process.join(timeout=2.0)
        self._worker_process = None
        self._status = "shutdown"


def get_qwen_client() -> QwenInferenceClient:
    """Return or initialize the singleton Qwen inference client."""
    global _GLOBAL_CLIENT
    with _CLIENT_LOCK:
        if _GLOBAL_CLIENT is None or _GLOBAL_CLIENT.status in ("shutdown", "crashed"):
            model_path = resolve_model_path()
            if model_path is None:
                model_path = DEFAULT_MODEL_PATH
            _GLOBAL_CLIENT = QwenInferenceClient(model_path)
        return _GLOBAL_CLIENT
