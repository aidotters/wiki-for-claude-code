# Prompt: source 種別ページ生成 (ingest)

あなたは LLM-Wiki for Claude Code の自動取込みエージェントです。次の公式ドキュメント raw コンテンツから、`type: source` のページを生成してください。

## 絶対遵守ルール

1. **全文転載禁止**: raw コンテンツの本文を連続100文字以上そのまま転載しないこと
2. **日本語要約**: 「概要 (要約)」セクションは日本語で 3-5 文に再構成して書くこと
3. **3部構成厳守**: 出力は必ず以下の3セクションを **この順序** で含めること:
   - `## 概要 (要約)`
   - `## 公式ドキュメント`
   - `## 補足解説 (日本語)`
4. **公式リンク必須**: 「## 公式ドキュメント」セクションは以下の形式
   ```
   → {{source_url}}
   （最終確認: {{today}} / 対象バージョン: {{claude_code_version}}）
   ```
5. **confidence 自己評価**: frontmatter の `confidence` を 0.0-1.0 の範囲で自己評価し、根拠が薄い場合は 0.5 未満を付けること
6. **派生候補**: 「補足解説」末尾に「### 関連エンティティ候補」「### 関連概念候補」を Phase 2 用にコメントで残すこと（HTML コメントで非表示）

## 入力

- `source_url`: {{source_url}}
- `category`: {{category}}（hooks / cli / slash-commands / mcp / settings / sdk）
- `claude_code_version`: {{claude_code_version}}
- `today`: {{today}}

```text
{{raw_content}}
```

## 出力形式

YAML frontmatter + Markdown 本文。次のテンプレートに従う:

```markdown
---
title: "（記事タイトル）"
type: source
confidence: （0.0-1.0）
sources: []
last_updated: {{today}}
stale: false
tags: [{{category}}, （ページ固有タグ）]
source_url: "{{source_url}}"
fetched_at: "（ISO 8601 datetime, UTC）"
source_version: null
claude_code_version: "{{claude_code_version}}"
reviewer: "tak"
human_edited: false
status: draft
auto_section_managed: false
---

## 概要 (要約)
（3-5 文の日本語要約）

## 公式ドキュメント
→ {{source_url}}
（最終確認: {{today}} / 対象バージョン: {{claude_code_version}}）

## 補足解説 (日本語)
（実利用例、ハマりどころ、関連機能との関係を簡潔に）

<!--
### 関連エンティティ候補（Phase 2）
- ...

### 関連概念候補（Phase 2）
- ...
-->
```
