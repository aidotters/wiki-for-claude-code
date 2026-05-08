# 要求内容（Phase 2-A: MVP / pivot 後）

> 作成日: 2026-05-06
> ステータス: draft（plan-feature 起票直後）
> 起点: `docs/ideas/20260505-llm-wiki-for-claude-code.md`（pivot 反映 / 2026-05-06）+ `~/.claude/plans/synchronous-tickling-dragon.md`
> 関連: `.steering/20260506-llm-wiki-for-claude-code-phase-2/`（pivot 前の旧 Phase 2 計画 / 参考用に保持）

## 概要

Phase 2 を A（MVP）/ B（拡張）に分割した上で、**Phase 2-A** として「実 Anthropic SDK 統合 + 公式 source 縮退 + コミュニティ source 1 系統取り込み + `recipe` 種別先行 + AUTO マーカー最小実装 + metrics 計測開始」を End-to-End で通し、新方針（コミュニティ知見の自動整理 + 横断的実用ドキュメント生成）の付加価値を最小コストで検証する。

## 背景

### pivot の経緯

Phase 1 受け入れテスト（2026-05-06 PASS）時に上流ドキュメント大規模移行を検出し、その過程で **公式日本語版（`code.claude.com/docs/ja/*`）** の存在を確認した。これにより当初の前提「公式は英語のみ → 日本語素訳に付加価値あり」が崩れ、`vault/sources/official/` の 10 本は「公式日本語ページの劣化コピー」化するリスクが顕在化した。

本来の付加価値は次のように再定義された:

- **コミュニティに散らばる実践知（英語コミュニティ + 個人発信）の定期整理 + 横断視点での再構成**
- **ユースケース別 Tips / セットアップ手順 / チートシートといった、公式リファレンスにない目的志向ドキュメント**
- **Claude が引くインデックス（A-3 用途）への構造化情報供給**

Phase 2 を A/B に分割し、Phase 2-A（本書）で MVP 検証 → metrics 結果を Phase 2-B 着手判断の入力にする。

### Phase 1 から継承する資産

- `vault/90_meta/{frontmatter-spec, markdown-rules, sources, license-notes, lint-rules}.md`（規約 5 本）
- `vault/90_meta/_schemas/frontmatter.schema.json`
- `agent/{fetchers, writers, validators, prompts, orchestration, runners}` 実装 + テスト 107 件 PASS
- `.claude/commands/{wiki-ingest, wiki-regenerate, wiki-lint}.md`
- `.claude/skills/llm-wiki-for-claude-code/{SKILL.md, references/, hooks/session-start.md}`
- `vault/sources/official/{cli,hooks}/*.md` 10 本（縮退の入力素材）

### Phase 2-A での pivot 反映ポイント

- `source` 種別の **3 部構成強制を撤回**、縮退仕様（タイトル + 1 段落要約 + 公式リンク + AUTO 領域）に書き換え
- 公式 6 カテゴリ展開（旧 Phase 2 機能 5）と drift 記事 2 本の全面書き直し（旧機能 1）は **撤回**
- ページ種別を 5 → 6 種別に拡張（`recipe` を追加 / `guide` `cheatsheet` は Phase 2-B/3 送り）
- コミュニティ source 取り込みを Phase 3 → Phase 2-A に前倒し（awesome-claude-code 1 系統のみ）

## 実装対象の機能

### A-1. 実 Anthropic SDK 統合（カリーオーバー解消）

- `agent/orchestration/llm.py` のスタブを Anthropic SDK 呼び出しに置換
- モデル: Sonnet 4.6 既定（`claude-sonnet-4-6`）、prompt caching 有効化
- `WIKI_LLM_BACKEND=stub|anthropic` 環境変数で切替（既定: `stub`、Phase 2-A 後半に `anthropic` 既定へ）
- `ANTHROPIC_API_KEY` 必須化（未設定時は exit code 3）
- `agent regenerate` の本番運用ガード（`CLAUDE.md` 注記）を解除

### A-2. 公式 source の縮退（10 本一括処理）

- `vault/sources/official/{cli,hooks}/*.md` 10 本を **縮退仕様**（タイトル + 1 段落要約 + 公式リンク + AUTO 領域）に書き換え
- 3 部構成強制ルール（`vault/90_meta/markdown-rules.md`, `.claude/skills/llm-wiki-for-claude-code/references/three-part-rule.md`）から `source` 種別を除外、または縮退版仕様に書き換え
- drift 記事 2 本（`cli/installation.md`, `hooks/overview.md`）は AUTO 領域再生成で drift 解消
- 既存 8 本は縮退仕様で `confidence ≥ 0.7` を再評価、`status: published` に昇格

### A-3. コミュニティ source 1 系統の取り込み（awesome-claude-code）

