---
description: vault 全体の lint 検査（孤立/陳腐化/低信頼度/不足/index 同期）
argument-hint: なし（常に --all）
---

# /wiki-lint

vault 全体に対し、規約違反候補を検出します。

## 実行手順

### 1. lint コマンド実行
```bash
uv run agent lint --all
```

### 2. レポートの解釈

`@.claude/skills/llm-wiki-for-claude-code/references/lint-rules.md` の検出6項目に従って結果を分類:

| 項目 | 重大度 | 主な対処 |
|------|--------|---------|
| `[orphan]` | warning | リンク追加 or `vault/index.md` への登録 |
| `[stale]` | warning | `/wiki-regenerate` で再生成 or `stale: true` の意図的設定確認 |
| `[low_confidence]` | warning | 補足解説の追加・引用追加で信頼度を上げる |
| `[broken]` | error | 不足ページの作成 or 引用先の修正（リンク切れ） |
| `[index_sync]` | warning | `vault/index.md` への手動追加（Phase 1 では手動メンテ） |
| `[contradiction-candidate]` | info | Phase 2 以降で対応、Phase 1 では情報提示のみ |

### 3. 違反の解消

各違反について、対応する操作を実行:
- `broken`: 該当ページを作成するか、wikilink を修正
- `orphan`: `vault/index.md` または関連ページから wikilink で参照を追加
- `stale`: `/wiki-regenerate` で再生成、もしくは内容を確認した上で `last_updated` を更新

### 4. 終了コード

- 違反 0 件: 終了コード 0
- 違反あり: 終了コード 4（CI では fail させない）

## 注意

- `/wiki-lint` は **人間レビュー支援** のため、CI では使わない
- CI ガード用には `agent validate --all`（終了コード 1 で fail）を使う
- Phase 1 では `contradiction` の機械的検出は未実装（同一 tag のリスト化のみ）
