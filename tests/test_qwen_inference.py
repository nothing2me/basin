"""Automated tests for embedded Qwen runtime, model discovery, and tool calling."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from basin_core.qwen_runtime import (
    get_model_info,
    resolve_model_path,
    _extract_json_tool_calls,
    QwenInferenceClient,
)
from basin_core.tools import TOOL_REGISTRY


def test_model_info_structure():
    """Verify runtime metadata structure and pinned configuration."""
    info = get_model_info()
    assert "installed" in info
    assert "runtime_version" in info
    assert info["quantization"] == "Q4_K_M"
    assert info["expected_sha256"] == "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
    assert info["model_name"] == "qwen2.5-3b-instruct-q4_k_m.gguf"
    assert info["context_tokens"] == 8192
    assert info["max_output_tokens"] == 1024


def test_tool_call_json_extraction():
    """Test extracting tool calls formatted as JSON markdown blocks."""
    sample_text = (
        "I will analyze the drought stress for that scenario.\n\n"
        "```json\n"
        '{"name": "check_concurrence", "parameters": {"scenario_id": "B-001"}}\n'
        "```\n"
        "Executing analysis..."
    )
    calls = _extract_json_tool_calls(sample_text)
    assert calls is not None
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "check_concurrence"
    args = json.loads(calls[0]["function"]["arguments"])
    assert args["scenario_id"] == "B-001"


def test_qwen_native_tool_call_double_braces():
    """Test extracting tool calls formatted as Qwen <tool_call> tags with double braces."""
    sample_text = (
        "Here is the concurrence check:\n"
        "<tool_call>\n"
        '{{"name": "check_concurrence", "arguments": {"scenario_id": "B-001"}}}\n'
        "</tool_call>"
    )
    calls = _extract_json_tool_calls(sample_text)
    assert calls is not None
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "check_concurrence"
    args = json.loads(calls[0]["function"]["arguments"])
    assert args["scenario_id"] == "B-001"


def test_tool_call_alternate_keys():
    """Test extracting tool calls with action/arguments format."""
    sample_text = (
        "```json\n"
        '{"tool": "explain_ranking", "arguments": {"scenario_id": "B-002"}}\n'
        "```"
    )
    calls = _extract_json_tool_calls(sample_text)
    assert calls is not None
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "explain_ranking"
    args = json.loads(calls[0]["function"]["arguments"])
    assert args["scenario_id"] == "B-002"


def test_tool_call_extraction_none_on_plain_text():
    """Plain conversational text should not extract tool calls."""
    plain = "Scenario B-001 has a 240 mm shortfall over 180 days."
    assert _extract_json_tool_calls(plain) is None


@pytest.mark.skipif(resolve_model_path() is None, reason="Qwen GGUF model weights not yet downloaded")
def test_real_qwen_inference():
    """Exercise real embedded inference through the application-owned worker process."""
    model_path = resolve_model_path()
    assert model_path is not None and model_path.exists()

    client = QwenInferenceClient(model_path)
    try:
        assert client.status == "ready"
        messages = [
            {"role": "system", "content": "You are a concise water resource assistant."},
            {"role": "user", "content": "Name three Texas reservoirs in 5 words."},
        ]
        resp = client.generate(messages, max_tokens=60, temperature=0.1)
        assert resp["type"] == "done"
        assert resp["tokens_generated"] > 0
        assert len(resp["content"]) > 0
        assert resp["tokens_per_sec"] > 0
    finally:
        client.shutdown()
