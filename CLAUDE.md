# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**LLM-Wiki for Claude Code** — Andrej Karpathy 氏が提唱した LLM-Wiki コンセプトと Reza Rezvani 氏の Claude Code Skill 実装パッケージングを下敷きに、Claude Code ドメインに特化したドメイン特化コンパイル型 Wiki プロジェクト。

LLM エージェントが週次で公式ドキュメントと英語コミュニティ知見を取得・整理し、人間レビューを経てマージすることで、Claude Code の最新セットアップ・使い方を継続的に参照できる場を提供する。

### コンテンツの2系統 × ページ5種別

ソース系統（公式 / コミュニティ）とページ種別（5種類）の2軸で分類する。

**ソース系統:**

1. **公式ドキュメントの整理版**（日本語）— Phase 2-A から **縮退仕様**（タイトル + 1 段落要約 + 公式日本語版へのリンク + AUTO 領域）を採用（ADR-017、旧 ADR-003 の 3 部構造を superseded）。Anthropic Usage Policy 遵守のため全文転載は禁止
2. **コミュニティ知見の日本語化** — Phase 2-A は awesome-claude-code 1 系統で着手したが CC BY-NC-ND 4.0 と判明し A-3 中止（ADR-016 の中止条件発動）。Phase 2-B B-3 で別系統（permissive license のリスト）に切替予定

**ページ種別（6 種別）:**

- `source` — 取込み元の要約（Phase 1〜、Phase 2-A から縮退仕様）
- `recipe` — ユースケース別の実用ドキュメント（Phase 2-A から先行投入、ADR-016 pivot）。`use_case` 必須、`sources` 最低 2 件
- `concept` — 複数 source 横断の概念（Phase 2-B から本格実装）
- `entity` — ツール・コマンド・人物（Phase 2-B から本格実装）
- `synthesis` — `/wiki-query` の結果保存（Phase 2-B から）
- `comparison` — 競合アプローチ比較（Phase 3 自動生成）

### 現在のステータス

- **Phase**: アイデア段階（実装未着手）
- **設計の単一情報源**: `docs/ideas/20260505-llm-wiki-for-claude-code.md`
- 実装言語・フレームワークは未確定（Phase 1 着手時に決定）

### 実装ロードマップ（Phase 1 / 2-A / 2-B / 3）

Phase 2 は ADR-016（2026-05-06）で 2-A（MVP）/ 2-B（拡張）に分割。ページ種別軸（コンパイル深度）と対象ソース軸（カバレッジ）の 2 軸で段階展開する。

| Phase | ページ種別軸 | 対象ソース軸 | 動作確認 |
|-------|------------|------------|---------|
| 1 | `source` のみ | 公式・hooks/cli の 2 カテゴリ | 規約準拠 source 記事 10 本、スラッシュコマンド `/wiki-ingest` `/wiki-regenerate` `/wiki-lint` 動作、冪等性確認 |
| 2-A | `+ recipe` を先行投入、`source` を縮退仕様（ADR-017）に書換 | 公式 hooks/cli の縮退 + コミュニティ 1 系統取込み（A-3 は A-7 中止条件発動で停止） | 実 Anthropic SDK 統合、AUTO マーカー最小実装、recipe 5 本、metrics 計測開始 |
| 2-B | `+ concept` `+ entity` `+ synthesis` 本格実装 | 公式の残カテゴリ + コミュニティ別系統（B-3 で再選定） | 派生ページ各最低 5 本、AUTO マーカー全展開、`/wiki-query` 動作 |
| 3 | `+ comparison`（自動生成） | 公式 + コミュニティ ホワイトリスト全系統 | 4 週連続自動 PR、修正率 30% 以下、月次運用 3 ヶ月 |

詳細は `docs/ideas/20260505-llm-wiki-for-claude-code.md` 参照。

## Architecture

### Key Directories（現在）

- `docs/`: ドキュメント
  - `docs/core/`: 中核ドキュメント（自動生成対象）
  - `docs/ideas/`: アイデア・ブレインストーミング成果物
  - `docs/plan/`: 計画ドキュメント
- `.steering/`: 作業計画・タスク管理ファイル
- `.claude/`: Claude Code 設定・スキル

### Key Directories（Phase 1 以降の予定）

