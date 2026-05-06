# Page Templates

各ページ種別のテンプレート集。Phase 1 では `source` 種別のみ実体、他種別はスタブ。

## source 種別テンプレート（Phase 1 実体）

```markdown
---
title: "（記事タイトル、例: Pre-Tool-Use Hook）"
type: source
confidence: 0.85    # 0.0-1.0、0.7 未満は補足解説で根拠を強化すること
sources: []          # source 種別自身は引用元なし（空配列）
last_updated: 2026-05-05
stale: false
tags: [<カテゴリ>, <ページ固有タグ>]
source_url: "https://code.claude.com/docs/ja/hooks/<page>"
fetched_at: "2026-05-05T10:00:00Z"
source_version: null    # ETag があれば設定（regenerate で活用）
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: true
status: draft           # → reviewed → published（単方向遷移）
auto_section_managed: false   # Phase 2 で AUTO セクション導入時に true 化
---

## 概要 (要約)
（公式の核となるポイントを日本語で 3-5 文に要約。連続100文字以上の転載禁止）

## 公式ドキュメント
→ https://code.claude.com/docs/ja/hooks/<page>
（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)
（実利用例、ハマりどころ、関連機能との関係を簡潔に）

<!--
### 関連エンティティ候補（Phase 2）
- ...

### 関連概念候補（Phase 2）
- ...
-->
```

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