- `vault/90_meta/sources.md` のホワイトリストに `awesome-claude-code` を追加（取得方式・ライセンス・レート制限を明記）
- `vault/90_meta/license-notes.md` に awesome-claude-code のライセンス整理を追記
- `agent/fetchers/` に awesome-claude-code 用 fetcher を追加（GitHub README 構造化リスト = 既存 HTTP fetcher の延長で対応）
- `vault/sources/community/awesome-claude-code/` 配下に最低 5 本の `type: source` 記事を生成
- 各記事の `sources` に上流 URL + コミット SHA を記録

### A-4. `recipe` 種別の先行検証

- `vault/90_meta/frontmatter-spec.md` に `recipe` 種別の必須キーを追記（共通 + `use_case`, `sources` ≥ 2 件）
- `vault/90_meta/_schemas/frontmatter.schema.json` の `oneOf` に `recipe` 分岐を追加
- `agent/validators/frontmatter_validator.py` に `recipe` 分岐を実装
- `agent/validators/citation_validator.py` で `recipe` の `sources` ≥ 2 件を強制
- `.claude/skills/llm-wiki-for-claude-code/references/page-templates.md` に `recipe` テンプレートを追加
- `vault/recipes/` 配下に **5 本以上** 配置（例: 「Claude Code セットアップ」「Hooks 入門」「MCP 連携 Tips」「権限制御の実践」「複数モデル切替」）
- 全件 `confidence ≥ 0.7`, `status: published`, `citation_validator` PASS

### A-5. AUTO マーカー（最小実装）

- `vault/90_meta/auto-marker-spec.md` を新規作成し、AUTO 構文（`<!-- AUTO:START --> ... <!-- AUTO:END -->`）と境界制御の規約を確定
- ADR-015（AUTO マーカー構文確定）として `docs/core/decisions.md` に起票
- `agent/writers/markdown_writer.py` を拡張: AUTO 領域抽出 + 領域外バイト一致保持ロジックを実装
- `vault/sources/official/{cli,hooks}/*.md` 10 本（A-2）+ `vault/recipes/*.md` 5 本（A-4）= **計 15 本** に AUTO 領域を導入
- バイト一致保持テスト（unit + integration）

### A-6. metrics 計測の開始

- `vault/90_meta/metrics.md` を新規作成
- A-2〜A-4 で生成・レビューした全記事について `(記事パス, 生成日時, レビュー時間, レビュアー, 自動修正件数, 人手修正件数)` を記録
- Phase 2-A 完了時に集計し、修正率・平均レビュー時間を算出

### A-7. Phase 2-A の中止条件（運用ガード）

以下のいずれかに該当した時点で Phase 2-B 着手前に再計画する:

- 修正率（人手修正件数 / 全件数）が **50% を超える**
- LLM コストが **想定の 2 倍を超える**
- A-3 の awesome-claude-code 取り込みでライセンス問題が発見される

## 受け入れ条件

### A-1: 実 Anthropic SDK 統合

- [ ] `agent/orchestration/llm.py` が Anthropic SDK 呼び出し実装に置換され、`stub` バックエンドと並列で選択可能
- [ ] `WIKI_LLM_BACKEND=anthropic uv run agent regenerate --target vault/recipes/<sample>.md` が成功する
- [ ] prompt caching が有効化され、連続 2 回目の同一ターゲット regenerate でトークンコストが減少することをログで確認
- [ ] `ANTHROPIC_API_KEY` 未設定時は exit code 3 で終了し、エラーメッセージで API キー欠落を明示
- [ ] モデル既定が `claude-sonnet-4-6`（環境変数 `WIKI_LLM_MODEL` で上書き可能）
- [ ] `CLAUDE.md` の `agent regenerate` 本番運用ガード注記が削除されている

### A-2: 公式 source 縮退

- [ ] `vault/sources/official/{cli,hooks}/*.md` 10 本が縮退仕様（タイトル + 1 段落要約 + 公式リンク + AUTO 領域）に書き換え済み
- [ ] 全 10 本が `agent validate --all` PASS、`confidence ≥ 0.7`, `status: published`, AUTO マーカー反映済み
- [ ] drift 記事 2 本（`cli/installation.md`, `hooks/overview.md`）の `stale: true` フラグが解除される
- [ ] `vault/90_meta/markdown-rules.md` および `.claude/skills/llm-wiki-for-claude-code/references/three-part-rule.md` が縮退仕様（または `source` 除外）に書き換え済み
- [ ] 旧 3 部構成（補足解説）を要求するテスト・lint ルールが縮退仕様に置換されている

### A-3: コミュニティ source 1 系統取り込み

