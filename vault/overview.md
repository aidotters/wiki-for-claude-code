# LLM-Wiki for Claude Code: Overview

> Andrej Karpathy 氏の LLM-Wiki コンセプトと Reza Rezvani 氏の Claude Code Skill 実装パッケージングを下敷きに、Claude Code ドメインに特化したドメイン特化コンパイル型 Wiki。

## 目的

- **日本語話者の Claude Code 開発者** が公式ドキュメントと英語コミュニティ知見の最新情報を継続参照できる場を提供する
- LLM エージェントが週次で取得・整理し、人間レビューを経てマージする運用

## 構成

### コンテンツの2系統

1. **公式ドキュメントの整理版**（日本語）— 「要約 + 公式リンク + 補足ノート」の3部構造
2. **英語コミュニティ知見の日本語化** — Phase 3 から

### ページ5種別

- `source` — 取込み元の要約（Phase 1）
- `concept` — 複数 source 横断の概念（Phase 2）
- `entity` — ツール・コマンド・人物（Phase 2）
- `comparison` — 競合アプローチ比較（Phase 3 自動生成）
- `synthesis` — `/wiki-query` の結果保存（Phase 2）

## 操作

- `/wiki-ingest <official-url>` — 新ソース取込み
- `/wiki-regenerate <path>` — 既存 source の再生成
- `/wiki-lint` — lint 検査
- `/wiki-query <question>` — Phase 2 で追加

## 関連ドキュメント

- 設計: `docs/core/architecture.md`
- 規約: [[90_meta/frontmatter-spec]], [[90_meta/markdown-rules]]
- ADR: `docs/core/decisions.md`
