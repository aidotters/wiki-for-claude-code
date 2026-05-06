# Phase 2 計画（起票）

> 作成日: 2026-05-06
> ステータス: draft（起票直後 / 詳細化未着手）
> 起点: `.steering/20260505-llm-wiki-for-claude-code/acceptance-test-report.md` の Phase 1 PASS 判定 + Phase 2 送り項目

## 背景

Phase 1（規約確立 + Skill 雛形 + 公式 hooks/cli の `source` 種別10本）は 2026-05-06 に総合判定 PASS で完了した。Phase 1 受け入れ時に発覚した上流ドキュメント移行（`docs.claude.com` → `code.claude.com/docs/{en,ja}`）と内容大幅更新により、当初予定していた一部完了条件は Phase 2 へ送られた。本ドキュメントは Phase 2 の起票として、スコープ・主要タスク・成功指標の初期案を記録する。詳細な要求定義 / 設計 / タスク化は別途同ディレクトリに `requirements.md` / `design.md` / `tasklist.md` として整備する。

## スコープ（主要 3 軸 + 拡張）

### 1. Phase 1 から引き継いだ未完了項目

- **drift 記事 2本の全面書き直し**
  - `vault/sources/official/cli/installation.md`（推奨インストール手段が `npm install -g` から `curl install.sh` ベースに変更）
  - `vault/sources/official/hooks/overview.md`（hook イベント数が 5種 → ~20種に拡大、handler type も拡張）
  - 現状 `status: draft`, `stale: true`、新ドキュメント基準で再作成して `reviewed → published` へ昇格
- **残 8本の `published` 昇格**
  - 現状 `status: reviewed`, `confidence: 0.6〜0.7`
  - 新ドキュメント基準で個別キー仕様を精査し、`confidence ≥ 0.7` + `status: published` を満たす
- **実 LLM（Anthropic SDK）統合**
  - 現状 `agent regenerate` はスタブ LLM。本番運用記事に対しては「呼ばない」運用ガード中
  - Anthropic SDK 統合により、要約 + 補足解説の自動再生成を実現
  - prompt caching 活用（コスト最適化）
  - `agent verify-links` を CI（別ジョブ・許容失敗）に組込み検討

### 2. ページ種別の拡張（Karpathy 原案の 5 種別フル対応）

- `concept` 種別の実装（複数 source 横断の概念ページ）
- `entity` 種別の実装（ツール・コマンド・人物）
- `synthesis` 種別の実装（`/wiki-query` の結果保存）
- `comparison` は Phase 3 自動生成へ送り（Phase 2 ではスキーマ整備のみ）
- 各種別の frontmatter 規約・テンプレート・lint ルール拡充

### 3. 公式ドキュメント全 6 カテゴリへの展開

- `vault/sources/official/slash-commands/`
- `vault/sources/official/mcp/`
- `vault/sources/official/settings/`
- `vault/sources/official/sdk/`
- 各カテゴリ最低 5 本以上の `source` 種別記事

### 4. その他 Phase 2 で着手する周辺機能

- **AUTO セクションマーカー**（`<!-- AUTO:START --> ... <!-- AUTO:END -->`）の仕様確定 + 既存記事への適用
  - 自動生成領域と人手編集領域の分離
- **`/wiki-query` コマンド**の実装
  - クエリ → 関連 source / concept / entity ページ集約 → `synthesis` 種別として保存
- **人手レビュー工数の実測**（`metrics.md`）
- `agent verify-links` の CI 別ジョブ統合（許容失敗で URL/内容 drift を継続監視）

## スコープ外（Phase 3 へ送り）

- `comparison` 種別の自動生成
- `vault/sources/community/` 配下の記事作成（コミュニティソース取り込み）
- GitHub Actions 週次 cron + `agent/runners/action.py` の実装
- CODEOWNERS / PR テンプレート整備
- API コスト・運用ログ（`cost-log.md`）
- Anthropic ブログ RSS / GitHub Releases 等のフェッチャ実装

## 成功指標（初期案）

