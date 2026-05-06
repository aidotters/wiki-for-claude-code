---
title: "PostToolUse フック"
type: source
confidence: 0.6
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
status: reviewed
auto_section_managed: false
---

<!--
Last verified: 2026-05-06 against code.claude.com/docs/ja/hooks.
PostToolUse はツール実行直後に発火し品質ゲート（自動 lint/format、テスト等）に有用な点は現行
ドキュメントと整合。PostToolUseFailure / PostToolBatch といった派生イベントは Phase 2 で別記事
として切り出すか、本記事を概念補完するかは要検討。
-->

## 概要 (要約)
PostToolUse は、Claude Code がツール実行を完了した直後に発火するフックです。ツールの結果（標準出力やエラー）を後処理に渡せます。代表的な用途は、ファイル編集後の自動 lint / format、テスト実行、コミット前のスモークチェックです。実行が保証されるため、Claude のプロンプト指示よりも信頼性の高い「品質ゲート」を構築できます。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks#posttooluse
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### 代表的な利用パターン

- **編集後の自動整形**: `Edit` / `Write` の matcher を設定し、`prettier --write` や `ruff format` を実行
- **保存後テスト**: 関連テストを `pytest -k <近傍ファイル>` で軽く回す
- **CI 失敗の事前検知**: ローカルで `mypy` や `eslint` を走らせる

### exit code の扱い

- 非ゼロでも Claude Code 側のセッションは継続する（PreToolUse と異なる）
- ただしユーザーへの通知メッセージとして表示される実装になっているため、品質失敗を気付かせやすい

### 注意点

- 実行時間が長すぎるとセッションの体感速度が下がる
- 全ツール対象の matcher を設定すると、`Read` 等の軽量ツールでも発火し過剰に回る

### 関連ページ

- 概念: [[overview]]
- 対: [[pre-tool-use]]
