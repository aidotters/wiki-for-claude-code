---
title: "Claude Code の設定 (settings.json)"
type: source
confidence: 0.7
sources: []
last_updated: 2026-05-06
stale: false
tags: [cli, configuration, settings]
source_url: "https://code.claude.com/docs/ja/settings"
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
Claude Code の設定はユーザー / プロジェクト / ローカルの 3 階層を持つ JSON ファイルで構成される。`~/.claude/settings.json`（ユーザー全体）、`.claude/settings.json`（プロジェクト共有、Git 管理）、`.claude/settings.local.json`（ローカル個別、Git 除外）の順で読み込まれ、後の階層が前を上書きする。permissions / hooks / env 変数 / 既定モデル / status line / MCP サーバーなどを宣言的に定義でき、チーム共有の再現性と個別環境のカスタマイズを両立できる。
<!-- AUTO:END -->

## 公式ドキュメント
→ https://code.claude.com/docs/ja/settings
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）
