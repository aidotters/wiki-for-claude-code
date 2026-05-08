"""LLM クライアントの抽象化。Phase 2-A から Anthropic SDK 実装を追加、Phase 2-A 後半で Claude Code 経由を追加。

Backend 切替は環境変数で行う:

- `WIKI_LLM_BACKEND=stub` (既定): 決定的スタブ。`StubLLMClient` を返す
- `WIKI_LLM_BACKEND=anthropic`: 実 SDK 経由（API キー必須・従量課金）。`AnthropicBackend` を返す
- `WIKI_LLM_BACKEND=claude-code`: `claude-agent-sdk` 経由で Claude Code (Max プラン) を呼ぶ。`ClaudeCodeBackend` を返す
- `WIKI_LLM_MODEL` (任意): 既定 `claude-sonnet-4-6`
- `ANTHROPIC_API_KEY` (`anthropic` backend でのみ必須): API キー

prompt caching は system プロンプトに `cache_control: ephemeral` を付与して有効化する（`anthropic` backend のみ）。
`claude-code` backend では caching は Claude Code 内部に委譲され、`cache_system` は noop となる。
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from typing import Any, Protocol

from agent.errors import ConfigurationError, LLMInvocationError

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096


@dataclass
class LLMUsage:
    """1 回の LLM 呼び出しのトークン使用量・キャッシュ統計。"""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @property
    def cache_hit_rate(self) -> float:
        """cache hit 率 = cache_read / (cache_read + cache_creation + 普通の input)。"""
        total = (
            self.input_tokens
            + self.cache_creation_input_tokens
            + self.cache_read_input_tokens
        )
        if total == 0:
            return 0.0
        return self.cache_read_input_tokens / total


@dataclass
class LLMResult:
    """LLM 呼び出しの結果。"""

    text: str
    usage: LLMUsage = field(default_factory=LLMUsage)


class LLMClient(Protocol):
    """`generate(prompt) -> str` を提供する従来のインターフェイス。後方互換のため維持。"""

    def generate(self, prompt: str) -> str: ...


class LLMBackend(Protocol):
    """Phase 2-A 以降のバックエンド抽象。`invoke` で usage 込みで返す。"""

    def invoke(
        self,
        *,
        system: str,
        prompt: str,
        cache_system: bool = True,
    ) -> LLMResult: ...


class StubLLMClient:
    """テスト・開発用の決定的スタブ。

    入力プロンプトのハッシュとは無関係に、固定の `source` 種別記事を返す。
    `regenerate` の冪等性検証では同じ入力に対して同じ出力を返す必要がある。

    `LLMClient` および `LLMBackend` の両プロトコルを満たす。
    """

    def __init__(self, fixed_response: str | None = None) -> None:
        self.fixed_response = fixed_response

    def generate(self, prompt: str) -> str:
        if self.fixed_response is not None:
            return self.fixed_response
        return _DEFAULT_STUB_RESPONSE

    def invoke(
        self,
        *,
        system: str,
        prompt: str,
        cache_system: bool = True,
    ) -> LLMResult:
        text = self.generate(prompt)
        return LLMResult(text=text, usage=LLMUsage())


class AnthropicBackend:
    """Anthropic SDK 経由のバックエンド。Phase 2-A 実装。

    - `ANTHROPIC_API_KEY` 必須（未設定時は `ConfigurationError`）
    - prompt caching: system プロンプトに `cache_control: ephemeral` を付与
    - リトライ: API 呼び出し失敗時に 1 回リトライ後 `LLMInvocationError`
    """

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        client: Any = None,
    ) -> None:
        self.model = model or os.environ.get("WIKI_LLM_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens
        if client is not None:
            # テスト用にモッククライアントを注入可
            self._client = client
            return

        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY が設定されていません。`.env` を確認してください。"
            )
        # 遅延 import で stub バックエンド時の依存を最小化
        from anthropic import Anthropic

        self._client = Anthropic(api_key=resolved_key)

    def invoke(
        self,
        *,
        system: str,
        prompt: str,
        cache_system: bool = True,
    ) -> LLMResult:
        system_blocks: list[dict[str, Any]] = [{"type": "text", "text": system}]
        if cache_system and system:
            system_blocks[0]["cache_control"] = {"type": "ephemeral"}

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system_blocks,
                    messages=[{"role": "user", "content": prompt}],
                )
                return _parse_response(response)
            except Exception as e:  # noqa: BLE001 — SDK 例外を一括捕捉して 1 回リトライ
                last_error = e
                if attempt == 0:
                    continue
                raise LLMInvocationError(
                    f"Anthropic SDK 呼び出しに失敗（リトライ後）: {e}"
                ) from last_error

        # 到達不可だが型チェック用
        raise LLMInvocationError("unreachable")  # pragma: no cover

    # 後方互換: `LLMClient.generate` を実装することで既存呼び出しからも使える
    def generate(self, prompt: str) -> str:
        result = self.invoke(system="", prompt=prompt, cache_system=False)
        return result.text


def _parse_response(response: Any) -> LLMResult:
    """Anthropic SDK のレスポンスから text と usage を抽出する。"""
    text_parts: list[str] = []
    for block in getattr(response, "content", []):
        # SDK 型によって `block.text` または `block["text"]` の両方ありうる
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            text_parts.append(text)

    usage_obj = getattr(response, "usage", None)
    usage = LLMUsage()
    if usage_obj is not None:
        usage.input_tokens = getattr(usage_obj, "input_tokens", 0) or 0
        usage.output_tokens = getattr(usage_obj, "output_tokens", 0) or 0
        usage.cache_creation_input_tokens = (
            getattr(usage_obj, "cache_creation_input_tokens", 0) or 0
        )
        usage.cache_read_input_tokens = (
            getattr(usage_obj, "cache_read_input_tokens", 0) or 0
        )

    return LLMResult(text="".join(text_parts), usage=usage)


class ClaudeCodeBackend:
    """`claude-agent-sdk` 経由で Claude Code (Max プラン) を呼ぶバックエンド。

    - 起動時に `claude` バイナリの PATH 存在を確認（フェイルファスト）
    - `claude-agent-sdk.query` は async-only のため、内部で `asyncio.run` で同期化
    - prompt caching は Claude Code 内部に委譲（`cache_system` フラグは noop）
    - リトライ: 1 回失敗時にリトライ、再失敗で `LLMInvocationError`
    - SDK 例外は `LLMInvocationError` にラップ（exit code 3）

    認証情報は `~/.claude/` に格納された Claude Code の認証情報を SDK が読む。
    `ANTHROPIC_API_KEY` は読まない（`anthropic` バックエンド向け）。
    """

    def __init__(
        self,
        *,
        model: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        client: Any = None,
    ) -> None:
        self.model = model or os.environ.get("WIKI_LLM_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens
        if client is not None:
            # テスト用にモック sdk モジュール / async query 関数を注入可
            self._client = client
            return

        if shutil.which("claude") is None:
            raise ConfigurationError(
                "claude バイナリが PATH にありません。`claude /login` を実行して"
                "Claude Code をセットアップしてください。"
            )
        # 遅延 import（stub / anthropic バックエンド時に依存を読み込まないため）
        import claude_agent_sdk

        self._client = claude_agent_sdk

    def invoke(
        self,
        *,
        system: str,
        prompt: str,
        cache_system: bool = True,
    ) -> LLMResult:
        # cache_system は claude-code 経由では noop（Claude Code 内部に委譲）
        del cache_system

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                return self._run_query(system=system, prompt=prompt)
            except Exception as e:  # noqa: BLE001 — SDK 例外を一括捕捉して 1 回リトライ
                last_error = e
                if attempt == 0:
                    continue
                raise LLMInvocationError(
                    f"claude-agent-sdk 呼び出しに失敗（リトライ後）: {e}"
                ) from last_error

        raise LLMInvocationError("unreachable")  # pragma: no cover

    def _run_query(self, *, system: str, prompt: str) -> LLMResult:
        import asyncio

        return asyncio.run(self._aquery(system=system, prompt=prompt))

    async def _aquery(self, *, system: str, prompt: str) -> LLMResult:
        options = self._client.ClaudeAgentOptions(
            system_prompt=system if system else None,
            model=self.model,
            max_turns=1,
        )
        text_parts: list[str] = []
        usage_dict: dict[str, Any] | None = None
        async for message in self._client.query(prompt=prompt, options=options):
            class_name = type(message).__name__
            if class_name == "AssistantMessage":
                for block in getattr(message, "content", []) or []:
                    text = getattr(block, "text", None)
                    if text:
                        text_parts.append(text)
            elif class_name == "ResultMessage":
                if getattr(message, "is_error", False):
                    raise LLMInvocationError(
                        f"claude-agent-sdk が is_error=True を返却: "
                        f"subtype={getattr(message, 'subtype', None)!r} "
                        f"errors={getattr(message, 'errors', None)!r}"
                    )
                usage_dict = getattr(message, "usage", None)

        return _parse_claude_code_response(text="".join(text_parts), usage=usage_dict)

    # 後方互換: `LLMClient.generate` を実装することで既存呼び出しからも使える
    def generate(self, prompt: str) -> str:
        result = self.invoke(system="", prompt=prompt, cache_system=False)
        return result.text


def _parse_claude_code_response(
    *, text: str, usage: dict[str, Any] | None
) -> LLMResult:
    """`claude-agent-sdk` のレスポンスから `LLMResult` を組み立てる。

    `usage` が不存在 / フィールド欠落の場合は 0 を埋める（`cache_hit_rate` は 0.0 を返す）。
    """
    llm_usage = LLMUsage()
    if usage:
        llm_usage.input_tokens = int(usage.get("input_tokens", 0) or 0)
        llm_usage.output_tokens = int(usage.get("output_tokens", 0) or 0)
        llm_usage.cache_creation_input_tokens = int(
            usage.get("cache_creation_input_tokens", 0) or 0
        )
        llm_usage.cache_read_input_tokens = int(
            usage.get("cache_read_input_tokens", 0) or 0
        )
    return LLMResult(text=text, usage=llm_usage)


def make_backend() -> LLMBackend:
    """環境変数 `WIKI_LLM_BACKEND` に基づいてバックエンドを生成する。"""
    backend_name = os.environ.get("WIKI_LLM_BACKEND", "stub").lower()
    if backend_name == "anthropic":
        return AnthropicBackend()
    if backend_name == "claude-code":
        return ClaudeCodeBackend()
    if backend_name == "stub":
        return StubLLMClient()
    raise ConfigurationError(
        f"未知の WIKI_LLM_BACKEND: {backend_name!r}"
        "（`stub` / `anthropic` / `claude-code` のいずれかを指定）"
    )


_DEFAULT_STUB_RESPONSE = """---
title: "Stub Source"
type: source
confidence: 0.8
sources: []
last_updated: 2026-05-05
stale: false
tags: [stub]
source_url: "https://docs.claude.com/claude-code/stub"
fetched_at: "2026-05-05T10:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: false
status: draft
auto_section_managed: false
---

## 概要 (要約)
スタブ要約。実 LLM 統合時に置き換わる。

## 公式ドキュメント
→ https://docs.claude.com/claude-code/stub
（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)
スタブ補足。冪等性確認用に固定文字列。
"""
