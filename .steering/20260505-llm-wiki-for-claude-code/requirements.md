# 要求内容

## 概要

LLM-Wiki for Claude Code プロジェクトの **Phase 1（規約確立 + Skill 雛形 + 公式 hooks/cli の `source` 種別10本）** を実装する。
具体的には以下の5点を完成させる:

1. Obsidian Vault 兼 Git リポジトリの `vault/` ディレクトリ構造（ページ種別ベース）を確立する
2. `vault/90_meta/` に運用規約5点（frontmatter, Markdown, ホワイトリスト, ライセンス, lint ルール）を制定する
3. `vault/sources/official/hooks/` および `vault/sources/official/cli/` に規約準拠の `type: source` 記事を **合計10本** 作成する（`status: published`）
4. `.claude/commands/wiki-{ingest,regenerate,lint}.md` のスラッシュコマンド3本と、`.claude/skills/llm-wiki-for-claude-code/`（`SKILL.md` + `references/` + `hooks/`）を配置し、`/wiki-ingest` `/wiki-regenerate` `/wiki-lint` がローカルで動作する（ADR-014: Skill 内に `commands/` サブディレクトリは置かない）
5. `agent/runners/local.{ts|py}` の最小実装で Skill から呼ばれる `ingest` `regenerate` `lint` `validate` サブコマンドを構築し、`regenerate` で **冪等な再生成** が動作する

> **本計画のスコープ外**: Phase 2 (AUTO セクションマーカー、`concept` / `entity` / `synthesis` 種別追加、`/wiki-query`、公式全6カテゴリ展開、人手レビュー工数実測)、Phase 3 (GitHub Actions 自動化、コミュニティソース取り込み、`comparison` 自動生成)。これらは Phase 1 完了後に別計画として作成する。

## 背景

### 現状の課題（アイデアファイルより）

- **公式ドキュメント追従困難**: Claude Code は機能追加・変更が早く、日本語話者向けの構造化された参照場所が存在しない
- **規約未整備状態でコンテンツを増やす危険性**: 規約に違反したコンテンツが大量にある状態を作ると後の手戻りが大きい（ADR-005）
- **エージェント基盤・Slash Command / Skill パッケージ未着手**: `src/`, `scripts/` は空。`agent/` ディレクトリも `.claude/commands/wiki-*.md` も `.claude/skills/` 配下の Skill も未作成

### Phase 1 が解決すること

- Wiki の **骨格と規約**（ページ種別5種類のうち `source` のみ）を確立する（Phase 2 以降の派生ページ展開が依存する基盤）
- **`.claude/commands/` のスラッシュコマンド + Skill `references/`/`hooks/`** を組み合わせ、`/wiki-*` をローカル開発の入り口として整える
- 規約準拠の **少量コンテンツ**（10本）で規約を試運転し、運用面の課題を洗い出す
- ローカル開発環境で **冪等動作する再生成（regenerate）** を構築し、Phase 3 の GitHub Actions エントリポイントの土台を作る

### 関連 ADR

- **ADR-001**: Karpathy LLM-Wiki + Rezvani Skill 構造を踏まえたドメイン特化コンパイル型 Wiki 採用（折衷案）
- **ADR-002**: Vault = Repo（Obsidian Vault と Git リポジトリ統合）
- **ADR-003**: `source` 種別に「要約 + リンク + 補足」3部構成を強制（Anthropic Usage Policy 対応）
- **ADR-004**: 標準 Markdown + Wikilinks のみ（Obsidian 独自記法禁止、Karpathy 推奨の Dataview も意図的に不採用）
- **ADR-005**: 規約先行（本 Phase の根拠）
- **ADR-007**: 開発フェーズはローカル Claude Code 実行（Slash Command 経由）
- **ADR-008**: 情報源ホワイトリスト方式
- **ADR-011**: ページ種別5種類（source / concept / entity / comparison / synthesis）採用
- **ADR-012**: Claude Code Skill としてパッケージング（ADR-014 で構造を改訂）
- **ADR-014**: Slash Command と Skill を分離して配置（Skill 内 `commands/` サブディレクトリは公式仕様外のため不採用）

