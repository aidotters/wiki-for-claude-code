"""LLM クライアントの抽象化。Phase 1 ではスタブ実装のみ用意。

Phase 3 で `anthropic` SDK を使った実装に差し替える。
"""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str: ...


class StubLLMClient:
    """テスト・開発用の決定的スタブ。

    入力プロンプトのハッシュとは無関係に、固定の `source` 種別記事を返す。
    `regenerate` の冪等性検証では同じ入力に対して同じ出力を返す必要がある。
    """

    def __init__(self, fixed_response: str | None = None) -> None:
        self.fixed_response = fixed_response

    def generate(self, prompt: str) -> str:
        if self.fixed_response is not None:
            return self.fixed_response
        # プロンプト中の `{{source_url}}` 残骸が無いことを確認するための簡易応答
        return _DEFAULT_STUB_RESPONSE


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
