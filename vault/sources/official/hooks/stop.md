---
title: "Stop フック"
type: source
confidence: 0.7
sources: []
last_updated: 2026-05-06
stale: false
tags: [hooks, stop]
source_url: "https://code.claude.com/docs/ja/hooks#stop"
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
Stop フックは Claude Code セッションが停止する際に発火する。停止理由（ユーザーによる中断・エージェントの自然完了・エラー）に応じて、Slack / メール通知、成果物の集約 push、CI トリガー、一時ファイルのクリーンアップなどを実行できる。SubagentStop はサブエージェント停止時のみ発火する別イベントで、Stop と区別され、サブエージェント単体の結果を集約する用途に適する。
<!-- AUTO:END -->

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks#stop
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）
