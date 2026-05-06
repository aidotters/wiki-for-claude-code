---
title: "Stop フック"
type: source
confidence: 0.6
sources: []
last_updated: 2026-05-06
stale: false
tags: [hooks, stop]
source_url: "https://code.claude.com/docs/ja/hooks#stop"
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
Stop / SubagentStop の役割分離と通知用途は現行ドキュメントと整合。SessionEnd / StopFailure 等の
関連イベントは Phase 2 で別記事化、または本記事に補章を追加するか検討する。
-->

## 概要 (要約)
Stop フックは Claude Code セッションが停止する際に発火します。停止理由（ユーザーによる中断、エージェントの自然完了、エラー等）に応じて通知や後処理を実行できます。代表用途は Slack / メール通知、成果物の集約 push、CI トリガです。SubagentStop はサブエージェント終了時のみ発火する別イベントで、Stop と区別されます。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks#stop
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### 利用例

- **完了通知**: 長時間タスクの完了を Slack / Teams に投稿
- **成果物集約**: 直前の編集を git で確認し、PR 草案を作成
- **クリーンアップ**: 一時ファイルや test fixture の削除

### Stop vs SubagentStop

| 項目 | Stop | SubagentStop |
|------|------|--------------|
| 発火主体 | メインエージェント | サブエージェント |
| 受け取る情報 | セッション全体のサマリ | サブエージェント単体の結果 |
| 用途 | 全体通知 | 個別タスクの集約 |

### 注意点

- ネットワーク呼び出しを含むコマンドはタイムアウトに注意
- 失敗してもセッションは既に停止しているためリカバリ手段が限られる
- 複数フックを設定する場合は冪等な順序を意識

### 関連ページ

- 概念: [[overview]]
- 対: [[pre-tool-use]], [[post-tool-use]]