## 実装対象の機能

### 1. Vault ディレクトリ構造の確立（PRD 機能1）

- `vault/` 配下にページ種別ベースの構造を作成する:
  - ナビゲーション: `index.md`, `log.md`, `overview.md`（雛形）
  - `sources/official/{cli,hooks,slash-commands,mcp,settings,sdk}/`
  - `sources/community/{tips,workflows,integrations,troubleshooting}/`
  - `concepts/`, `entities/`, `comparisons/`, `syntheses/`
  - `30_drafts/`, `90_meta/`
- Phase 1 で実コンテンツを置くのは `sources/official/{cli,hooks}/`, `90_meta/`, ナビゲーション3点の4箇所。それ以外は空ディレクトリ + `.gitkeep` で確保する
- Obsidian Vault として認識される最小構成（`.obsidian/` の最小設定 + `.gitignore` で個別設定を除外）を含める

### 2. frontmatter 規約の確立（PRD 機能2）

- `vault/90_meta/frontmatter-spec.md` に以下を記載:
  - **共通必須キー（全種別）**: `title`（必須）, `type`（必須, enum: source/concept/entity/comparison/synthesis）, `confidence`（必須, 0.0-1.0）, `sources`（必須, wikilink 配列）, `last_updated`（必須）, `stale`（必須, bool）, `tags`（必須, 配列）
  - **`type=source` のみ必須**: `source_url`（必須）, `fetched_at`（必須, ISO 8601）, `source_version`（任意）, `claude_code_version`（必須, SemVer）
  - **運用メタ**: `reviewer`（必須）, `human_edited`（必須, bool）, `status`（必須, enum）, `auto_section_managed`（必須, bool）
- `status` の遷移規則: `draft → reviewed → published` の単方向
- `vault/90_meta/_schemas/frontmatter.schema.json` に `type` 別の JSON Schema を配置
- `agent/validators/frontmatter_validator` を実装し、規約違反を CLI から検出可能にする

### 3. Markdown 制約の確立（PRD 機能5）

- `vault/90_meta/markdown-rules.md` に以下を記載:
  - 許可記法: 標準 Markdown（CommonMark）+ Wikilinks（`[[file-name]]`）+ Mermaid
  - 禁止記法: Obsidian Dataview, Callout（`> [!note]` 等）、Obsidian 独自の埋め込み記法
  - **`source` 種別** の3部構成（「## 概要 (要約)」「## 公式ドキュメント」「## 補足解説 (日本語)」）の強制
  - 派生種別（concept/entity 等）は引用必須のみで構成は自由
- Markdown 制約の規約違反検出スクリプトを `agent/validators/markdown_rules_validator`, `three_part_validator`, `citation_validator` として実装する

### 4. 情報源ホワイトリストの確立（PRD 機能4）

- `vault/90_meta/sources.md` に Phase 1 で使用する情報源（最低限 `anthropic-claude-docs`）の YAML ブロック形式リストを記載する
- 各ソースに `id`, `name`, `base_url`, `fetch_method`, `rate_limit`, `license_notes`, `enabled` を必須記載する
- `vault/90_meta/license-notes.md` に Anthropic Usage Policy / docs.claude.com 利用規約の要点と「全文転載禁止」原則を整理する

### 5. lint ルールの確立（PRD 機能新規）

- `vault/90_meta/lint-rules.md` に以下の検出項目を記載:
  - 孤立ページ（インバウンドの wikilinks がないページ）
  - 陳腐化（`stale: true` または `last_updated` が30日超）
  - 矛盾（同じトピックの複数ページで主張不一致）
  - 低信頼度（`confidence < 0.5`）
  - 不足ページ（既存 wikilinks の到達先が存在しない）
  - index 同期（全ページが `index.md` に表示されているか）
- `agent/validators/lint_validator` を実装する

### 6. `source` 種別記事10本作成（PRD 機能3）

