---
description: 公式ドキュメントの URL から source 種別ページを生成
argument-hint: <official-url> [--category hooks|cli|...]
---

# /wiki-ingest

公式ドキュメントの URL を取込み、規約準拠の `type: source` ページを生成します。

## 入力

- `$1`: 取込み元 URL（必須、`vault/90_meta/sources.md` のホワイトリスト準拠）
- `$2` または `--category`: カテゴリ（hooks / cli / slash-commands / mcp / settings / sdk）

## 実行手順

以下の6ステップを順番に実行してください。各ステップでエラーがあれば、そこで停止してユーザーに報告すること。

### 1. ホワイトリスト検証
- `@.claude/skills/llm-wiki-for-claude-code/references/sources-whitelist.md` を参照し、`$1` のドメインが `enabled: true` のソースに含まれることを確認

### 2. 重複検出
- `vault/sources/` 配下を grep し、同一 `source_url` の既存ページが無いことを確認
- 既存があれば `/wiki-regenerate` の使用を提案して停止

### 3. CLI 経由でのページ生成
- 次のコマンドを実行:
  ```bash
  uv run agent ingest --source-url "$1" --category "<category>"
  ```
- 終了コード 0 以外なら停止してエラーメッセージをユーザーに伝える

### 4. 生成ページのレビュー
- 生成されたページ（`vault/sources/official/<category>/<slug>.md`）を読み、以下を確認:
  - `@.claude/skills/llm-wiki-for-claude-code/references/three-part-rule.md` の3部構成（「## 概要 (要約)」「## 公式ドキュメント」「## 補足解説 (日本語)」）が揃っている
  - `@.claude/skills/llm-wiki-for-claude-code/references/schema.md` の必須 frontmatter キーが揃っている
  - 連続100文字以上の公式コンテンツ転載が無い

### 5. 規約検証
- 次のコマンドで機械的検証を実行:
  ```bash
  uv run agent validate --target vault/sources/official/<category>/<slug>.md
  ```
- 失敗時はエラーを修正してから次へ進む

### 6. index.md / log.md の更新
- 生成ページが `vault/index.md` のカテゴリリストに追加されていることを確認（無ければ追加提案）
- `vault/log.md` の追記は CLI 側で自動実行済み

## 注意

- 取込み元の利用規約・robots.txt 違反が疑われる場合は、`vault/90_meta/license-notes.md` を参照しユーザーに確認を求めること
- 全文転載は `transclusion_validator` で機械検出するが、人手チェックも併用すること
- 生成ページの `status` は初期値 `draft`。レビュー完了後 `reviewed` → `published` に進めること