- `vault/`: Obsidian Vault = Wiki コンテンツ本体（Vault と Git リポジトリは統合、ページ種別ベースの構造）
  - `vault/index.md`: ナビゲーション本体（Rezvani 由来）
  - `vault/log.md`: 全操作の追記専用ログ（Rezvani 由来）
  - `vault/overview.md`: Wiki 全体の高レベル俯瞰
  - `vault/sources/`: `type=source` 取込み元の要約（Phase 2-A から縮退仕様 / ADR-017: タイトル + 1 段落要約 + 公式リンク + AUTO 領域）
    - `vault/sources/official/`: 公式ドキュメント由来（cli, hooks, slash-commands, mcp, settings, sdk）
    - `vault/sources/community/`: コミュニティ知見由来 — Phase 2-B B-3 から本格展開（Phase 2-A の awesome-claude-code は CC BY-NC-ND 検出で停止）
  - `vault/recipes/`: `type=recipe` ユースケース別の実用ドキュメント（Phase 2-A から先行投入 / ADR-016）
  - `vault/concepts/`: `type=concept` 複数 source 横断の概念（Phase 2 から）
  - `vault/entities/`: `type=entity` ツール・コマンド・人物（Phase 2 から）
  - `vault/comparisons/`: `type=comparison` 競合アプローチ比較（Phase 3 で自動生成）
  - `vault/syntheses/`: `type=synthesis` クエリ結果の保存（Phase 2 から）
  - `vault/30_drafts/`: LLM 下書き（レビュー待ち）
  - `vault/90_meta/`: 情報源ホワイトリスト、frontmatter 規約、Markdown 規約、用語集、運用ログ
- `.claude/commands/`: スラッシュコマンド本体（明示起動の Wiki 操作）
  - `wiki-ingest.md`, `wiki-regenerate.md`, `wiki-lint.md`（Phase 1）
  - `wiki-query.md`（Phase 2 で追加）
- `.claude/skills/llm-wiki-for-claude-code/`: Claude Code Skill（規約・テンプレート・hook の共有領域、Phase 1 で雛形）
  - `SKILL.md`: Skill エントリ（コンテキストに応じて自動ロードされる規約ガイダンス）
  - `references/`: 規約・テンプレート・lint ルール（schema.md, page-templates.md, three-part-rule.md, sources-whitelist.md, lint-rules.md）
  - `hooks/session-start.md`: 起動時に index.md / log.md 直近10件をロード
- `agent/`: 環境非依存ロジック層
  - `agent/fetchers/`: 情報収集（HTTP, RSS, GitHub API 等）
  - `agent/writers/`: Markdown 生成・更新、frontmatter シリアライズ
  - `agent/validators/`: frontmatter（type 別）, 3部構成, 連続100文字一致, lint ルール
  - `agent/orchestration/`: ingest / query / lint / regenerate のユースケース実装
  - `agent/runners/`: 実行エントリポイント（local: Skill から呼ばれるラッパ / action: GitHub Actions、Phase 3）
- `.github/workflows/`: 週次 cron ワークフロー（Phase 3 で追加）

### 重要な設計方針

- **Vault = Repo**: Obsidian Vault と Git リポジトリを同一ディレクトリに統合し、同期問題を回避
- **ページ種別ベースの構造化**: Karpathy 原案の 5 種別（source / concept / entity / comparison / synthesis）に Phase 2-A で `recipe` を加えた **6 種別** を採用し、1 source から複数の派生ページが育つコンパイル構造を実現
- **`source` 種別への縮退仕様強制**（ADR-017、Phase 2-A から）: Anthropic Usage Policy / 著作権リスク回避のため、`type: source` のページは「タイトル + 1 段落要約（AUTO 領域） + 公式日本語版へのリンク」の縮退 2 セクション構造を強制（旧 ADR-003 の 3 部構成は superseded）
- **規約先行**: Phase 1 で frontmatter 規約・Markdown 制約・情報源ホワイトリストを確立してから、コンテンツ生成・自動化に進む
- **3操作 + regenerate**: `/wiki-ingest`, `/wiki-query`, `/wiki-lint`（Karpathy/Rezvani 原案）+ `/wiki-regenerate`（本プロジェクト独自）
- **信頼度スコア（confidence）**: 全ページに `confidence: 0.0-1.0` 必須化、`/wiki-lint` で 0.5 未満をフラグ
- **AUTO セクションマーカー**: `<!-- AUTO:START --> ... <!-- AUTO:END -->` で自動生成領域と人手編集領域を分離（Phase 2 で導入）
- **Slash Command と Skill の分離**: 4操作（ingest/regenerate/lint/query）は明示起動の `.claude/commands/*.md` に配置、規約・テンプレート・hook はコンテキスト自動ロードの `.claude/skills/llm-wiki-for-claude-code/` に集約。Skill 内に `commands/` サブディレクトリは置かない（公式仕様外）
- **Skill + Slash Command + 環境非依存ロジック**: スラッシュコマンドからも GitHub Actions からも `agent/orchestration` を呼ぶ二段構造
- **portability 重視の Markdown**: 標準 Markdown + Wikilinks のみ。Obsidian の Dataview や Callout など独自記法は禁止（Karpathy 原案では Dataview 推奨だが Web 公開を見据え意図的に不採用）

