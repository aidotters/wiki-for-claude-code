---
title: "Hooks 概要"
type: source
confidence: 0.7
sources: []
last_updated: 2026-05-06
stale: false
tags: [hooks, overview]
source_url: "https://code.claude.com/docs/ja/hooks"
fetched_at: "2026-05-06T01:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: true
status: published
auto_section_managed: true
---

## 概要 (要約)
<!-- AUTO:START purpose=summary-1-paragraph -->
Hooks は Claude Code のライフサイクル中に発火する各種イベントで任意のコマンドを実行する仕組みで、`settings.json` に宣言的に定義する。ツール実行の前後（PreToolUse / PostToolUse）、メッセージ送信前（UserPromptSubmit）、セッション停止時（Stop / SubagentStop）など多数のフックポイントがあり、handler は command 以外に http / mcp_tool / prompt / agent といった種別を持つ。プロンプト指示と異なり実行が保証されるため、品質ゲート・監査・コンテキスト追加に適し、Claude Code では exit code 2 が「ブロッキングエラー」として扱われる規約がある。
<!-- AUTO:END -->

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）
