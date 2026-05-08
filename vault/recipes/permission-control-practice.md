---
title: "パーミッション制御の実践（チーム共有設定）"
type: recipe
use_case: "Claude Code の permissions を実プロジェクトで運用するため、チーム共有 allow / deny ポリシーを設計する"
confidence: 0.7
sources:
  - "[[sources/official/cli/permissions]]"
  - "[[sources/official/cli/configuration]]"
  - "[[sources/official/hooks/pre-tool-use]]"
last_updated: 2026-05-06
stale: false
tags: [recipe, permissions, security, team]
reviewer: "tak"
human_edited: true
status: published
auto_section_managed: true
---

## TL;DR
<!-- AUTO:START purpose=recipe-tldr -->
permissions は「チーム共通で許す安全なコマンド」を `.claude/settings.json` の `allow` に置き、「絶対禁止」を `deny` に置く（deny 優先）。`Bash(...)` の引数有無は厳密に区別されるため、引数付きパターンは `Bash(npm run:*)` のようにワイルドカード `:*` を使う。複雑なロジック判定は permissions ではなく PreToolUse フックに譲る。
<!-- AUTO:END -->

## 手順
<!-- AUTO:START purpose=recipe-steps -->
1. **既定のチーム共有を `.claude/settings.json` に置く**: Git 管理対象。例: `permissions.allow` に `Bash(git status)`, `Bash(git diff:*)`, `Edit(src/**/*.ts)` を入れる
2. **絶対禁止を `deny` に置く**: 例: `Bash(rm -rf:*)`, `Bash(sudo:*)`, `Bash(curl:*)` など。deny は allow より優先される
3. **個人の追加許可は `.local.json`**: `.claude/settings.local.json`（Git 除外）に個人だけが必要なものを加える。これでチーム共有を汚さない
4. **対話中は `/permissions`**: セッション内で出た新しい許可候補を、その場で永続化または一時許可で対応
5. **複雑な判定はフックへ**: 「特定ファイルだけ Edit を許す」「ブランチが main の場合だけブロック」のような動的判定は PreToolUse フックで実装し、permissions は単純化を保つ
6. **deny の落とし穴を確認**: `Bash(git diff)`（引数なしのみ）と `Bash(git diff:*)`（引数あり）は別物として扱われるため、両方カバーするか意識的に片方だけ許可する
<!-- AUTO:END -->

## 引用元の補足
permissions の単純な記法は公式ドキュメントで完結するが、「チーム共有 / 個人 / フック切り分け」の運用観点は明文化されていない。本レシピは configuration の階層構造（`.json` / `.local.json`）と pre-tool-use の動的判定を組み合わせた実運用パターンとして再構成している。
