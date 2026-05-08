# Page Templates

各ページ種別のテンプレート集。Phase 2-A 時点で `source` / `recipe` を実体化、他種別はスタブ。

## source 種別テンプレート（Phase 2-A 縮退仕様 / ADR-017）

```markdown
---
title: "（記事タイトル、例: Pre-Tool-Use Hook）"
type: source
confidence: 0.85    # 0.0-1.0、0.7 未満は要点強化が必要
sources: []          # source 種別自身は引用元なし（空配列）
last_updated: 2026-05-06
stale: false
tags: [<カテゴリ>, <ページ固有タグ>]
source_url: "https://code.claude.com/docs/ja/hooks/<page>"
fetched_at: "2026-05-06T10:00:00Z"
source_version: null    # ETag があれば設定（regenerate で活用）
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: true
status: draft           # → reviewed → published（単方向遷移）
auto_section_managed: true   # Phase 2-A から true（AUTO 領域導入済み）
---

## 概要 (要約)
<!-- AUTO:START -->
（1 段落の日本語要約。3-5 文。公式日本語版の連続 100 文字一致を回避）
<!-- AUTO:END -->

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks/<page>
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）
```

> 旧 `## 補足解説 (日本語)` セクションは ADR-017 で撤廃。補足は `recipe` / `concept` / `entity` 種別で表現する。

## recipe 種別テンプレート（Phase 2-A 実体）

```markdown
---
title: "（ユースケース名、例: Claude Code セットアップ）"
type: recipe
use_case: "（具体的なユースケース、1 文。例: Claude Code を新規プロジェクトでセットアップする）"
confidence: 0.7         # 0.7 以上で published 化可能
sources:                # 最低 2 件、vault/sources/ 配下への wikilink
  - "[[sources/official/cli/installation]]"
  - "[[sources/official/cli/configuration]]"
last_updated: 2026-05-06
stale: false
tags: [recipe, <カテゴリ>]
reviewer: "tak"
human_edited: true
status: draft
auto_section_managed: true
---

## TL;DR
<!-- AUTO:START -->
（ユースケースの結論を 1-3 文で。何をすればゴールに到達できるかを最短で示す）
<!-- AUTO:END -->

## 手順
<!-- AUTO:START -->
1. ...
2. ...
3. ...
<!-- AUTO:END -->

## 引用元の補足
（人手記述。引用元のどの部分を再構成したか、横断視点でどう独自価値を出したか）

## 関連
- [[sources/official/cli/installation]]
- [[sources/official/cli/configuration]]
```

> `recipe` 種別の必須要件:
> - `use_case` キーは 1 文で具体的に書く（曖昧な「セットアップ全般」より「新規プロジェクトに導入してテスト実行まで」のように粒度を絞る）
> - `sources` 最低 2 件は **既存の `vault/sources/` 配下** への wikilink（`citation_validator` で検証）
> - AUTO 領域は最低 2 件（`## TL;DR` / `## 手順`）。`## 引用元の補足` は人手領域

## concept 種別テンプレート（Phase 2 スタブ）

```markdown
---
title: "（概念タイトル）"
type: concept
confidence: 0.8
sources:
  - "[[sources/official/<category>/<source-page>]]"
last_updated: 2026-05-05
stale: false
tags: [<関連 tag>]
reviewer: "tak"
human_edited: true
status: draft
auto_section_managed: false
---

# （概念タイトル）

（複数の source ページを横断する概念の解説。引用必須）

## 関連 source

- [[sources/official/<category>/<source-page>]]
```

> Phase 2 で本テンプレートを実体化し、`citation_validator` の対象とする。

## entity 種別テンプレート（Phase 2 スタブ）

```markdown
---
title: "（ツール・コマンド・人物名）"
type: entity
confidence: 0.85
sources:
  - "[[sources/official/<category>/<source-page>]]"
last_updated: 2026-05-05
stale: false
tags: [<関連 tag>]
reviewer: "tak"
human_edited: true
status: draft
auto_section_managed: false
---

# （Entity 名）

## 概要

## 関連 source

- [[...]]
```

## comparison 種別テンプレート（Phase 3 スタブ）

```markdown
---
title: "（A vs B の比較）"
type: comparison
confidence: 0.7
sources:
  - "[[entities/A]]"
  - "[[entities/B]]"
last_updated: 2026-05-05
stale: false
tags: [comparison]
reviewer: "tak"
human_edited: false
status: draft
auto_section_managed: true   # comparison は自動生成対象
---

# （A vs B）

| 観点 | A | B |
|------|---|---|
| ... | ... | ... |
```

## synthesis 種別テンプレート（Phase 2 スタブ）

```markdown
---
title: "（クエリ）に対する synthesis"
type: synthesis
confidence: 0.75
sources:
  - "[[sources/...]]"
  - "[[concepts/...]]"
last_updated: 2026-05-05
stale: false
tags: [synthesis]
reviewer: "tak"
human_edited: false
status: draft
auto_section_managed: false
---

# （クエリ）

## 回答

## 引用元

- [[...]]
```