### Configuration

- 環境変数: `.env`（`.env.example` を参照）
- Wiki 記事の必須 frontmatter（Phase 1 で確定予定）:
  - 共通必須（全種別）: `title`, `type`, `confidence`, `sources`, `last_updated`, `stale`, `tags`
  - `type=source` のみ必須: `source_url`, `fetched_at`, `source_version`, `claude_code_version`
  - 運用メタ: `reviewer`, `human_edited`, `status`, `auto_section_managed`

## Commands

Phase 1 で確定（ADR-010）:

- **言語**: Python 3.12+
- **パッケージマネージャ**: uv 0.6+
- **テストランナー**: pytest 8.x（pytest-asyncio）
- **リンタ・フォーマッタ**: ruff 0.6+
- **型チェッカ**: mypy 1.10+ strict

```bash
# 依存導入
uv sync

# テスト
uv run pytest tests/

# Lint
uv run ruff check .

# 型チェック
uv run mypy agent

# Wiki コンテンツ検証
uv run agent validate --all
uv run agent lint --all

# Wiki 操作（Slash Command 経由でも実行可能）
uv run agent ingest --source-url <url> --category <hooks|cli|...>
uv run agent regenerate --target <path>      # AUTO 領域のみ実 LLM で再生成（既定 claude-code バックエンド）
uv run agent verify-links                    # source_url の HTTP 到達 + 連続100文字一致検査（ネットワーク依存）
```

> **`agent regenerate` の現行仕様**: ADR-018 / ADR-019（2026-05-08 accepted）で AUTO 領域のみを実 LLM 経由で再生成する設計に確定。既定バックエンドは `claude-code`（`claude` バイナリ + Max プラン認証が必要）。CI / API 利用は `WIKI_LLM_BACKEND=anthropic`、テスト・冪等性検証は `WIKI_LLM_BACKEND=stub` で切替可能。`auto_section_managed: true` のページに対して AUTO マーカー外の人手編集は保護される（`--force` 未指定時は content_hash 一致で no-op）。

CI: `.github/workflows/validate.yml` で `ruff` / `mypy` / `pytest` / `agent validate --all` を実行。
`agent verify-links` はネットワーク依存のため CI に含めない（手動 / 別ジョブで実行）。

### Phase 2-A ステータス（2026-05-06 着手）

- **規約・ADR 整備完了**: ADR-015（AUTO マーカー）/ ADR-016（Phase 2 pivot）/ ADR-017（公式 source 縮退仕様）起票、`vault/90_meta/auto-marker-spec.md` および `metrics.md` 新規作成、`frontmatter-spec.md` / `markdown-rules.md` / `sources.md` / `license-notes.md` / JSON Schema を縮退仕様 + recipe 種別対応で改訂
- **agent 層拡張完了**: `MalformedAutoMarkerError` / `ConfigurationError` / `LLMInvocationError` 新設、`anthropic>=0.40` 依存追加、`markdown_writer.py` に AUTO 領域処理（`extract_auto_regions` / `replace_auto_regions`）、`citation_validator.py` / `frontmatter_validator.py` に recipe 分岐、`orchestration/llm.py` に AnthropicBackend（mock テストで挙動検証、prompt caching 有効）、`fetchers/awesome_claude_code.py` 新設、`orchestration/regenerate.py` に AUTO 領域処理を追加（後に ADR-019 で実 LLM 呼び出しへ昇格、2026-05-08）
- **コンテンツ生成**: 公式 source 11 本（cli 6 + hooks 5）を縮退仕様に書き換え + AUTO 領域導入、recipe 5 本（claude-code-setup / hooks-introduction / permission-control-practice / post-tool-use-formatter / keybindings-customization）を新規作成
- **A-7 中止条件発動**: awesome-claude-code が CC BY-NC-ND 4.0 と判明したため A-3 を停止、`vault/90_meta/sources.md` で `enabled: false` 設定。Phase 2-B B-3 で別系統に切替予定（fetcher 実装は流用可能な状態で残置）
- **テスト件数**: Phase 1 の 107 件 → **159 件 PASS**（目標 130 件超）。`uv run ruff check .` / `uv run mypy agent` / `uv run agent validate --all`（16 本） / `uv run agent lint --all`（違反 0） すべて PASS
- **empirical 検証**: `agent regenerate` の実 LLM 経由動作確認は `claude-code` バックエンド経由で PASS 済（2026-05-08、ADR-018 / ADR-019、73.33s 実走 + 冪等性確認）。`WIKI_LLM_BACKEND=anthropic` 経由 + Slash Command のローカル動作確認は別途必要時に実施
- **`agent regenerate` 本番運用ガード解除（2026-05-08）**: ADR-018 empirical PASS（73.33s 実走確認）+ ADR-019 完了に伴い、`make_backend()` の既定値を `claude-code` に昇格。`auto_section_managed: true` のページは AUTO 領域のみ実 LLM 経由で再生成され、AUTO 外の人手編集は保護される。`status: published` ページへの実行はスラッシュコマンド側で `--force` 確認フローを保持

