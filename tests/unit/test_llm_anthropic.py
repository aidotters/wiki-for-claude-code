"""AnthropicBackend のユニットテスト（Phase 2-A / A-1）。

実 API 呼び出しはせず、モッククライアントで挙動を検証する。
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from agent.errors import ConfigurationError, LLMInvocationError
from agent.orchestration.llm import (
    DEFAULT_MODEL,
    AnthropicBackend,
    LLMResult,
    LLMUsage,
    StubLLMClient,
    make_backend,
)


def _mock_response(text: str = "ok", *, input_tokens: int = 10, output_tokens: int = 5,
                   cache_creation: int = 0, cache_read: int = 0) -> Any:
    response = MagicMock()
    block = MagicMock()
    block.text = text
    response.content = [block]
    response.usage.input_tokens = input_tokens
    response.usage.output_tokens = output_tokens
    response.usage.cache_creation_input_tokens = cache_creation
    response.usage.cache_read_input_tokens = cache_read
    return response


class TestAnthropicBackendConfig:
    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
            AnthropicBackend()

    def test_default_model(self) -> None:
        client = MagicMock()
        backend = AnthropicBackend(client=client)
        assert backend.model == DEFAULT_MODEL

    def test_model_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WIKI_LLM_MODEL", "custom-model")
        client = MagicMock()
        backend = AnthropicBackend(client=client)
        assert backend.model == "custom-model"


class TestAnthropicBackendInvoke:
    def test_invoke_returns_text_and_usage(self) -> None:
        client = MagicMock()
        client.messages.create.return_value = _mock_response(
            text="hello", input_tokens=20, output_tokens=8, cache_read=10
        )
        backend = AnthropicBackend(client=client)
        result = backend.invoke(system="sys", prompt="user")
        assert result.text == "hello"
        assert result.usage.input_tokens == 20
        assert result.usage.output_tokens == 8
        assert result.usage.cache_read_input_tokens == 10

    def test_invoke_passes_cache_control_for_system(self) -> None:
        client = MagicMock()
        client.messages.create.return_value = _mock_response()
        backend = AnthropicBackend(client=client)
        backend.invoke(system="sys", prompt="p", cache_system=True)
        call_kwargs = client.messages.create.call_args.kwargs
        system_blocks = call_kwargs["system"]
        assert isinstance(system_blocks, list)
        assert system_blocks[0]["cache_control"] == {"type": "ephemeral"}

    def test_invoke_no_cache_when_disabled(self) -> None:
        client = MagicMock()
        client.messages.create.return_value = _mock_response()
        backend = AnthropicBackend(client=client)
        backend.invoke(system="sys", prompt="p", cache_system=False)
        system_blocks = client.messages.create.call_args.kwargs["system"]
        assert "cache_control" not in system_blocks[0]

    def test_invoke_retries_once_on_failure(self) -> None:
        client = MagicMock()
        client.messages.create.side_effect = [
            RuntimeError("transient"),
            _mock_response(text="recovered"),
        ]
        backend = AnthropicBackend(client=client)
        result = backend.invoke(system="sys", prompt="p")
        assert result.text == "recovered"
        assert client.messages.create.call_count == 2

    def test_invoke_raises_after_second_failure(self) -> None:
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("rate limit")
        backend = AnthropicBackend(client=client)
        with pytest.raises(LLMInvocationError, match="リトライ後"):
            backend.invoke(system="sys", prompt="p")
        assert client.messages.create.call_count == 2


class TestLLMUsage:
    def test_cache_hit_rate_zero_when_no_tokens(self) -> None:
        assert LLMUsage().cache_hit_rate == 0.0

    def test_cache_hit_rate_calculation(self) -> None:
        usage = LLMUsage(
            input_tokens=10,
            cache_creation_input_tokens=20,
            cache_read_input_tokens=70,
        )
        assert usage.cache_hit_rate == 0.7


class TestMakeBackend:
    def test_default_returns_claude_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 2026-05-08: ADR-018 で empirical PASS 後の既定値昇格。未設定時は claude-code。
        import agent.orchestration.llm as llm_module

        monkeypatch.delenv("WIKI_LLM_BACKEND", raising=False)
        monkeypatch.setattr(llm_module.shutil, "which", lambda _: "/usr/local/bin/claude")
        backend = make_backend()
        from agent.orchestration.llm import ClaudeCodeBackend

        assert isinstance(backend, ClaudeCodeBackend)

    def test_explicit_stub_returns_stub(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 既定切替後も明示指定で StubLLMClient を選択できる
        monkeypatch.setenv("WIKI_LLM_BACKEND", "stub")
        backend = make_backend()
        assert isinstance(backend, StubLLMClient)

    def test_anthropic_requires_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WIKI_LLM_BACKEND", "anthropic")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ConfigurationError):
            make_backend()

    def test_unknown_backend_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WIKI_LLM_BACKEND", "foobar")
        with pytest.raises(ConfigurationError, match="未知の"):
            make_backend()


class TestStubLLMClientCompatibility:
    def test_invoke_returns_default_response(self) -> None:
        result = StubLLMClient().invoke(system="", prompt="anything")
        assert isinstance(result, LLMResult)
        assert "Stub Source" in result.text

    def test_invoke_respects_fixed_response(self) -> None:
        stub = StubLLMClient(fixed_response="custom")
        result = stub.invoke(system="", prompt="ignored")
        assert result.text == "custom"
