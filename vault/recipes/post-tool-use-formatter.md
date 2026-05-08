---
title: "編集後の自動 format（PostToolUse 実践）"
type: recipe
use_case: "Edit / Write ツール実行後に自動で format / lint を走らせ、コードベースのスタイル一貫性を保つ"
confidence: 0.7
sources:
  - "[[sources/official/hooks/post-tool-use]]"
  - "[[sources/official/hooks/overview]]"
last_updated: 2026-05-06
stale: false
tags: [recipe, hooks, format, quality]
reviewer: "tak"
human_edited: true
status: published
auto_section_managed: true
---

## TL;DR
<!-- AUTO:START purpose=recipe-tldr -->
PostToolUse + Edit/Write の matcher を組み合わせ、`prettier --write` や `ruff format` を呼ぶフックを `settings.json` に置けば、Claude が編集するたびに自動整形がかかる。長時間処理にすると体感速度が下がるため、対象ファイルだけに絞り、CI 重視のチェックは別途回す方針が安全。
<!-- AUTO:END -->

## 手順
<!-- AUTO:START purpose=recipe-steps -->
1. **対象ツールを決める**: Python なら `Edit` と `Write`、JS/TS なら `Edit` と `Write` と `MultiEdit` を matcher に並べる
2. **整形コマンドを選ぶ**: ワークスペース既定（`prettier`、`ruff format`、`black` 等）を選ぶ。引数で対象ファイル名を渡すスタイル
3. **`settings.json` に hook を記述**: `hooks.PostToolUse` に `matcher`（正規表現可）と `hooks: [{type: "command", command: "prettier --write $CLAUDE_FILE_PATHS"}]` を入れる
4. **失敗時の挙動を確認**: PostToolUse は exit code 非ゼロでもセッションを止めない。`prettier` のシンタックスエラーで赤字通知が出るが Claude は次に進めるため、開発体験への影響は小さい
5. **拡張**: 単純な format に加えて `eslint --fix` や `mypy --strict` を続けて回す場合は、複数 hook を順序付きで並べる。各 hook は冪等であることを意識
6. **CI 衝突を避ける**: ローカルの自動整形と CI のチェックが矛盾しないよう、両者で同じ設定ファイル（`.prettierrc` 等）を読ませる
<!-- AUTO:END -->

## 引用元の補足
公式 PostToolUse ページは「品質ゲートに有用」と述べるに留まるが、実際の `prettier` や `ruff format` を組み込む際の手順・落とし穴（exit code 非ゼロのセッション継続挙動、CI 衝突、対象 matcher の絞り込み）はレシピ化する価値がある。本レシピは overview の補足と post-tool-use の用途記述を結合し、実運用フローとして再構成した。
