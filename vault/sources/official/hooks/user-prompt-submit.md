---
title: "UserPromptSubmit フック"
type: source
confidence: 0.7
sources: []
last_updated: 2026-05-06
stale: false
tags: [hooks, user-prompt-submit]
source_url: "https://code.claude.com/docs/ja/hooks#userpromptsubmit"
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
UserPromptSubmit はユーザーがプロンプトを送信した直後、エージェントが解釈する前に発火するフック。フックの標準出力は Claude に渡される追加コンテキストとして扱われ、複数フックの結果が結合される。典型的な用途は環境情報の自動付与（`git rev-parse HEAD` や直近のテスト結果）、PII の検出と削除、定型「役割」プロンプトの注入などで、Claude Code では exit code 2 でプロンプト送信を中断するブロッキングガードとしても機能する。
<!-- AUTO:END -->

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks#userpromptsubmit
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）
