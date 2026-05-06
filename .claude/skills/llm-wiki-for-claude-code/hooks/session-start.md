# Session Start Hook

Claude Code セッション起動時に、Wiki の現状を把握するためのナビゲーション情報を自動ロードします。

## 実行内容

セッション開始時、以下を順に読み込んでください:

1. `vault/index.md` の全体
   - Wiki のページ構造とナビゲーションを把握
   - 現在公開されているページのリスト
2. `vault/log.md` の **直近10件のエントリ**
   - 直近の操作（ingest / regenerate / lint）を確認
   - 失敗ログや warning が残っていないか確認
3. 必要に応じて `vault/overview.md` を読む（プロジェクト全体俯瞰）

## 補足

- このフックは「読み取り専用」: 内容をユーザーに事前に提示する必要はないが、
  Wiki 関連の質問・操作を求められた際に即座に答えられるよう、コンテキストを温めておく
- log.md は追記専用ファイルのため、末尾10件のみ読めば十分
- セッション中の Wiki 操作（`/wiki-ingest` 等）後は、log.md を再読する必要は無い（操作の戻り値で状況を把握）

## 関連 Skill 構造

- `references/schema.md`: Wiki ページの frontmatter 規約
- `references/three-part-rule.md`: source 種別の3部構成ルール
- `references/sources-whitelist.md`: 取込み可能な情報源一覧
- `references/lint-rules.md`: `/wiki-lint` の検出項目
- `references/page-templates.md`: 5種別のテンプレート