### Phase 1 ステータス（2026-05-06 更新）

- 規約 5 本（`vault/90_meta/{frontmatter-spec, markdown-rules, sources, license-notes, lint-rules}.md`）確立
- frontmatter JSON Schema（`vault/90_meta/_schemas/frontmatter.schema.json`）配置
- agent 層（fetchers / writers / validators / prompts / orchestration / runners）実装、ユニット + 統合 + E2E テスト **107 件 PASS**
- Slash Command 3 本（`/wiki-ingest`, `/wiki-regenerate`, `/wiki-lint`）配置
- Skill `llm-wiki-for-claude-code` 配置（`references/` は `vault/90_meta/` のシンボリックリンク、ADR-013）
- `source` 種別記事 10 本配置（hooks/ 5本、cli/ 5本）。**受入れテスト時に上流ドキュメント移行を検出**:
  - URL 移行: `https://docs.claude.com/claude-code/*` → `https://code.claude.com/docs/{en,ja}/*`（旧 URL は 301 redirect）
  - 2026-05-06: 公式日本語版（`/docs/ja/*`）の存在を確認、読者は日本人想定であることから全 source 記事の `source_url` を **日本語版へ切替**（A 案採用）
  - 既知の構成変更: `keyboard-shortcuts` セクションは `/docs/ja/cli-reference` から `/docs/ja/interactive-mode#keyboard-shortcuts` へ移動済み（`cli/keybindings.md` の `source_url` を該当ページに変更）
  - whitelist は `anthropic-claude-code-docs-ja`（主） + `anthropic-claude-code-docs-en`（補完） + `anthropic-claude-docs-legacy`（redirect 追跡）の3エントリ構成
  - 8本: `status: reviewed`, `confidence: 0.6〜0.7`（高レベルの記述は新ドキュメントと整合、Phase 2 で個別仕様の精査後 published 化）
  - 2本: `status: draft`, `stale: true`（`cli/installation.md`, `hooks/overview.md` は内容が新ドキュメントと大幅乖離、Phase 2 で全面書き直し）
- `transclusion_validator` を `validate_target` の optional `raw_content` 経由で組み込み（CI ネットワーク非依存維持）
- `agent verify-links` サブコマンド追加（`source_url` 200 確認 + 連続100文字一致検査）

## スコープ外

- Wiki 本体の Web 公開（GitHub Pages 等）— 将来別スコープ
- プレゼンテーション資料の自動生成 — 別アイデアとして切り出し
- 多言語対応（日本語のみ）
- Anthropic Routines / Schedule での実装 — Phase 3 安定後に検討

## 主要リスク（要監視）

| リスク | 影響度 | 主な対策 |
|-------|--------|---------|
| Anthropic Usage Policy / docs.claude.com 利用規約違反 | 高 | `source` 種別に3部構成（要約 + リンク + 補足）を強制、全文転載禁止 |
| Reddit API 有料化・GitHub レート制限 | 高 | 情報源ホワイトリストを Phase 1 で確定 |
| Claude Code バージョン揮発性による記事陳腐化 | 高 | `claude_code_version` を frontmatter 必須化、`/wiki-lint` で識別 |
| LLM のハルシネーション（誤った主張の混入） | 高 | `confidence` 必須化、引用必須（全主張に `sources` 紐付け）、`/wiki-lint` での矛盾検出、人間レビュー |
| 自動 PR が人手編集を上書き | 中 | AUTO セクションマーカーで領域分離（Phase 2） |
| 200ページ超えで index ベース検索が劣化 | 中 | Phase 3 以降でセマンティック検索（qmd / MCP server）導入を検討 |
| API コスト超過 | 中 | 差分検知で更新対象を絞る、prompt caching 活用 |
