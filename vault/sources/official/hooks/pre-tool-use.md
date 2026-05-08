---
title: "PreToolUse フック"
type: source
confidence: 0.7
sources: []
last_updated: 2026-05-06
stale: false
tags: [hooks, pre-tool-use]
source_url: "https://code.claude.com/docs/ja/hooks#pretooluse"
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
PreToolUse は、Claude Code が Bash / Edit / Write などのツールを呼び出す直前に発火するフック。`matcher` でツール名のパターンを指定し、command handler 経由でシェルを実行する。Claude Code では exit code 2 が「ブロッキングエラー」として扱われ、ツール実行が中止されるため、書込み禁止ガード・コマンドブロックリスト・監査ログの埋め込みに利用できる。フック側は標準入力で対象ツール名と引数の JSON を受け取れる。
<!-- AUTO:END -->

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks#pretooluse
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）
