---
name: llm-wiki-for-claude-code
description: LLM-Wiki for Claude Code の規約・テンプレート・hook を提供する Skill。Wiki ページ（vault/sources/, vault/concepts/, vault/entities/, vault/comparisons/, vault/syntheses/）の編集や frontmatter 検証、3部構成チェック、引用ルール確認の文脈で context-aware にロードされる。`/wiki-ingest`, `/wiki-regenerate`, `/wiki-lint` の各操作の規約参照元として `references/` 配下を提供する。
triggers:
  - "vault/**/*.md"
  - "vault/90_meta/**"
  - "frontmatter-spec.md"
  - "markdown-rules.md"
---

# LLM-Wiki for Claude Code Skill

このスキルは、LLM-Wiki for Claude Code プロジェクトの **規約・テンプレート・hook** を Claude Code に提供します。Wiki ページ編集中に文脈に応じて自動ロードされ、`/wiki-*` スラッシュコマンドの規約参照元としても使われます（ADR-014）。

## 3レイヤー構造

このプロジェクトは Karpathy 氏の LLM-Wiki 設計に従い、3つのレイヤーを持ちます:

| レイヤー | 場所 | 性質 | 編集者 |
|---------|------|------|-------|
| **Raw Sources** | 公式 docs.claude.com 等（プロジェクト外） | 不変 | LLM は読むのみ |
| **Wiki** | `vault/` | LLM 生成 + 人間レビュー | 両方 |
| **Schema** | このスキル + `vault/90_meta/` | 規約 | 人間が定義、LLM が遵守 |

## 7つの絶対ルール

Wiki ページを編集・生成する際は、以下を遵守すること:

1. **Raw Sources 不変**: 取込み元のコンテンツを直接書き換えない（読むのみ）
2. **引用必須**: `type: source` 以外は frontmatter の `sources` キーに wikilink で引用元を明示
3. **Wikilinks 形式**: ページ間リンクは `[[file-name]]` または `[[path/to/file]]`
4. **frontmatter 必須**: 全ページに `references/schema.md` 準拠の frontmatter
5. **3部構成（source 種別のみ）**: 「## 概要 (要約)」「## 公式ドキュメント」「## 補足解説 (日本語)」を厳守
6. **index 更新**: 新規ページ作成時は `vault/index.md` のカテゴリリストに追加
7. **log.md 追記**: 全操作を `vault/log.md` に追記（CLI が自動実行）

## 規約参照（references/）

`vault/90_meta/` のシンボリックリンクで以下を提供します（ADR-013）:

- `references/schema.md` → frontmatter 規約（共通必須キー + type 別）
- `references/three-part-rule.md` → Markdown 制約（許可/禁止記法、3部構成強制）
- `references/sources-whitelist.md` → 取込み元ホワイトリスト
- `references/lint-rules.md` → `/wiki-lint` の検出6項目
- `references/page-templates.md` → 5種別のテンプレート（Phase 1 では `source` のみ実体）

Wiki ページ編集時、上記の対応する規約を必要に応じて自動参照してください。

## hook（hooks/session-start.md）

Claude Code 起動時に `vault/index.md` の全体と `vault/log.md` の直近10件を自動ロードします。

## スラッシュコマンドとの連携

`/wiki-ingest`, `/wiki-regenerate`, `/wiki-lint` の各コマンド（`.claude/commands/wiki-*.md`）は、本 Skill の `references/` を `@.claude/skills/llm-wiki-for-claude-code/references/...` 形式で参照します。