- `vault/sources/official/hooks/` および `vault/sources/official/cli/` に規約準拠記事を合計10本（最低各カテゴリ4本以上、合計10本）作成する
- 全記事が以下を満たす:
  - `type: source` であり、共通必須 + source 種別必須の frontmatter キーが揃っている
  - 「## 概要 (要約)」「## 公式ドキュメント」「## 補足解説 (日本語)」の3セクションを持つ
  - 「## 公式ドキュメント」セクションに `→ {URL}（最終確認: YYYY-MM-DD / 対象バージョン: X.Y.Z）` の形式で公式リンクと最終確認日が記載されている
  - 連続100文字以上の公式コンテンツ一致がない（全文転載禁止）
- 内容妥当性が確認できた記事は `status: reviewed`, `confidence ≥ 0.6` を満たす（人手レビュー証跡として `human_edited: true`, `reviewer` を設定）
- `published` への昇格は実 LLM 統合（Phase 2/3）後に内容を最新公式ドキュメントに対して再生成・精査して行う（Phase 1 完了条件外）
- 上流ドキュメントとの内容乖離が検出された記事は `status: draft`, `stale: true` を維持し、frontmatter コメントに drift 内容を記録（Phase 2 で全面書き直し）
- `agent ingest` または `agent regenerate` で生成可能（regenerate は実 LLM 統合まで運用記事に対して呼ばない）

> **2026-05-06 改訂理由**: 受入れテスト時に上流公式ドキュメントが `docs.claude.com/claude-code/*` →
> `code.claude.com/docs/{en,ja}/*` に移行し、内容も大幅に更新されていることが判明。当初の「published / confidence ≥ 0.7」
> 目標は内容の最新性を前提としていたため、その前提が崩れた段階での `published` 化は誤情報の固定化となる。
> Phase 1 完了条件を「人手レビュー済み構造（reviewed / 0.6）」に再調整し、`published` を Phase 2 へ送る。
>
> **2026-05-06 追補**: 同日、公式日本語版（`/docs/ja/*`）の存在を確認。読者は日本人想定であることから
> 全 source 記事の `source_url` を日本語版へ切替（A 案採用）。whitelist は `anthropic-claude-code-docs-ja`（主） +
> `anthropic-claude-code-docs-en`（補完） + legacy（redirect 追跡）の3エントリ構成に再編。これにより
> 「公式ドキュメント」セクションのリンク先も日本語ページとなり、読者体験が改善される。

### 7. Slash Command + Skill パッケージの配置（PRD 機能新規、ADR-014）

- **Slash Command 層**: `.claude/commands/wiki-ingest.md`, `wiki-regenerate.md`, `wiki-lint.md` を配置（自然言語の指示書として記述し、内部で `agent <subcommand>` を呼ぶ）
- **Skill 層**: `.claude/skills/llm-wiki-for-claude-code/SKILL.md` を配置（`name`, `description`, `triggers` を含む。`description` は Wiki ページ編集時に context-aware にロードされる旨を含む）
- **Skill 内に `commands/` サブディレクトリは置かない**（公式仕様外のため）
- `.claude/skills/llm-wiki-for-claude-code/references/` 配下を `vault/90_meta/` のシンボリックリンクで構成（schema, three-part-rule, sources-whitelist, lint-rules）
- `references/page-templates.md` に `source` 種別のテンプレート実体（他種別はスタブ）
- `.claude/skills/llm-wiki-for-claude-code/hooks/session-start.md` で起動時に `vault/index.md` と `vault/log.md` 直近10件をロード
- Claude Code から `/wiki-ingest`, `/wiki-regenerate`, `/wiki-lint` で起動可能なことを確認

### 8. ローカル CLI による記事 ingest/regenerate/lint の最小実装（PRD 機能6）

- `agent/runners/local.{ts|py}` に以下のサブコマンドを実装する:
  - `agent ingest --source-url <url> --category <hooks|cli>`: 新ソース取込み
  - `agent regenerate --target <path>`: 既存 source の再生成
  - `agent lint --all`: lint 検査
  - `agent validate --all`: 機械的検証（CI 用）
  - `agent validate --target <path>`: 単記事 CI 用
