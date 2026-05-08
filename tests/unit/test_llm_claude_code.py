"""ClaudeCodeBackend のユニットテスト（Phase 2-A 後半 / ADR-018）。

実 `claude` CLI / `claude-agent-sdk` 呼び出しはせず、モッククライアントで挙動を検証する。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from agent.errors import ConfigurationError, LLMInvocationError
from agent.orchestration.llm import (
    DEFAULT_MODEL,
    ClaudeCodeBackend,
    LLMResult,
    _parse_claude_code_response,
    make_backend,
)

# --- mock SDK ヘルパ ---------------------------------------------------------

@dataclass
class _FakeTextBlock:
    text: str


@dataclass
class _FakeAssistantMessage:
    content: list[Any]


@dataclass
class _FakeResultMessage:
    usage: dict[str, Any] | None = None
    is_error: bool = False
    subtype: str = "success"
    errors: list[str] | None = None


# isinstance ではなく type(x).__name__ で分岐するので、クラス名を合わせる
_FakeAssistantMessage.__name__ = "AssistantMessage"
_FakeResultMessage.__name__ = "AssistantMessage"  # 後で個別に再設定
_FakeResultMessage.__name__ = "ResultMessage"


class _FakeOptions:
    def __init__(
        self,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        max_turns: int | None = None,
    ) -> None:
        self.system_prompt = system_prompt
        self.model = model
        self.max_turns = max_turns


class _FakeSDK:
    """`claude_agent_sdk` の最小モック。`ClaudeAgentOptions` と `query` のみ提供。"""

    ClaudeAgentOptions = _FakeOptions

    def __init__(
        self,
        *,
        messages: list[Any] | None = None,
        side_effect: list[list[Any] | Exception] | None = None,
    ) -> None:
        # 単発レスポンス用 / リトライ検証用の両対応
        self._messages = messages
        self._side_effect = list(side_effect) if side_effect is not None else None
        self.captured_options: list[_FakeOptions] = []
        self.captured_prompts: list[str] = []

    def query(
        self,
        *,
        prompt: str,
        options: _FakeOptions | None = None,
    ) -> AsyncIterator[Any]:
        self.captured_prompts.append(prompt)
        if options is not None:
            self.captured_options.append(options)

        if self._side_effect is not None:
            current = self._side_effect.pop(0)
            if isinstance(current, Exception):
                async def _raise() -> AsyncIterator[Any]:
                    raise current
                    yield  # pragma: no cover
                return _raise()
            messages = current
        else:
            messages = self._messages or []

        async def _gen() -> AsyncIterator[Any]:
            for m in messages:
                yield m

        return _gen()


def _make_messages(text: str = "ok", *, usage: dict[str, Any] | None = None) -> list[Any]:
    return [
        _FakeAssistantMessage(content=[_FakeTextBlock(text=text)]),
        _FakeResultMessage(usage=usage),
    ]


# --- テストクラス ------------------------------------------------------------

class TestClaudeCodeBackendConfig:
    def test_default_model(self) -> None:
        backend = ClaudeCodeBackend(client=_FakeSDK(messages=[]))
        assert backend.model == DEFAULT_MODEL

    def test_model_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WIKI_LLM_MODEL", "claude-opus-4-7")
        backend = ClaudeCodeBackend(client=_FakeSDK(messages=[]))
        assert backend.model == "claude-opus-4-7"

    def test_anthropic_api_key_not_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # ANTHROPIC_API_KEY 未設定でも __init__ は成功する
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        backend = ClaudeCodeBackend(client=_FakeSDK(messages=[]))
        assert backend is not None

    def test_missing_claude_binary_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # client 未注入経路で shutil.which が None を返すと ConfigurationError
        import agent.orchestration.llm as llm_module

        monkeypatch.setattr(llm_module.shutil, "which", lambda _: None)
        with pytest.raises(ConfigurationError, match="claude /login"):
            ClaudeCodeBackend()

    def test_present_claude_binary_does_not_raise(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import agent.orchestration.llm as llm_module

        monkeypatch.setattr(llm_module.shutil, "which", lambda _: "/usr/local/bin/claude")
        # claude_agent_sdk が import できる前提（uv add 済み）
        backend = ClaudeCodeBackend()
        assert backend.model == DEFAULT_MODEL


class TestClaudeCodeBackendInvoke:
    def test_invoke_returns_text_and_usage(self) -> None:
        sdk = _FakeSDK(
            messages=_make_messages(
                text="hello world",
                usage={
                    "input_tokens": 20,
                    "output_tokens": 8,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 10,
                },
            )
        )
        backend = ClaudeCodeBackend(client=sdk)
        result = backend.invoke(system="sys", prompt="user")
        assert isinstance(result, LLMResult)
        assert result.text == "hello world"
        assert result.usage.input_tokens == 20
        assert result.usage.output_tokens == 8
        assert result.usage.cache_read_input_tokens == 10

    def test_invoke_passes_system_prompt_and_model(self) -> None:
        sdk = _FakeSDK(messages=_make_messages())
        backend = ClaudeCodeBackend(model="claude-sonnet-4-6", client=sdk)
        backend.invoke(system="my-sys", prompt="user")
        assert len(sdk.captured_options) == 1
        opts = sdk.captured_options[0]
        assert opts.system_prompt == "my-sys"
        assert opts.model == "claude-sonnet-4-6"
        assert opts.max_turns == 1

    def test_invoke_with_empty_system_uses_none(self) -> None:
        sdk = _FakeSDK(messages=_make_messages())
        backend = ClaudeCodeBackend(client=sdk)
        backend.invoke(system="", prompt="user")
        assert sdk.captured_options[0].system_prompt is None

    def test_invoke_cache_system_is_noop(self) -> None:
        sdk = _FakeSDK(messages=_make_messages())
        backend = ClaudeCodeBackend(client=sdk)
        # cache_system=True / False で挙動が変わらないこと（claude-code は noop）
        r1 = backend.invoke(system="s", prompt="p", cache_system=True)
        r2 = backend.invoke(system="s", prompt="p", cache_system=False)
        assert r1.text == r2.text

    def test_invoke_retries_once_on_failure(self) -> None:
        sdk = _FakeSDK(
            side_effect=[
                RuntimeError("transient"),
                _make_messages(text="recovered"),
            ]
        )
        backend = ClaudeCodeBackend(client=sdk)
        result = backend.invoke(system="sys", prompt="p")
        assert result.text == "recovered"

    def test_invoke_raises_after_second_failure(self) -> None:
        sdk = _FakeSDK(
            side_effect=[
                RuntimeError("rate limit"),
                RuntimeError("rate limit again"),
            ]
        )
        backend = ClaudeCodeBackend(client=sdk)
        with pytest.raises(LLMInvocationError, match="リトライ後"):
            backend.invoke(system="sys", prompt="p")

    def test_invoke_raises_on_is_error_result(self) -> None:
        sdk = _FakeSDK(
            side_effect=[
                [_FakeResultMessage(is_error=True, subtype="error", errors=["boom"])],
                [_FakeResultMessage(is_error=True, subtype="error", errors=["boom"])],
            ]
        )
        backend = ClaudeCodeBackend(client=sdk)
        with pytest.raises(LLMInvocationError):
            backend.invoke(system="sys", prompt="p")

    def test_generate_returns_text(self) -> None:
        sdk = _FakeSDK(messages=_make_messages(text="from generate"))
        backend = ClaudeCodeBackend(client=sdk)
        assert backend.generate("hello") == "from generate"


class TestParseClaudeCodeResponse:
    def test_with_full_usage(self) -> None:
        result = _parse_claude_code_response(
            text="hi",
            usage={
                "input_tokens": 5,
                "output_tokens": 3,
                "cache_creation_input_tokens": 1,
                "cache_read_input_tokens": 2,
            },
        )
        assert result.text == "hi"
        assert result.usage.input_tokens == 5
        assert result.usage.output_tokens == 3
        assert result.usage.cache_creation_input_tokens == 1
        assert result.usage.cache_read_input_tokens == 2

    def test_with_missing_usage(self) -> None:
        result = _parse_claude_code_response(text="hi", usage=None)
        assert result.text == "hi"
        assert result.usage.input_tokens == 0
        assert result.usage.cache_read_input_tokens == 0
        assert result.usage.cache_hit_rate == 0.0

    def test_with_partial_usage(self) -> None:
        result = _parse_claude_code_response(
            text="x", usage={"input_tokens": 7}
        )
        assert result.usage.input_tokens == 7
        assert result.usage.output_tokens == 0


class TestMakeBackendClaudeCode:
    def test_claude_code_branch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import agent.orchestration.llm as llm_module

        monkeypatch.setenv("WIKI_LLM_BACKEND", "claude-code")
        monkeypatch.setattr(llm_module.shutil, "which", lambda _: "/usr/local/bin/claude")
        backend = make_backend()
        assert isinstance(backend, ClaudeCodeBackend)

    def test_claude_code_missing_binary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import agent.orchestration.llm as llm_module

        monkeypatch.setenv("WIKI_LLM_BACKEND", "claude-code")
        monkeypatch.setattr(llm_module.shutil, "which", lambda _: None)
        with pytest.raises(ConfigurationError, match="claude /login"):
            make_backend()

    def test_unknown_backend_message_includes_three_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("WIKI_LLM_BACKEND", "garbage")
        with pytest.raises(ConfigurationError) as exc_info:
            make_backend()
        msg = str(exc_info.value)
        assert "stub" in msg
        assert "anthropic" in msg
        assert "claude-code" in msg

    def test_claude_code_does_not_require_anthropic_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import agent.orchestration.llm as llm_module

        monkeypatch.setenv("WIKI_LLM_BACKEND", "claude-code")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr(llm_module.shutil, "which", lambda _: "/usr/local/bin/claude")
        # ConfigurationError が出ないこと（API キー欠落で失敗しない）
        backend = make_backend()
        assert isinstance(backend, ClaudeCodeBackend)


# 既存テストとの統合確認: MagicMock を直接 client に渡すケースもサポート
class TestClientInjection:
    def test_magicmock_client_accepted(self) -> None:
        sdk = MagicMock()
        backend = ClaudeCodeBackend(client=sdk)
        assert backend._client is sdk  # type: ignore[attr-defined]
