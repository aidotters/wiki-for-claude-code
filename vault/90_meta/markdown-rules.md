# Markdown 制約 (markdown-rules)

> Wiki ページの Markdown 記法制約。`agent/validators/markdown_rules_validator` および `three_part_validator` が機械的に検証する。

## 許可記法

- **CommonMark**: 標準 Markdown（見出し、リスト、コードブロック、リンク、強調、表）
- **Wikilinks**: `[[file-name]]` または `[[path/to/file]]`（Obsidian 記法、ただし shortest 設定を前提）
  - エイリアス: `[[file-name|表示名]]`
  - 「不足ページ」は `agent lint` で検出する
- **Mermaid**: ` ```mermaid ` ブロック（フロー図・シーケンス図等）
- **HTML コメント**: `<!-- ... -->`（AUTO セクションマーカーで活用、詳細は [[auto-marker-spec]]）
- **AUTO セクションマーカー**: `<!-- AUTO:START --> ... <!-- AUTO:END -->`（行頭限定、ネスト禁止、構文詳細は [[auto-marker-spec]]）

## 禁止記法

| 記法 | 例 | 検出パターン | 不採用理由 |
|------|----|------------|-----------|
| Obsidian Dataview | ` ```dataview ` ブロック | 行頭が ```` ```dataview ```` | 公開時 portability を損なう（Karpathy 原案では推奨だが本プロジェクトでは ADR-004 で不採用） |
| Obsidian Callout | `> [!note]`, `> [!warning]` | 行頭 `> [!` | 標準 Markdown 外 |
| Obsidian 埋め込み | `![[file-name]]` | 先頭 `![[` | 一般 Markdown レンダラで動作しない |

## `source` 種別の縮退仕様（ADR-017）

`type: source` のページは以下の **2 セクション構造**（縮退仕様）を遵守すること:

```markdown
## 概要 (要約)
<!-- AUTO:START -->
（1 段落の日本語要約。3-5 文。公式日本語版の連続 100 文字一致を回避）
<!-- AUTO:END -->

## 公式ドキュメント
→ {公式日本語版 URL}
（最終確認: YYYY-MM-DD / 対象バージョン: X.Y.Z）
```

### セクション要件

- 「## 概要 (要約)」: 必須、見出し文字列の完全一致。配下に **AUTO 領域 1 件** を含むこと
- 「## 公式ドキュメント」: 必須、内部に `→ ` 始まりの URL 行と `最終確認: YYYY-MM-DD` `対象バージョン: X.Y.Z` を含むこと
- 「## 補足解説 (日本語)」セクションは **撤廃**（旧 ADR-003、補足は `recipe` / `concept` / `entity` 種別で表現）
- AUTO マーカー構文の詳細は [[auto-marker-spec]] を参照

### 検証エラー

`three_part_validator`（縮退版）は以下を検証する:

- 「## 概要 (要約)」見出し欠損 → `agent validate` 終了コード `1`
- 「## 公式ドキュメント」見出し欠損 / `→ URL` 欠損 / `最終確認:` 欠損 / `対象バージョン:` 欠損 → 終了コード `1`
- 「## 概要 (要約)」配下の AUTO 領域不在（`auto_section_managed: true` のとき）→ 終了コード `1`

### 移行注記

- ADR-003（旧 3 部構成）→ ADR-017（縮退仕様）への移行は Phase 2-A の A-2 タスクで実施
- 旧 `## 補足解説 (日本語)` セクションを持つ既存記事は縮退書き換えと同時に削除し、内容は recipe / concept 種別へ転記する

## 派生種別（`concept` / `entity` / `comparison` / `synthesis` / `recipe`）

- 構成は自由（縮退仕様は強制しない）
- ただし `sources` frontmatter キー必須かつ wikilink で実在ページを指していること（`citation_validator` で検証）
- `recipe` 種別は `sources` ≥ 2 件、`use_case` キー必須（[[frontmatter-spec]] 参照）
- 主張を含む段落には可能な限り `[[sources/...]]` で引用を付ける（Phase 2 以降で運用ルール詳細化）

## 全文転載禁止（連続100文字一致）

- `type: source` のページは、`source_url` 取得時の raw コンテンツと **連続100文字以上の一致** があってはならない
- `transclusion_validator` が日本語/英語の文字列スライディングウィンドウで検出する
- 違反検出時は `agent validate` 終了コード `1`
- 詳細は [[license-notes]] を参照

## 「公式ドキュメント」セクションのフォーマット

```markdown
## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks
（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）
```

- URL 行は `→ ` で始まり、その後にスペースを挟まず URL を1つ記載（複数 URL は補足解説セクションで対応）
- 直後の行に `（最終確認: YYYY-MM-DD / 対象バージョン: X.Y.Z）` を記載
- `last_updated` frontmatter とこの「最終確認」日付は一致させる
