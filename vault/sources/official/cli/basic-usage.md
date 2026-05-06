---
title: "Claude Code 基本的な使い方"
type: source
confidence: 0.6
sources: []
last_updated: 2026-05-06
stale: false
tags: [cli, basic-usage]
source_url: "https://code.claude.com/docs/ja/quickstart"
fetched_at: "2026-05-06T01:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: true
status: reviewed
auto_section_managed: false
---

<!--
Last verified: 2026-05-06 against code.claude.com/docs/ja/quickstart.
高レベルの記述（claude 起動、/help, /clear, /compact, /init, /review, --continue, --resume）は
現行ドキュメントと整合する。published 化は Phase 2 で実 LLM 再生成 + 内容差分の精査後に行う。
-->

## 概要 (要約)
Claude Code は対話的なコーディングエージェントで、プロジェクトのルートで `claude` を起動するとセッションが始まります。自然言語でコードの読解・編集・実行を依頼でき、ツール（Bash、Read、Write、Edit）を介してリポジトリを操作します。`/help` でコマンド一覧、`/clear` でコンテキストクリア、`/compact` でコンテキスト圧縮ができ、エージェント的な長期作業にも対応します。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/quickstart
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### 起動とセッション管理

- 起動: `claude`（プロジェクトルートで実行を推奨）
- 既存セッションの再開: `claude --continue` or `claude -c`
- 過去セッション選択: `claude --resume`

### よく使う組込みコマンド

| コマンド | 用途 |
|---------|------|
| `/help` | コマンド一覧と簡易ヘルプ |
| `/clear` | 会話履歴のクリア |
| `/compact` | コンテキスト圧縮 |
| `/init` | リポジトリ用 CLAUDE.md の初期化 |
| `/review` | PR / 差分のレビュー |

### ハマりどころ

- 大規模リポジトリでは初回の探索に時間がかかる。`CLAUDE.md` を整備すると改善
- `Bash` ツールの権限プロンプトが頻繁に出る場合、許可設定（[[configuration]]）で軽減

### 関連ページ

- インストール: [[installation]]
- 設定: [[configuration]]
- ショートカット: [[keybindings]]
