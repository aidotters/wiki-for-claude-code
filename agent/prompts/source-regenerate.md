# Prompt: source 種別ページ再生成 (regenerate)

既存の `type: source` ページを最新の raw コンテンツで再生成してください。

## 絶対遵守ルール

1. **全文転載禁止**: 連続100文字以上の一致を避けること
2. **既存補足解説の保持**: 入力の `existing_supplement` セクションは原則そのまま保持し、軽微な事実誤りのみ訂正すること
3. **要約と confidence の更新**: 「概要 (要約)」と frontmatter `confidence` のみ最新内容に基づいて更新する
4. **frontmatter の更新範囲**: `last_updated`, `fetched_at`, `confidence`, `claude_code_version`, `stale=false` のみ更新。それ以外（`title`, `tags`, `reviewer`, `human_edited`, `status`, `auto_section_managed`）は保持
5. **意味のない更新は避ける**: raw の核となる主張に変化がない場合は要約を書き換えないこと（冪等性確保）

## 入力

```yaml
existing_frontmatter:
{{existing_frontmatter}}
```

```markdown
existing_supplement:
{{existing_supplement}}
```

```text
raw_content:
{{raw_content}}
```

## 出力形式

`source-ingest.md` と同じ frontmatter + 3部構成の Markdown。
ただし、補足解説セクションは `existing_supplement` をそのまま保持すること。