- [ ] `vault/90_meta/sources.md` のホワイトリストに `awesome-claude-code` エントリ（URL / 取得方式 / ライセンス / レート制限）が追加されている
- [ ] `vault/90_meta/license-notes.md` に awesome-claude-code のライセンスと引用方針が記載されている
- [ ] `agent/fetchers/` に awesome-claude-code 用 fetcher が実装され、ユニットテストが PASS
- [ ] `uv run agent ingest --source-url <awesome-claude-code-entry-url> --category awesome-claude-code` が成功する
- [ ] `vault/sources/community/awesome-claude-code/` 配下に **最低 5 本** の `type: source` 記事が生成される
- [ ] 全 5 本が `agent validate` PASS、`sources` に上流 URL + コミット SHA が記録されている

### A-4: `recipe` 種別先行

- [ ] `vault/90_meta/frontmatter-spec.md` に `recipe` 種別の必須キー（`use_case`, `sources` ≥ 2 件 等）が追記されている
- [ ] `vault/90_meta/_schemas/frontmatter.schema.json` の `oneOf` に `recipe` 分岐が追加され、JSON Schema validation で recipe ページが PASS
- [ ] `agent/validators/frontmatter_validator.py` が `recipe` の必須キーを検証する
- [ ] `agent/validators/citation_validator.py` が `recipe` の `sources ≥ 2` を強制する
- [ ] `.claude/skills/llm-wiki-for-claude-code/references/page-templates.md` に `recipe` テンプレートが追加されている
- [ ] `vault/recipes/` 配下に **5 本以上** の `type: recipe` 記事が配置され、全件 `confidence ≥ 0.7`, `status: published`, `citation_validator` PASS
- [ ] 各 recipe の `sources` に最低 2 件の wikilink（`vault/sources/` 配下）が含まれる

### A-5: AUTO マーカー（最小実装）

- [ ] `vault/90_meta/auto-marker-spec.md` が新規作成され、AUTO 構文と境界制御規約が確定している
- [ ] ADR-015（AUTO マーカー構文確定）が `docs/core/decisions.md` に起票されている
- [ ] `agent/writers/markdown_writer.py` に AUTO 領域抽出 + 領域外バイト一致保持ロジックが実装されている
- [ ] AUTO 領域外を意図的に編集後 `agent regenerate` を実行しても、領域外がバイト単位で保持されることをテストで確認
- [ ] 公式 source 10 本 + recipe 5 本 = 計 15 本に AUTO 領域が導入されている
- [ ] AUTO 構文が無効（START/END の対応不一致など）な場合、Writer が明示的にエラーを返す

### A-6: metrics 計測開始

- [ ] `vault/90_meta/metrics.md` が新規作成され、列定義（記事パス / 生成日時 / レビュー時間 / レビュアー / 自動修正件数 / 人手修正件数）が記載されている
- [ ] A-2〜A-4 で生成・レビューした全記事の計測値が `vault/90_meta/metrics.md` に記録されている
- [ ] Phase 2-A 完了時に修正率（人手修正件数 / 全件数）が算出されている

### A-7: 中止条件モニタリング

- [ ] 中止条件（修正率 50% 超 / LLM コスト 2 倍超 / ライセンス問題発見）が `vault/90_meta/metrics.md` または別ドキュメントで監視可能な形で記録されている
- [ ] 中止条件のいずれかに該当した場合、Phase 2-B 着手前に `.steering/20260506-llm-wiki-for-claude-code-phase-2a/` 配下に再計画ノートを残す運用が明記されている

### 共通: テスト・CI・ADR

- [ ] agent 層の自動テスト件数が **130 件以上**（Phase 1: 107 件 + Phase 2-A 増分）に拡大、全 PASS
- [ ] `uv run pytest tests/` 全 PASS
- [ ] `uv run ruff check .` PASS
- [ ] `uv run mypy agent` PASS
- [ ] `uv run agent validate --all` PASS（公式 10 本 + community 5 本 + recipe 5 本 = 計 20 本以上）
- [ ] `uv run agent lint --all` PASS（confidence < 0.5 ゼロ、孤立ページゼロ、broken wikilink ゼロ）
- [ ] CI（`.github/workflows/validate.yml`）で recipe 種別記事も検証対象に含まれる
- [ ] ADR-015（AUTO マーカー）/ ADR-016（Phase 2 pivot 決定）/ ADR-017（公式 source 縮退仕様）が `docs/core/decisions.md` に起票されている

### Slash Command / Skill 動作

- [ ] ローカル Claude Code から `/wiki-ingest <awesome-claude-code-url>` で community 記事生成
- [ ] `/wiki-regenerate vault/recipes/<sample>.md` で AUTO 領域のみが更新される（領域外バイト一致保持）
- [ ] `/wiki-lint` で全 20 本以上が PASS
- [ ] Skill `references/page-templates.md` が context-aware に自動ロードされ、recipe テンプレートが参照可能

## 成功指標

### 定量指標

