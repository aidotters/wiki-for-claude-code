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
status: reviewed
auto_section_managed: false
---

<!--
Last verified: 2026-05-06 against code.claude.com/docs/ja/permissions.
permissions.allow / deny / Bash / Edit パターン記法、対話中の /permissions、deny 優先などの主要記述は
現行ドキュメントと整合。published 化は Phase 2 で auto モード仕様の最新化後に行う。
-->

## 概要 (要約)
Claude Code は危険なコマンドや書込み操作に対して都度ユーザー確認を求めるパーミッションモデルを採用しています。settings.json の `permissions.allow` で常時許可するコマンドや書込み対象を、`permissions.deny` で禁止対象を宣言できます。許可粒度はツール名（`Bash(npm install)` 等）やパスパターン（`Edit(src/**)` 等）で指定でき、対話中の `/permissions` で一時的な許可も可能です。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/permissions
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### 主な記法例

```jsonc
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff:*)",
      "Edit(src/**/*.ts)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(sudo:*)"
    ]
  }
}
```

### 対話中の `/permissions`

- 直近のプロンプトを許可対象に追加
- セッション内のみ・永続化（settings.json への追記）の選択可

### Auto モードとの関係

`/auto` モード起動時はパーミッション確認の頻度を下げる挙動になるが、危険操作（force push, rm -rf 等）は明示確認のままが原則。

### ハマりどころ

- `Bash(git diff)` と `Bash(git diff:*)` は厳密に区別される（前者は引数なしのみ許可）
- `Edit` の glob パターンは settings.json のリポジトリルート相対
- deny の方が allow より優先されるため、広く許可した上で危険のみ deny する設計が安全

### 関連ページ

- 設定: [[configuration]]
- フック: [[../hooks/pre-tool-use]]