- 同一記事を連続2回 `agent regenerate` した際、2回目は意味のある差分（タイムスタンプ等を除く本文差分）が出ない（冪等性）
- エラー時は記事を更新せず、エラーログを残し、終了コード非ゼロを返す（0/1/2/3/4 の使い分け）

### 9. 実装言語・パッケージマネージャ等の確定

- 言語（TypeScript / Python のいずれか）を Phase 1 着手の最初で確定し、ADR として `docs/core/decisions.md` に追記する
- パッケージマネージャ、テストフレームワーク、リンタ・フォーマッタ、最小 CI ワークフローを併せて確定する

## 受け入れ条件

### Vault ディレクトリ構造（機能1）

- [ ] `vault/sources/official/{cli,hooks,slash-commands,mcp,settings,sdk}/`, `vault/sources/community/{tips,workflows,integrations,troubleshooting}/`, `vault/concepts/`, `vault/entities/`, `vault/comparisons/`, `vault/syntheses/`, `vault/30_drafts/`, `vault/90_meta/` の全ディレクトリが Git 上に存在する（空ディレクトリは `.gitkeep` 配置）
- [ ] `vault/index.md`, `vault/log.md`, `vault/overview.md` の雛形が存在する
- [ ] プロジェクトルートを Obsidian Vault として開いた際にエラーが出ない
- [ ] `.obsidian/workspace.json` 等の個別設定が `.gitignore` に追加されている

### frontmatter 規約（機能2）

- [ ] `vault/90_meta/frontmatter-spec.md` に共通必須キー、`type` 別追加必須キー、運用メタの一覧・型・サンプル・`status` 遷移規則が記載されている
- [ ] `vault/90_meta/_schemas/frontmatter.schema.json` に `type` 別 JSON Schema が配置されている
- [ ] frontmatter 検証スクリプトが、共通必須キー欠損時にエラー終了コード（非ゼロ）を返す
- [ ] frontmatter 検証スクリプトが、`type=source` の追加必須キー（`source_url`, `fetched_at`, `claude_code_version`）欠損時にエラー終了コードを返す
- [ ] frontmatter 検証スクリプトが、`status` または `type` が enum 外の値の場合にエラー終了コードを返す
- [ ] Phase 1 で生成した10本の記事が全て検証スクリプトで PASS する

### Markdown 制約（機能3）

