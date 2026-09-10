"""Weight-free regressions for the embedded assistant trust boundary."""
import hashlib
import queue
from types import SimpleNamespace

import pytest
from basin_core import assistant, qwen_runtime as runtime


def install_response(monkeypatch, response):
    client = SimpleNamespace(status="ready", generate=lambda *a, **k: response)
    monkeypatch.setattr(runtime, "get_qwen_client", lambda: client)
    monkeypatch.setattr(assistant, "semantic_query_route", lambda *a: "SAFE FALLBACK")


def test_model_prose_without_tools_is_not_displayed(monkeypatch):
    install_response(monkeypatch, {"content": "Restrictions start tomorrow. Guaranteed."})
    reply, history = assistant.run_assistant(None, "What happens next?", [])
    assert reply == "SAFE FALLBACK"
    assert history[-1]["content"] == reply


def test_model_prose_cannot_prefix_tool_evidence(monkeypatch, workspace):
    sid = workspace.selected[0]
    install_response(monkeypatch, {"content": "FABRICATED guarantee", "tool_calls": [
        {"function": {"name": "describe_scenario", "arguments": {"scenario_id": sid}}}]})
    reply, _ = assistant.run_assistant(workspace, "Describe this scenario", [])
    assert sid in reply
    assert "FABRICATED" not in reply
    assert "SAFE FALLBACK" not in reply


@pytest.mark.parametrize("calls,cancelled", [
    ([{"function": {"name": "describe_scenario", "arguments": {}}}] * 4, False),
    ([{"function": {"name": "describe_scenario", "arguments": {}}}, None], False),
    ([{"function": {"name": "unknown", "arguments": {}}}], False),
    ([{"function": {"name": "describe_scenario", "arguments": {}}}], True),
    ("invalid", False),
])
def test_invalid_batch_executes_no_model_tools(monkeypatch, calls, cancelled):
    executed = []
    monkeypatch.setitem(assistant.TOOL_REGISTRY, "describe_scenario", lambda *a, **k: executed.append(1))
    monkeypatch.setattr(assistant, "validate_tool_args", lambda *a: {})
    install_response(monkeypatch, {"tool_calls": calls, "cancelled": cancelled})
    reply, _ = assistant.run_assistant(None, "Question", [])
    assert reply == "SAFE FALLBACK"
    assert executed == []


def test_model_pin_verifies_bytes_not_manifest(monkeypatch, tmp_path):
    model = tmp_path / "model.gguf"
    model.write_bytes(b"fixture")
    monkeypatch.setattr(runtime, "MODEL_BYTES", 7)
    monkeypatch.setattr(runtime, "MODEL_SHA256", hashlib.sha256(b"fixture").hexdigest())
    runtime.verify_model_file(model)
    model.write_bytes(b"changed")
    with pytest.raises(ValueError, match="SHA-256"):
        runtime.verify_model_file(model)
    model.write_bytes(b"short")
    with pytest.raises(ValueError, match="size"):
        runtime.verify_model_file(model)


def test_worker_rejects_unverified_model_before_native_load(tmp_path):
    responses = queue.Queue()
    runtime._worker_process_main(str(tmp_path / "missing.gguf"), queue.Queue(), responses, None)
    result = responses.get_nowait()
    assert result["type"] == "init_error"
    assert "Model verification failed" in result["error"]


def test_timeout_terminates_worker(monkeypatch):
    client = runtime.QwenInferenceClient.__new__(runtime.QwenInferenceClient)
    import threading
    client._lock = threading.Lock()
    client._worker_process = SimpleNamespace(is_alive=lambda: True)
    client._current_req_id = 0
    client._req_queue = queue.Queue()
    actions = []
    monkeypatch.setattr(client, "cancel", lambda: actions.append("cancel"))
    monkeypatch.setattr(client, "shutdown", lambda: actions.append("shutdown"))
    with pytest.raises(TimeoutError):
        client.generate([], timeout=0)
    assert actions == ["cancel", "shutdown"]


@pytest.mark.parametrize("index", [-1, 3, 1000000000, True, "0"])
def test_worker_bounds_streamed_tool_indices(monkeypatch, index):
    import sys
    import threading
    class FakeLlama:
        def __init__(self, **kwargs):
            pass
        def create_chat_completion(self, **kwargs):
            yield {"choices": [{"delta": {"tool_calls": [{"index": index}]}}]}
    monkeypatch.setitem(sys.modules, "llama_cpp", SimpleNamespace(Llama=FakeLlama))
    monkeypatch.setattr(runtime, "verify_model_file", lambda path: None)
    requests, responses = queue.Queue(), queue.Queue()
    requests.put({"type": "generate", "id": 1, "messages": []})
    requests.put({"type": "shutdown"})
    runtime._worker_process_main("fixture", requests, responses, threading.Event())
    assert responses.get_nowait()["type"] == "init_ok"
    result = responses.get_nowait()
    assert result["type"] == "error"
    assert "tool-call index" in result["error"]


def test_manifest_cannot_override_expected_hash(monkeypatch, tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"sha256": "attacker value"}')
    monkeypatch.setattr(runtime, "MANIFEST_PATH", manifest)
    assert runtime.get_model_info()["expected_sha256"] == runtime.MODEL_SHA256
    manifest.write_text('[]')
    assert runtime.get_model_info()["expected_sha256"] == runtime.MODEL_SHA256
