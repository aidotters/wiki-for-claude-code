---
title: "Claude Code の設定 (settings.json)"
type: source
confidence: 0.6
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
status: reviewed
auto_section_managed: false
---

<!--
Last verified: 2026-05-06 against code.claude.com/docs/ja/settings.
高レベルの記述（settings.json の3階層、permissions/hooks/env/model 等の主要キー）は現行ドキュメントと
整合する。published 化は Phase 2 で実 LLM 再生成 + 個別キー仕様の精査後に行う。
-->

## 概要 (要約)
Claude Code の設定はユーザー / プロジェクト / ローカルの3階層で管理され、`~/.claude/settings.json`（ユーザー）、`.claude/settings.json`（プロジェクト共有）、`.claude/settings.local.json`（個別環境）の順で読み込まれます。許可ツール、permissions、hooks、env 変数、status line、MCP サーバー等を宣言的に定義でき、後の階層が前を上書きします。プロジェクトの再現性とチーム共有のため、`.claude/settings.json` を Git で管理するのが基本です。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/settings
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### 設定ファイルの階層

| ファイル | スコープ | 共有 |
|---------|---------|------|
| `~/.claude/settings.json` | ユーザー全体 | × |
| `.claude/settings.json` | プロジェクト共通 | ○（Git 管理） |
| `.claude/settings.local.json` | 個別環境 | ×（Git 除外） |

### よく使うキー

- `permissions.allow` / `permissions.deny`: Bash コマンドや書込み対象パスの許可/拒否
- `hooks`: PreToolUse / PostToolUse / Stop 等のフック定義（[[../hooks/overview]] 参照）
- `env`: セッションに渡す環境変数
- `model`: 既定モデル（Opus / Sonnet 等）

### ハマりどころ

- ローカル設定（`.local.json`）で機微情報を扱い、Git 共有用と分離する
- 階層順は「下層が上書き」なので、共通禁止 + 個別許可の構造が組みやすい
- JSON 構文エラーがあると起動時に静かに無視されることがある

### 関連ページ

- インストール: [[installation]]
- 起動と操作: [[basic-usage]]
- フック: [[../hooks/overview]]