- [ ] `vault/90_meta/markdown-rules.md` に許可記法・禁止記法・`source` 種別の3部構成強制ルールが記載されている
- [ ] Markdown 制約検証スクリプトが、Dataview ブロック（` ```dataview `）を含むファイルでエラー終了コードを返す
- [ ] Markdown 制約検証スクリプトが、Callout 記法（`> [!note]`）を含むファイルでエラー終了コードを返す
- [ ] `three_part_validator` が、`type=source` で3部構成セクションが欠けている記事でエラー終了コードを返す
- [ ] `three_part_validator` が、`type=source` 以外の記事には3部構成を要求しないことを確認

### 情報源ホワイトリスト（機能4）

- [ ] `vault/90_meta/sources.md` に最低1ソース（`anthropic-claude-docs`）が登録されている
- [ ] 各ソースに `id`, `name`, `base_url`, `fetch_method`, `rate_limit`, `license_notes`, `enabled` の全フィールドが記載されている
- [ ] `vault/90_meta/license-notes.md` に Anthropic Usage Policy と docs.claude.com の利用規約の要点・全文転載禁止原則が記載されている

### lint ルール（機能5）

- [ ] `vault/90_meta/lint-rules.md` に検出6項目（孤立ページ、陳腐化、矛盾、低信頼度、不足ページ、index 同期）が記載されている
- [ ] `agent/validators/lint_validator` が孤立ページ・陳腐化・低信頼度・index 同期を検出する
- [ ] `agent lint --all` 実行で全違反件数のレポートと `vault/log.md` への追記が行われる

### `source` 種別記事10本（機能6、2026-05-06 改訂）

- [x] `vault/sources/official/hooks/` 配下に4本以上の記事が存在し、全て `type: source`
- [x] `vault/sources/official/cli/` 配下に4本以上の記事が存在し、全て `type: source`
- [x] 上記2カテゴリ合計で **10本以上** の記事が存在
- [x] 全記事が「## 概要 (要約)」「## 公式ドキュメント」「## 補足解説 (日本語)」の3セクションを持つ
- [x] 全記事の「## 公式ドキュメント」セクションに `最終確認: YYYY-MM-DD` と `対象バージョン: X.Y.Z` が記載されている
- [x] 全記事に共通必須 frontmatter キー + source 種別必須キーが揃っている（検証スクリプトで PASS）
- [x] 内容が新ドキュメントと整合する記事は `status: reviewed`, `confidence ≥ 0.6`（8/10 本）
- [x] 内容乖離が検出された記事は `status: draft`, `stale: true` + drift 内容のコメント記録（2/10 本: `cli/installation.md`, `hooks/overview.md`）
- [x] 各記事の `source_url` への HTTP HEAD リクエストでステータス200が返る（`agent verify-links` で検証可能）
- [x] 各記事と公式ページ間で連続100文字以上の一致が存在しない（`agent verify-links` で検査可能）
- [ ] 全記事の `status: published` および `confidence ≥ 0.7` への昇格 — **Phase 2 へ送り**（実 LLM 再生成 + 内容精査後）

### Slash Command + Skill パッケージ（機能7、ADR-014）

- [ ] `.claude/commands/wiki-ingest.md`, `.claude/commands/wiki-regenerate.md`, `.claude/commands/wiki-lint.md` が存在し、内部で `agent <subcommand>` を呼び出す指示が記載されている
- [ ] `.claude/skills/llm-wiki-for-claude-code/SKILL.md` が存在し、`name`, `description`, `triggers` を含み、Wiki ページ編集時に context-aware にロードされる旨が `description` に明記されている
- [ ] `.claude/skills/llm-wiki-for-claude-code/` 配下に `commands/` サブディレクトリが**存在しない**ことを確認（ADR-014: 公式仕様外）
- [ ] `.claude/skills/llm-wiki-for-claude-code/references/` 配下が `vault/90_meta/` のシンボリックリンクで正しく解決される
- [ ] `references/page-templates.md` に `source` 種別の実体テンプレートが含まれる
- [ ] `.claude/skills/llm-wiki-for-claude-code/hooks/session-start.md` でセッション起動時に `vault/index.md` と `vault/log.md` 直近10件がロードされることを確認
- [ ] Claude Code から `/wiki-ingest <official-url>` 実行で `vault/sources/official/<cat>/` 配下に記事が生成される
- [ ] Claude Code から `/wiki-regenerate <path>` 実行で記事の再生成が完了する
- [ ] Claude Code から `/wiki-lint` 実行で違反件数レポートが出力される

### ローカル CLI（機能8）

- [ ] `agent/runners/local.{ts|py}` が存在し、引数解析・サブコマンド分岐が実装されている
- [ ] `agent ingest --source-url <url> --category <hooks|cli>` で新ソースから `source` 種別ページが生成される
- [ ] `agent regenerate --target vault/sources/official/hooks/[ファイル名].md` で対象記事の再生成が完了する
- [ ] 同一記事を連続2回 `agent regenerate --target [同一path]` 実行し、2回目で意味のある差分（本文・要約・補足）が `git diff` 上に出ないこと（タイムスタンプ等の機械的更新は許容）
- [ ] `agent validate --all` で全記事の frontmatter / Markdown 制約検証が30秒以内に完了する
- [ ] `agent lint --all` で違反件数レポートを出力し、違反ありなら終了コード4を返す
- [ ] HTTP 取得失敗時は対象記事を更新せずエラーログを残し、終了コード非ゼロ（2）を返す
- [ ] 終了コード使い分け（0=成功, 1=検証, 2=取得, 3=LLM, 4=lint）が動作する

### 実装言語・ツール選定（機能9）

- [ ] `docs/core/decisions.md` に ADR-010（実装言語選定）が追加されている
- [ ] パッケージマネージャ、テストフレームワーク、リンタ・フォーマッタが確定し ADR に記載されている
- [ ] 選定結果に従って `package.json` または `pyproject.toml` がリポジトリに存在する
- [ ] `npm test`（または `uv run pytest`）が PASS する（最低限のスモークテスト）

### CI（最小セット）

- [ ] `.github/workflows/validate.yml` が存在する
- [ ] PR / push で `agent validate --all` 相当のチェックが走り、規約違反時に CI が fail する
- [ ] ユニットテストが CI で実行され、失敗時に fail する
- [ ] `agent lint --all` は CI 内では実行しない（人間レビュー支援用のため）

## 成功指標（2026-05-06 改訂）

- 規約準拠 `source` 種別記事数: **10本以上**（`vault/sources/official/{hooks,cli}` 配下）
- 内容が新ドキュメントと整合する記事は `status: reviewed`, `confidence ≥ 0.6`
- 内容乖離が検出された記事は `status: draft`, `stale: true` + drift コメント明記（Phase 2 で書き直し）
- `published` 化と `confidence ≥ 0.7` は Phase 2 完了条件（実 LLM 再生成 + 個別仕様精査後）
- `agent regenerate` の冪等動作: 連続2回実行で意味のある差分0件
- 検証スクリプトの実行時間: 全記事で30秒以内
- frontmatter / Markdown 制約違反検出: わざと壊した記事に対して100%検出
- 上流ドキュメントの URL/内容 drift を `agent verify-links` で検出可能
- スラッシュコマンド `/wiki-ingest`, `/wiki-regenerate`, `/wiki-lint`（`.claude/commands/` 配下）が Claude Code から起動可能
- Phase 1 の関係する PRD 機能の受け入れ条件をすべて満たす

## スコープ外

以下はこのフェーズでは実装しません:

- **AUTO セクションマーカー**（`<!-- AUTO:START --> ... <!-- AUTO:END -->`）の仕様確定と既存記事への適用 → Phase 2
- **派生ページ種別の実装**（`concept`, `entity`, `synthesis`）→ Phase 2
- **`/wiki-query` コマンド** → Phase 2
- **公式 全6カテゴリ展開**（slash-commands, mcp, settings, sdk）への記事作成 → Phase 2
- **`vault/sources/community/` 配下の記事作成** → Phase 3
- **人手レビュー工数の実測**（`metrics.md`）→ Phase 2
- **`comparison` 自動生成** → Phase 3
- **GitHub Actions 週次 cron** および `agent/runners/action.{ts|py}` の実装 → Phase 3
- **コミュニティソース取り込み**（Anthropic ブログ RSS, GitHub Releases 等）→ Phase 3
- **CODEOWNERS / PR テンプレート整備** → Phase 3
- **API コスト・運用ログ**（`cost-log.md`）→ Phase 3
- **セマンティック検索層**（qmd / MCP server）→ Phase 3 以降（200ページ超で検討）
- **Web 公開**（GitHub Pages, MkDocs, Astro Starlight 等）→ Phase 3 安定後
- **多言語対応**（日本語のみ）→ 永続的にスコープ外
- **LLM 投入用 RAG / ベクトル DB の構築** → 将来検討

## 参照ドキュメント

- `docs/ideas/20260505-llm-wiki-for-claude-code.md` - 元アイデアファイル（本計画の起点）
- `docs/core/product-requirements.md` - PRD（機能1〜6 が本計画の対象）
- `docs/core/architecture.md` - アーキテクチャ設計書（環境非依存ロジック + 薄いランナー方針）
- `docs/core/functional-design.md` - 機能設計書（Article エンティティ・ユースケース1）
- `docs/core/repository-structure.md` - リポジトリ構造定義書
- `docs/core/development-guidelines.md` - 開発ガイドライン
- `docs/core/decisions.md` - ADR（特に ADR-001〜008 が前提）
