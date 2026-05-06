# Markdown 制約 (markdown-rules)

> Wiki ページの Markdown 記法制約。`agent/validators/markdown_rules_validator` および `three_part_validator` が機械的に検証する。

## 許可記法

- **CommonMark**: 標準 Markdown（見出し、リスト、コードブロック、リンク、強調、表）
- **Wikilinks**: `[[file-name]]` または `[[path/to/file]]`（Obsidian 記法、ただし shortest 設定を前提）
  - エイリアス: `[[file-name|表示名]]`
  - 「不足ページ」は `agent lint` で検出する
- **Mermaid**: ` ```mermaid ` ブロック（フロー図・シーケンス図等）
- **HTML コメント**: `<!-- ... -->` （Phase 2 で AUTO セクションマーカーを導入する際に活用）

## 禁止記法

| 記法 | 例 | 検出パターン | 不採用理由 |
|------|----|------------|-----------|
| Obsidian Dataview | ` ```dataview ` ブロック | 行頭が ```` ```dataview ```` | 公開時 portability を損なう（Karpathy 原案では推奨だが本プロジェクトでは ADR-004 で不採用） |
| Obsidian Callout | `> [!note]`, `> [!warning]` | 行頭 `> [!` | 標準 Markdown 外 |
| Obsidian 埋め込み | `![[file-name]]` | 先頭 `![[` | 一般 Markdown レンダラで動作しない |

## `source` 種別の3部構成強制

`type: source` のページは以下の3セクションを **この順序で** 含む必要がある:

```markdown
## 概要 (要約)
（3-5文の日本語要約。公式の核心ポイントを再構成）

## 公式ドキュメント
→ {URL}（最終確認: YYYY-MM-DD / 対象バージョン: X.Y.Z）

## 補足解説 (日本語)
（実利用例、ハマりどころ、関連機能との関係）
```

### セクション要件

- 「## 概要 (要約)」: 必須、見出し文字列の完全一致を要求
- 「## 公式ドキュメント」: 必須、内部に `→ ` 始まりの URL 行と `最終確認: YYYY-MM-DD` `対象バージョン: X.Y.Z` を含むこと
- 「## 補足解説 (日本語)」: 必須、見出し文字列の完全一致を要求
- 3セクション以外の追加見出しは「補足解説」セクション内のサブ見出しとして配置可能（`### ...`）

### 検証エラー

`three_part_validator` が3セクションのいずれかの欠損を検出した場合、`agent validate` 終了コード `1`。

## 派生種別（`concept` / `entity` / `comparison` / `synthesis`）

- 構成は自由（3部構成は強制しない）
- ただし `sources` frontmatter キー必須かつ wikilink で実在ページを指していること（`citation_validator` で検証）
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
