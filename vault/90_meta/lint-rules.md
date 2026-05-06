# Lint ルール (lint-rules)

> `/wiki-lint`（`agent lint --all`）の検出項目仕様。`agent/validators/lint_validator` が本仕様に従って検出する。
> `agent validate --all`（CI 用）とは異なり、知的判断要素（孤立・陳腐化・矛盾）を含む。

## 検出6項目

### 1. 孤立ページ（orphan）

- **定義**: インバウンドの wikilinks が **0件** のページ
- **対象**: `vault/index.md`, `vault/log.md`, `vault/overview.md`, `vault/90_meta/*` を除く全ページ
- **検出ロジック**: 全 .md ファイルから wikilinks を抽出し、各ページの被参照数を集計、被参照数 0 のページをフラグ
- **重大度**: warning

### 2. 陳腐化（stale）

- **定義**: 以下のいずれかを満たすページ
  - `stale: true` が frontmatter に明示されている
  - `last_updated` から **30日超** 経過している
- **対象**: 全ページ（特に `type: source`）
- **検出ロジック**: 現在日付と `last_updated` の差分計算
- **重大度**: warning

### 3. 矛盾（contradiction）

- **定義**: 同じトピック（同じ tag を持つ）の複数ページで主張不一致
- **対象**: `type: source` 同士、`type: source` と派生種別
- **検出ロジック**: Phase 1 では実装最小限（同じ `tags` を持つページの存在をリスト化するのみ。実際の矛盾検出は Phase 2 以降で LLM ベース検出を追加検討）
- **重大度**: warning（情報提示のみ）

### 4. 低信頼度（low confidence）

- **定義**: `confidence < 0.5` のページ
- **対象**: 全ページ
- **検出ロジック**: frontmatter の `confidence` フィールド
- **重大度**: warning

### 5. 不足ページ（broken wikilinks）

- **定義**: 既存ページから wikilink で参照されているが、対象ファイルが存在しないページ
- **対象**: 全ページ
- **検出ロジック**: 全 .md から wikilinks を抽出し、ファイルシステム上で対象 .md ファイルが存在するか確認
- **重大度**: error（リンク切れは品質に直結）

### 6. index 同期（index sync）

- **定義**: 全公開ページ（`status: published`）が `vault/index.md` に表示されているか
- **対象**: `status: published` のページ
- **検出ロジック**: `vault/index.md` から wikilinks を抽出し、`status: published` の全ページがリストされているか確認
- **重大度**: warning（Phase 1 では手動メンテナンス、Phase 2 以降で自動更新化）

## 出力フォーマット

`agent lint --all` は以下の形式で結果を出力する:

```
=== Lint Report ===
Orphan pages:        2
Stale pages:         0
Low confidence:      1
Broken wikilinks:    0
Index sync issues:   3
Contradictions:      0
-------------------
Total violations:    6

[orphan] vault/sources/official/cli/some-page.md
[stale] vault/sources/official/hooks/old-page.md (last_updated: 2026-04-01, days_old: 35)
[low_confidence] vault/sources/official/cli/uncertain.md (confidence: 0.4)
[index_sync] vault/sources/official/cli/missing-from-index.md
```

`vault/log.md` には以下を追記する:

```markdown
## [YYYY-MM-DD HH:MM] lint | total=N violations (orphan=2 stale=0 low_conf=1 broken=0 index=3 contra=0)
```

## 終了コード

- 違反 0 件: `0`
- 違反あり: `4`（lint 違反専用、`/wiki-lint` 専用）

`/wiki-lint` の終了コード `4` は CI では fail させない（人間レビュー支援のため）。
CI ガード用には別途 `agent validate --all`（終了コード `0` または `1`）を使用する。

## Phase 別の精度

- **Phase 1**: 孤立・陳腐化（30日固定）・低信頼度・不足ページ・index 同期の機械的検出。矛盾はリスト化のみ
- **Phase 2**: AUTO セクションマーカー違反検出を追加
- **Phase 3**: 矛盾の LLM ベース検出、外部リンク到達確認の本格化
