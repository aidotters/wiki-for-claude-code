# frontmatter 規約 (frontmatter-spec)

> Wiki ページの YAML frontmatter キーの仕様。`agent/validators/frontmatter_validator` が本仕様を機械的に検証する。
> 機械可読版は `_schemas/frontmatter.schema.json`（type 別 JSON Schema）。

## 共通必須キー（全ページ種別）

| キー | 型 | 必須 | サンプル | 説明 |
|------|----|------|---------|------|
| `title` | string | ✓ | `"Pre-Tool-Use Hook"` | ページタイトル（人間が読む見出し） |
| `type` | enum | ✓ | `source` | ページ種別（`source` / `concept` / `entity` / `comparison` / `synthesis`） |
| `confidence` | number (0.0-1.0) | ✓ | `0.9` | 信頼度。`< 0.5` は `/wiki-lint` でフラグ |
| `sources` | string[] (wikilink) | ✓ | `[]` または `["[[sources/official/cli/installation]]"]` | 引用元ページ。`source` 種別自身は空配列で可 |
| `last_updated` | ISO 8601 date | ✓ | `2026-05-05` | 最終更新日 |
| `stale` | bool | ✓ | `false` | 陳腐化フラグ（`/wiki-lint` で操作可能） |
| `tags` | string[] | ✓ | `[hooks, pre-tool-use]` | 自由タグ（カテゴリ + ページ固有） |

## `type=source` のみ追加必須キー

| キー | 型 | 必須 | サンプル | 説明 |
|------|----|------|---------|------|
| `source_url` | string (URL) | ✓ | `"https://code.claude.com/docs/ja/hooks"` | 取込み元 URL（ホワイトリスト準拠、原則として公式日本語版を採用） |
| `fetched_at` | ISO 8601 datetime | ✓ | `"2026-05-05T10:00:00Z"` | 取得日時 |
| `source_version` | string \| null | 任意 | `null` | 取込み元のバージョン（あれば） |
| `claude_code_version` | SemVer | ✓ | `"1.5.0"` | 対象 Claude Code バージョン |

## 運用メタ（全種別共通、必須）

| キー | 型 | 必須 | サンプル | 説明 |
|------|----|------|---------|------|
| `reviewer` | string | ✓ | `"tak"` | 最終レビュアー識別子 |
| `human_edited` | bool | ✓ | `true` | 人間が手で編集した部分があるか |
| `status` | enum | ✓ | `published` | `draft` → `reviewed` → `published`（単方向遷移） |
| `auto_section_managed` | bool | ✓ | `false` | AUTO セクションマーカー導入済みか（Phase 1 では全て `false`） |

## `status` の遷移規則

```
draft  ─►  reviewed  ─►  published
   ▲                          │
   └──────  禁止（後戻り） ────┘
```

- `draft`: LLM 生成直後または人間執筆中
- `reviewed`: 人間レビュー完了、規約準拠確認済み
- `published`: 公開対象（`/wiki-lint` チェック対象、外部公開可能性あり）
- 後戻り（`published → reviewed` 等）は禁止。修正が必要な場合は新たな `draft` PR を作成する

## サンプル: `source` 種別

```yaml
---
title: "Pre-Tool-Use Hook"
type: source
confidence: 0.9
sources: []
last_updated: 2026-05-05
stale: false
tags: [hooks, pre-tool-use]
source_url: "https://code.claude.com/docs/ja/hooks"
fetched_at: "2026-05-05T10:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: true
status: published
auto_section_managed: false
---
```

## サンプル: `concept` 種別（Phase 2 から）

```yaml
---
title: "Hook 実行モデル"
type: concept
confidence: 0.8
sources:
  - "[[sources/official/hooks/overview]]"
  - "[[sources/official/hooks/pre-tool-use]]"
last_updated: 2026-05-05
stale: false
tags: [hooks, model]
reviewer: "tak"
human_edited: true
status: published
auto_section_managed: false
---
```

## バリデーション挙動

- 共通必須キーまたは `type=source` 追加必須キーが欠損: `agent validate` 終了コード `1`（CI fail）
- 型不一致（例: `confidence: "high"`）: 終了コード `1`
- `status` または `type` が enum 外: 終了コード `1`
- `confidence < 0.5`: `agent lint --all` で警告フラグ（fail はせず終了コード `4` で通知）

## バージョニング

- 本規約自体に `version` フィールドは設けない（規約変更時は ADR を立て、影響範囲を明示）
- 規約変更時の既存記事への適用方針は `docs/core/decisions.md` の該当 ADR で議論する
