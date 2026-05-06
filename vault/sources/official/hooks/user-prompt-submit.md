---
title: "UserPromptSubmit フック"
type: source
confidence: 0.6
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
status: reviewed
auto_section_managed: false
---

<!--
Last verified: 2026-05-06 against code.claude.com/docs/ja/hooks.
ユーザープロンプト送信時の前処理としての用途、stdout を追加コンテキストに使う点は現行ドキュメントと
整合。ブロッキング規約は exit 2 に統一されている点は Phase 2 で「exit code」節を補強予定。
sessionTitle 等の hookSpecificOutput キー機能は別記事化候補。
-->

## 概要 (要約)
UserPromptSubmit はユーザーがプロンプトを送信した直後、エージェントが解釈する前に発火するフックです。プロンプトに対する前処理（自動的なコンテキスト追加、機微情報の検出と削除、定型文の挿入）を実装できます。出力は標準出力で Claude に渡される追加コンテキストとして扱われ、複数フックの結果を結合できます。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks#userpromptsubmit
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### 典型的な利用例

- **環境情報の自動付与**: `git rev-parse HEAD` の結果や直近のテスト結果を毎回プロンプトに添える
- **PII フィルタ**: メールアドレス・電話番号等を含むプロンプトを警告 / 削除
- **定型「役割」プロンプトの注入**: 特定リポジトリでは常に「Pythonist として答えよ」を先頭に挿入

### exit code

- 非ゼロを返した場合、プロンプト送信自体が中断される実装が一般的（ガードレール用途）

### 注意点

- ユーザー体験への影響が大きい（毎回発火するため）。実行時間は最低限に
- プロンプトを書き換える場合、ユーザーが意図しない変更とならないよう透明性を確保

### 関連ページ

- 概念: [[overview]]
- 関連: [[pre-tool-use]]
