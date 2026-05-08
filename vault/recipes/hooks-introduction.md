---
title: "Hooks 入門（最小フック設定から品質ゲート構築）"
type: recipe
use_case: "Claude Code Hooks の基本概念を理解し、最初の PreToolUse / PostToolUse フックを動かして品質ゲートを構築する"
confidence: 0.7
sources:
  - "[[sources/official/hooks/overview]]"
  - "[[sources/official/hooks/pre-tool-use]]"
  - "[[sources/official/hooks/post-tool-use]]"
last_updated: 2026-05-06
stale: false
tags: [recipe, hooks, quality-gate]
reviewer: "tak"
human_edited: true
status: published
auto_section_managed: true
---

## TL;DR
<!-- AUTO:START purpose=recipe-tldr -->
Hooks は `settings.json` の `hooks` キーで宣言し、PreToolUse でツール実行前にブロック判定（exit code 2 でブロック）、PostToolUse で実行後の自動 lint / format を仕掛けるのが入門の典型パターン。最初は `Bash` 限定で監査ログを取り、慣れたら `Edit` の matcher で自動 format を追加するのが安全。
<!-- AUTO:END -->

## 手順
<!-- AUTO:START purpose=recipe-steps -->
1. **目的を決める**: 監査ログ（PostToolUse 全捕捉）か、品質ゲート（特定ツールのブロック）か、編集後の自動整形（PostToolUse + Edit 限定）か
2. **最小設定を `settings.json` に書く**: 例えば PostToolUse + Edit に `prettier --write` を仕掛ける場合、`hooks.PostToolUse` 配下に `matcher: "Edit"`, `hooks: [{type: "command", command: "prettier --write $CLAUDE_FILE_PATHS"}]` を記述
3. **動作確認**: 実際に `claude` セッションで Edit ツールを使う依頼をし、フックが発火するか観察。発火しない場合は matcher の正規表現を疑う
4. **PreToolUse でブロック規則を試す**: 危険コマンドのブロックは `matcher: "Bash"` で、フック側スクリプトが対象引数を JSON で受け取り `exit 2` を返す（Claude Code は exit 2 を「ブロッキングエラー」として扱う）
5. **段階的に範囲を広げる**: `Bash` 全捕捉は実行頻度が高すぎるので、`matcher` を絞る。長時間処理は体感速度を下げるため別プロセス化を検討
6. **複数フック並列**: 同一マッチャに複数 hook を並べると上から順に実行される。冪等性と順序を意識
<!-- AUTO:END -->

## 引用元の補足
公式の hooks 概要・PreToolUse・PostToolUse の 3 ページに分散している情報を、「最初に動かす」目的で再構成した。`exit code 2` が Claude Code 特有の「ブロッキングエラー」規約である点は overview に注記済みだが、入門者が見落としやすいため本レシピでは PreToolUse の手順内に組み込んで強調した。
