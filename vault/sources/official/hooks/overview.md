---
title: "Hooks 概要"
type: source
confidence: 0.5
sources: []
last_updated: 2026-05-06
stale: true
tags: [hooks, overview]
source_url: "https://code.claude.com/docs/ja/hooks"
fetched_at: "2026-05-06T01:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: true
status: draft
auto_section_managed: false
---

<!--
Content drift detected vs. code.claude.com on 2026-05-06: 現行ドキュメントは本記事の5種より多くの
hook イベントを定義（SessionStart, SessionEnd, Setup, UserPromptExpansion, StopFailure,
PostToolUseFailure, PostToolBatch, PermissionRequest, PermissionDenied, SubagentStart/Stop,
Notification, ConfigChange, CwdChanged, FileChanged, InstructionsLoaded, PreCompact/PostCompact,
Elicitation/ElicitationResult 等）。また、handler type も command 以外に http / mcp_tool / prompt /
agent が存在し、exit code は exit 2 が「ブロッキングエラー」の Claude Code 特有規約。
本記事の内容は古い表面のみで、Phase 2 で全面書き直し予定。それまで status は draft 維持。
-->

## 概要 (要約)
Claude Code の Hooks は、エージェントのライフサイクル中に発生する特定イベントで任意のコマンドを実行する仕組みです。ツール実行の前後（Pre/Post-Tool-Use）、セッション停止時（Stop）、メッセージ送信前（User-Prompt-Submit）など複数のフックポイントがあり、settings.json で宣言的に設定します。プロンプトでの指示と異なり、フックは実行が保証されるため、品質ゲートや監査ログの埋め込みに適しています。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### 主なフックポイント

| フック | 発火タイミング | 主な用途 |
|-------|--------------|---------|
| `PreToolUse` | ツール実行直前 | パーミッション制御、書込み禁止 |
| `PostToolUse` | ツール実行直後 | 自動 lint / format、テスト実行 |
| `UserPromptSubmit` | ユーザープロンプト送信前 | プロンプト整形・追記 |
| `Stop` | セッション停止時 | 通知・成果物の集約 |
| `SubagentStop` | サブエージェント停止時 | サブエージェント結果の処理 |

### 設定例（イメージ）

`settings.json` に `hooks` キーを追加し、各イベントに対するマッチャと実行コマンドを記述します。詳細は [[pre-tool-use]], [[post-tool-use]] 等を参照。

### 注意点

- フックは **シェルコマンドを実行する** ため、信頼できる範囲のみ設定すること
- 実行時間が長いと体感速度が下がる（PreToolUse は特に）
- exit code が非ゼロの場合のフォールバック挙動はフック種別で異なる

### 関連ページ

- 個別フック: [[pre-tool-use]], [[post-tool-use]], [[stop]], [[user-prompt-submit]]
- 設定方法: [[../cli/configuration]]
