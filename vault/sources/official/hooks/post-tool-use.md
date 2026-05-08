---
title: "PostToolUse フック"
type: source
confidence: 0.7
sources: []
last_updated: 2026-05-06
stale: false
tags: [hooks, post-tool-use]
source_url: "https://code.claude.com/docs/ja/hooks#posttooluse"
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
PostToolUse は、Claude Code がツール実行を完了した直後に発火するフックで、ツールの結果（標準出力 / エラー）を後処理に渡せる。代表用途はファイル編集後の自動 lint / format（`prettier --write`、`ruff format` 等）、テスト実行、コミット前のスモーク検査で、CI 失敗を事前検知するゲートとしても機能する。PreToolUse と異なり exit code 非ゼロでもセッション自体は継続するが、ユーザー通知として失敗が表示される。
<!-- AUTO:END -->

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks#posttooluse
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）
