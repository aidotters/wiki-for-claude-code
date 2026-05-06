---
description: 既存の source 種別ページを最新の取込み元で再生成
argument-hint: <vault/sources/official/.../page.md>
---

# /wiki-regenerate

既存 `type: source` ページを取込み元から再フェッチし、要約と confidence を更新します。
補足解説セクションは保持されます（人手編集を尊重）。

## 入力

- `$1`: 対象ページのパス（必須、`vault/sources/official/...` 配下の `.md`）

## 実行手順

### 0. スタブ上書きリスクの事前チェック（実 LLM 統合完了まで必須）
- `$1` の frontmatter から `status` を読み取る
- `status: reviewed` または `status: published` の場合、**ここで停止しユーザーに確認を求める**
  - 理由: 現状の `agent regenerate` は LLM スタブで動作し、低品質ダミー本文で記事を上書きする（CLAUDE.md「`agent regenerate` の運用注意」参照）。reviewed/published 記事を上書きすると手書きの要約・補足解説が失われる
  - 確認時は次の選択肢を提示: (a) バックアップ取得後に強行 / (b) 対象を `status: draft` のページへ変更 / (c) 中止
- `status: draft` であればそのまま手順1へ進む
- 実 LLM 統合（Phase 2/3）完了後は本ステップを撤去する

### 1. 対象ページの確認
- `$1` を読み、`type: source` であることを確認
- `source_url` が `@.claude/skills/llm-wiki-for-claude-code/references/sources-whitelist.md` のホワイトリストに含まれることを確認

### 2. CLI 経由での再生成
- 次のコマンドを実行:
  ```bash
  uv run agent regenerate --target "$1"
  ```
- 出力に `no changes` が含まれる場合、取込み元に変化がないため正常終了

### 3. 差分の確認
- `git diff "$1"` で変更点を確認（git 未初期化の場合はスキップ）
- 変更が「要約」「confidence」「タイムスタンプ」の範囲内であること、補足解説セクションが保持されていることを確認

### 4. 規約検証
```bash
uv run agent validate --target "$1"
```

### 5. log.md の追記
- CLI が自動で `vault/log.md` に追記済み

## 冪等性

連続 2 回実行で意味のある差分が出ないことが要件（ADR / PRD KPI）。
2 回目以降の出力に `no changes` が含まれない場合は、`agent/orchestration/regenerate.py` の挙動を確認すること。