- **drift 記事 2本** が新ドキュメント基準で全面書き直し完了し、`status: published`, `confidence ≥ 0.7` に昇格
- **既存 8本 + drift 2本 = 計10本** が `status: published`, `confidence ≥ 0.7` を満たす
- **公式 全 6 カテゴリ** で各最低 5 本以上の `source` 種別記事が存在
- **実 LLM 統合**: `agent regenerate` が実 Anthropic SDK 経由で動作、本番運用記事に対しても安全に再生成可能
- **派生ページ種別** `concept` / `entity` / `synthesis` の各最低 5 本が存在
- **AUTO セクションマーカー**仕様が確定し、`/wiki-regenerate` が AUTO 領域のみを更新する動作を確認
- **`/wiki-query`** コマンドが Claude Code から起動可能で、結果が `vault/syntheses/` 配下に保存される
- **`agent verify-links`** が CI（別ジョブ・許容失敗）で動作し、URL/内容 drift を週次以上の頻度で検出可能
- 関係する PRD 機能（Phase 1 の機能 1〜9 を超える拡張）の受け入れ条件をすべて満たす

## 前提・依存

- Phase 1 で確立した規約（`vault/90_meta/{frontmatter-spec, markdown-rules, sources, license-notes, lint-rules}.md`）を継承
- Phase 1 の agent 層（`fetchers/`, `writers/`, `validators/`, `orchestration/`, `runners/`）を継承・拡張
- Anthropic API キー（`ANTHROPIC_API_KEY`）の運用準備（個人キー or 組織キー、コスト上限・モニタリング体制）
- `code.claude.com/docs/ja/*` の URL 構造維持（再度 redirect が発生した場合は再対応）

## リスクと対策（初期案）

| リスク | 影響度 | 対策方針 |
|-------|-------|---------|
| Anthropic API コスト超過 | 中 | prompt caching 活用、差分検知で更新対象を絞る、月次予算上限を `cost-log.md` で監視（Phase 3 で本格運用） |
| LLM ハルシネーション混入（実 LLM 統合後） | 高 | `confidence` 必須化を継続、引用必須、`/wiki-lint` の矛盾検出強化、人手レビューゲート維持 |
| AUTO マーカーで自動更新領域と人手編集領域の境界が曖昧化 | 中 | Phase 2 着手前に仕様を ADR 化、テストで境界制御を担保 |
| 公式ドキュメントの再 redirect / 内容大変動 | 高 | `agent verify-links` を CI 統合し週次で検出、`stale: true` フラグで運用 |
| ページ種別拡張で既存 source 規約と競合 | 中 | 種別別 JSON Schema を分離、`type` 別 validator 経路を明確化 |

## マイルストーン（初期案）

1. **要件定義 + 設計**（このディレクトリ配下に `requirements.md` / `design.md` を整備）
2. **drift 記事 2本書き直し + 既存 8本 published 昇格**（実 LLM 統合より先に手動レビュー込みで整える）
3. **実 LLM（Anthropic SDK）統合**: `agent regenerate` のスタブ置き換え、prompt caching、コスト計測
4. **公式 全 6 カテゴリ展開**: 各カテゴリ最低 5 本の `source` 種別記事生成
5. **派生ページ種別実装**: `concept` / `entity` / `synthesis` の規約・テンプレート・lint 拡充
6. **AUTO セクションマーカー** 仕様確定 + `/wiki-regenerate` 動作変更
7. **`/wiki-query` コマンド** 実装、`vault/syntheses/` 配下に結果保存
8. **`agent verify-links` を CI 別ジョブ統合**
9. **受入れテスト**: Phase 1 と同様の自動 + 手動チェックで PASS 化

## 残タスク（このドキュメント以降の起票作業）

- [ ] `.steering/20260506-llm-wiki-for-claude-code-phase-2/requirements.md` の作成（受け入れ条件の詳細化）
- [ ] `.steering/20260506-llm-wiki-for-claude-code-phase-2/design.md` の作成（実 LLM 統合・派生ページ種別の設計）
- [ ] `.steering/20260506-llm-wiki-for-claude-code-phase-2/tasklist.md` の作成（マイルストーン別の実装タスク分解）
- [ ] CLAUDE.md の Phase 1 → Phase 2 への遷移更新（Phase 1 完了マークと Phase 2 着手宣言）

## 参照ドキュメント

- `.steering/20260505-llm-wiki-for-claude-code/acceptance-test-report.md` — Phase 1 受け入れテストレポート（PASS / 2026-05-06）
- `.steering/20260505-llm-wiki-for-claude-code/requirements.md` — Phase 1 受け入れ条件（line 192 = Phase 2 送り項目）
- `docs/ideas/20260505-llm-wiki-for-claude-code.md` — 元アイデアファイル（ステータス: verified / 2026-05-06）
- `CLAUDE.md` — Phase 1 ステータス（実装ロードマップ表参照）
