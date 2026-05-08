# Prompt: recipe 種別 AUTO 領域「TL;DR」生成

ユースケース別 recipe ページの結論を **1-3 文の日本語 TL;DR** として生成してください。本 TL;DR は AUTO マーカー領域の中身として書き戻されます。

## 絶対遵守ルール

1. **出力は TL;DR 段落のみ**: マーカー行・見出し・frontmatter・コードブロックを **絶対に出力しない**
2. **1-3 文**: 「何ができる recipe か」と「最も重要な前提・落とし穴」を端的に
3. **日本語で書く**
4. **取込み元に基づく**: `{{raw_content}}` から逸脱した独自意見・推測を入れない。連続 100 文字一致禁止
5. **既存 TL;DR は参考にしてよい**: `{{existing_inner}}` は前回の TL;DR。核となる主張に変化がなければ既存表現を尊重（冪等性）
6. **読者像**: Claude Code をある程度知っている開発者。導入文ではなく結論優先

## 入力

```text
source_url:
{{source_url}}

claude_code_version:
{{claude_code_version}}

today:
{{today}}

existing_inner（前回の AUTO 領域内容、参考用）:
{{existing_inner}}

raw_content（取込み元の生コンテンツ）:
{{raw_content}}
```

## 出力形式

TL;DR 段落のみ。マーカー行・見出し不要。