- **記事数**: 公式 source 縮退 10 本 + community source 5 本以上 + recipe 5 本以上 = **計 20 本以上**
- **テスト件数**: 130 件以上 PASS
- **修正率**: 人手修正件数 / 全件数 ≤ **50%**（中止条件閾値）
- **LLM コスト**: 想定の **2 倍以下**（中止条件閾値、想定値は ADR-015/016 起票時に確定）
- **prompt caching 効果**: 連続 2 回目 regenerate でトークンコスト減少をログで確認

### 定性指標

- 新方針（コミュニティ知見整理 + 横断的実用ドキュメント）の付加価値が `vault/recipes/` 5 本で具体的に示される
- AUTO マーカーで人手編集領域が保護されることが体感できる
- Phase 2-B 着手判断の入力（metrics + 修正率）が揃う

## スコープ外

以下は Phase 2-A では実装しない:

- **`concept` / `entity` / `synthesis` 種別の本格実装** → Phase 2-B（B-1）
- **`/wiki-query` コマンド実装** → Phase 2-B（B-2）
- **コミュニティ source の追加系統**（GitHub Releases / Anthropic blog RSS / Karpathy・Rezvani 等の個人発信） → Phase 2-B（B-3）
- **fetcher の拡張**（HTML 構造ベース → RSS / JSON API ベース） → Phase 2-B（B-3）
- **Claude エコシステム拡張カテゴリ**（`vault/sources/official/{claude-design, skills, agent-sdk}/`） → Phase 2-B（B-4）
- **`agent verify-links` の CI 別ジョブ統合** → Phase 2-B（B-5）
- **AUTO マーカーの全 source 記事への展開**（Phase 2-A は 15 本のみ） → Phase 2-B（B-6）
- **`guide` / `cheatsheet` 種別追加** → Phase 3
- **X/Twitter / Reddit / 個人ブログ fetcher** → Phase 3
- **公式 6 カテゴリの面的整備**（旧 Phase 2 機能 5）— 撤回
- **drift 記事 2 本の全面書き直し**（旧 Phase 2 機能 1）— 縮退仕様で代替
- **GitHub Actions 週次 cron + 自動 PR** → Phase 3
- **`comparison` 種別自動生成** → Phase 3

## 主要リスク

| リスク | 影響度 | 対策方針 |
|-------|-------|---------|
| Anthropic API コスト超過 | 中 | prompt caching 活用、差分検知、`metrics.md` で実測、A-7 中止条件で 2 倍超を検知 |
| LLM ハルシネーション混入（実 LLM 統合後） | 高 | `confidence` 必須化継続、引用必須、`/wiki-lint` の矛盾検出、人手レビューゲート維持、metrics で修正率監視 |
| AUTO マーカー境界の曖昧化 | 中 | ADR-015 で仕様確定、Writer に境界制御テスト、領域外バイト一致テストで担保 |
| awesome-claude-code のライセンス問題 | 高 | A-3 着手前に `vault/90_meta/license-notes.md` で整理、不適合の場合は別系統に切替 |
| `recipe` 種別のハルシネーション率上昇 | 中 | `sources ≥ 2` 強制、`citation_validator` PASS 必須、初回 5 本は人手レビュー必須 |
| 公式日本語版の再 redirect / URL 構造変動 | 高 | Phase 2-B の `agent verify-links` CI 統合まではローカル手動チェック運用 |
| ページ種別拡張で既存 source 規約と競合 | 中 | 種別別 JSON Schema を分離、`type` 別 validator 経路を明確化（Phase 1 の構造を継続） |
| Phase 2-A スコープのインフレ | 中 | A-1〜A-7 の境界を厳守、A-7 中止条件で再計画判断 |

## 参照ドキュメント

- `docs/ideas/20260505-llm-wiki-for-claude-code.md` — 元アイデア（pivot 反映 / 2026-05-06）
- `~/.claude/plans/synchronous-tickling-dragon.md` — Phase 2 pivot 提案 plan（実装計画詳細）
- `.steering/20260505-llm-wiki-for-claude-code/` — Phase 1 受入れテスト・要件定義
- `.steering/20260506-llm-wiki-for-claude-code-phase-2/` — pivot 前の旧 Phase 2 計画（参考用）
- `docs/core/decisions.md` — ADR 一覧（ADR-001〜014 を継承、ADR-015/016/017 を本フェーズで起票）
- `docs/core/architecture.md` — レイヤー構成（agent / Skill / Slash Command）
- `docs/core/development-guidelines.md` — コーディング規約
- `docs/core/repository-structure.md` — ディレクトリ配置規約
- `CLAUDE.md` — プロジェクト概観・Phase 1 ステータス
- `vault/90_meta/{frontmatter-spec, markdown-rules, sources, license-notes, lint-rules}.md` — Phase 1 確立規約 5 本
