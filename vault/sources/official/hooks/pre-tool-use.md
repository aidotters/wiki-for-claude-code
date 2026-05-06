---
title: "PreToolUse フック"
type: source
confidence: 0.6
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
status: reviewed
auto_section_managed: false
---

<!--
Last verified: 2026-05-06 against code.claude.com/docs/ja/hooks.
PreToolUse がツール実行直前に発火しブロック可能、matcher でツール名指定、command handler 経由で
シェル実行できる点は現行ドキュメントと整合。Claude Code では exit 2 が「ブロッキングエラー」規約で
ある点は Phase 2 で本文に補強予定。
-->

## 概要 (要約)
PreToolUse は、Claude Code がツール（Bash, Edit, Write 等）を実行する直前に発火するフックです。ツール名と引数を受け取り、シェルコマンドを実行できます。コマンドが非ゼロを返すとツール実行は中止される場合があり、パーミッション制御や禁止コマンド検出のゲートとして機能します。`matcher` でツール名にパターンマッチし、対象を絞れます。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks#pretooluse
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### 主な利用例

- **書込み禁止ガード**: `Edit` / `Write` ツールに対して、保護対象パスへの変更を拒否
- **コマンドブロックリスト**: `Bash` の引数をパースし、`rm -rf /`、`sudo`、`curl | sh` 等を阻止
- **監査ログ**: 全ツール実行を JSONL で記録、後で振り返り可能に

### マッチャ例

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "scripts/audit.sh" }] }
    ]
  }
}
```

### ハマりどころ

- `matcher` は文字列 / 正規表現の両方を受けるが、エスケープ規約に注意
- フック内で標準入力（JSON）を読む場合、ツールの引数情報が渡される
- 同一マッチャに複数フックを並べた場合、上から順に実行される

### 関連ページ

- 概念: [[overview]]
- 反対側: [[post-tool-use]]
- セッション停止: [[stop]]
- パーミッション制御: [[../cli/permissions]]
