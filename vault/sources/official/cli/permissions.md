---
title: "Claude Code パーミッションモデル"
type: source
confidence: 0.7
sources: []
last_updated: 2026-05-06
stale: false
tags: [cli, permissions, security]
source_url: "https://code.claude.com/docs/ja/permissions"
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
Claude Code は危険なコマンドや書込み操作に対し都度ユーザーへ確認するパーミッションモデルを採用する。`settings.json` の `permissions.allow` / `permissions.deny` でツール名と引数パターン（例: `Bash(git status)`、`Edit(src/**/*.ts)`）を粒度高く宣言でき、deny は allow より優先される。対話中の `/permissions` でセッション内の一時許可や永続化を選択でき、`Bash(git diff)` と `Bash(git diff:*)` のように引数有無を厳密に区別する。
<!-- AUTO:END -->

## 公式ドキュメント
→ https://code.claude.com/docs/ja/permissions
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）
