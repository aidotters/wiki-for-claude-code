> **ステータス: 計画段階**
> このドキュメントは `docs/ideas/20260505-llm-wiki-for-claude-code.md` から生成されました。
> 実装後は `/update-docs` で実態に同期してください。

# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造（Phase 3 完成形の想定）

```
wiki-for-claude-code/
├── vault/                                    # Obsidian Vault = Wiki コンテンツ本体（ページ種別ベース）
│   ├── index.md                              # ナビゲーションの本体
│   ├── log.md                                # 全操作の追記専用ログ
│   ├── overview.md                           # Wiki 全体の高レベル俯瞰
│   ├── sources/                              # type=source: 取込み元の要約 + 公式リンク + 補足
│   │   ├── official/                         # 公式ドキュメント由来
│   │   │   ├── cli/
│   │   │   ├── hooks/
│   │   │   ├── slash-commands/               # Phase 2 から
│   │   │   ├── mcp/                          # Phase 2 から
│   │   │   ├── settings/                     # Phase 2 から
│   │   │   └── sdk/                          # Phase 2 から
│   │   └── community/                        # Phase 3 から
│   │       ├── tips/
│   │       ├── workflows/
│   │       ├── integrations/
│   │       └── troubleshooting/
│   ├── concepts/                             # type=concept: 複数 source 横断の概念（Phase 2 から）
│   ├── entities/                             # type=entity: ツール・コマンド・人物（Phase 2 から）
│   ├── comparisons/                          # type=comparison: 競合アプローチ比較（Phase 3 で自動生成）
│   ├── syntheses/                            # type=synthesis: クエリ結果の保存（Phase 2 から）
│   ├── 30_drafts/                            # LLM 下書き（レビュー待ち）
│   └── 90_meta/                              # 規約・ホワイトリスト・運用ログ
│       ├── frontmatter-spec.md
│       ├── markdown-rules.md
│       ├── sources.md
│       ├── license-notes.md
│       ├── lint-rules.md
│       ├── _schemas/
│       │   └── frontmatter.schema.json       # type 別 JSON Schema
│       ├── auto-marker-spec.md               # Phase 2 で追加
│       ├── metrics.md                        # Phase 2 で追加
│       └── cost-log.md                       # Phase 3 で追加
├── .claude/                                  # Claude Code 設定
│   ├── commands/                             # スラッシュコマンド本体（明示起動の Wiki 操作）
│   │   ├── wiki-ingest.md
│   │   ├── wiki-regenerate.md
│   │   ├── wiki-lint.md
│   │   └── wiki-query.md                     # Phase 2 で追加
│   ├── agents/
│   └── skills/
│       └── llm-wiki-for-claude-code/         # 規約・テンプレート・hook の Skill パッケージ
│           ├── SKILL.md                       # Skill エントリ（コンテキスト自動ロード）
│           ├── references/                    # vault/90_meta/ へのシンボリックリンク群
│           └── hooks/
│               └── session-start.md           # 起動時に index.md / log.md ロード
├── agent/                                    # 環境非依存ロジック層
│   ├── fetchers/                             # 情報取得層
│   ├── writers/                              # Markdown 生成・更新（nav files 含む）
│   ├── prompts/                              # LLM 指示テンプレート
│   ├── orchestration/                        # ユースケース実装（ingest/regenerate/lint/query）
│   ├── validators/                           # 規約検証（type 別）
│   └── runners/                              # 実行エントリポイント
│       ├── local.{ts,py}                     # Skill から呼ばれるラッパ
│       └── action.{ts,py}                    # GitHub Actions（Phase 3）
├── tests/                                    # テストコード
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                                     # プロジェクトドキュメント（Wiki ではない）
│   ├── core/                                 # 設計ドキュメント（本ファイル含む）
│   ├── ideas/                                # ブレインストーミング成果物
│   └── plan/                                 # 計画ドキュメント
├── scripts/                                  # 補助スクリプト
├── .github/                                  # GitHub 連携（Phase 3 で本格化）
│   ├── workflows/
│   │   ├── validate.yml                      # Phase 1 から: PR/push で検証
│   │   └── weekly-update.yml                 # Phase 3
│   ├── CODEOWNERS                            # Phase 3
│   └── pull_request_template.md              # Phase 3
├── .obsidian/                                # Obsidian 設定（一部のみ Git 管理）
├── .steering/                                # 作業計画・タスク管理（一時ファイル、Git 管理外）
├── .gitignore
├── .env.example
├── README.md
├── CLAUDE.md                                 # プロジェクト全体ガイド
└── [package.json or pyproject.toml]          # 言語確定後
```

> **構造方針について**: ディレクトリ分類の主軸は **ページ種別**（source / concept / entity / comparison / synthesis）。Claude Code のドメインカテゴリ（cli, hooks, slash-commands 等）は `sources/{official,community}/<category>/` のサブディレクトリと frontmatter `tags` で表現する。詳細は [`decisions.md` ADR-011](./decisions.md) を参照。Skill パッケージング方針は [`decisions.md` ADR-012](./decisions.md)、Slash Command と Skill の分離方針は [`decisions.md` ADR-014](./decisions.md) を参照。

## ディレクトリ詳細

### vault/ (Wiki コンテンツ本体 / Obsidian Vault)

#### vault/index.md, vault/log.md, vault/overview.md（ナビゲーション3点）

**役割**: Wiki 全体のナビゲーションと運用記録

| ファイル | 役割 | 更新タイミング |
|---------|------|--------------|
| `index.md` | 全ページのカタログ（リンク + 1行要約 + type + confidence + sources 数） | 全 ingest / regenerate / lint 操作後 |
| `log.md` | 全操作の追記専用ログ（`## [YYYY-MM-DD] operation \| description`） | 全操作後（追記のみ、過去エントリ書き換え禁止） |
| `overview.md` | Wiki 全体の高レベル俯瞰（現状・主要トピック・未解決の質問） | 5回 ingest ごと、または明示要求時 |

**依存関係**:
- 依存可能: 全ページへの wikilink
- 依存禁止: なし

#### vault/sources/

**役割**: `type: source` のページ。取込み元の一次情報（公式ドキュメント / コミュニティ記事）を「要約 + 公式リンク + 補足」3部構成で整理する

**配置**:
- `vault/sources/official/<category>/<slug>.md`: 公式ドキュメント由来
- `vault/sources/community/<category>/<slug>.md`: コミュニティ知見由来（Phase 3 から）

**サブカテゴリ**:
- `official/`: `cli/`, `hooks/`, `slash-commands/`, `mcp/`, `settings/`, `sdk/`
- `community/`: `tips/`, `workflows/`, `integrations/`, `troubleshooting/`

**命名規則**:
- 機能名・コマンド名をベースに、小文字 + ハイフン（例: `pre-tool-use.md`）
- 拡張子は `.md`

**必須要素**:
- YAML frontmatter: 共通必須（`title`, `type: source`, `confidence`, `sources`, `last_updated`, `stale`, `tags`）+ source 種別必須（`source_url`, `fetched_at`, `source_version`, `claude_code_version`）+ 運用メタ
- 「## 概要 (要約)」「## 公式ドキュメント」「## 補足解説 (日本語)」の3セクション

#### vault/concepts/, vault/entities/, vault/comparisons/, vault/syntheses/

**役割**: 派生ページ種別（Phase 2 / 3 で実装）

| ディレクトリ | type | 役割 | 導入 Phase |
|------------|------|------|----------|
| `concepts/` | concept | 複数 source 横断の概念（例: 「AUTO マーカー」「permission mode」） | 2 |
| `entities/` | entity | ツール・コマンド・人物（例: 「Bash tool」「Skills」「MCP server」） | 2 |
| `comparisons/` | comparison | 競合アプローチ比較（例: 「hooks vs Skills」） | 3（自動生成） |
| `syntheses/` | synthesis | `/wiki-query` の結果保存 | 2 |

**命名規則**: 派生ページは `<Name>.md`（PascalCase 推奨）。`comparisons/` は `<A>-vs-<B>.md`

**必須要素**:
- 共通必須 frontmatter（`title`, `type`, `confidence`, `sources`, `last_updated`, `stale`, `tags`）
- `sources` には引用元 wikilink を1つ以上必須
- `source` 種別と異なり3部構成は不要（自由構成）

**依存関係**:
- 依存可能: 同カテゴリ内・他カテゴリの記事への Wikilinks
- 依存禁止: `vault/30_drafts/` への参照（公開記事から下書きへの参照は不可）

**例**:
```
vault/sources/official/hooks/
├── overview.md
├── pre-tool-use.md
├── post-tool-use.md
└── stop.md

vault/concepts/
├── AUTO-marker.md
└── permission-mode.md

vault/entities/
├── Bash-tool.md
└── Skills.md
```

#### vault/sources/community/（Phase 3 から）

**役割**: 英語コミュニティ知見の日本語化（`type: source` のサブセット）

**配置ファイル**:
- `tips/`: 個別 Tips
- `workflows/`: ワークフロー事例
- `integrations/`: 他ツール連携
- `troubleshooting/`: トラブルシュート

**命名規則**: 公式と同じ（小文字 + ハイフン）

**必須要素**: 公式 source と同じ frontmatter + 3部構成（出典 URL は元の英語記事）

#### vault/30_drafts/

**役割**: LLM 下書きの一時保管（レビュー待ち）

**配置ファイル**: `status: draft` の記事

**命名規則**: 最終配置先と同じファイル名

**依存関係**:
- 公開記事から下書きへのリンクは禁止
- レビュー後に該当する公開ディレクトリへ移動

#### vault/90_meta/

**役割**: Wiki 運用に関するメタ情報

**配置ファイル**:

| ファイル | 役割 |
|---------|------|
| `sources.md` | 情報源ホワイトリスト |
| `frontmatter-spec.md` | frontmatter 規約 |
| `markdown-rules.md` | Markdown 制約（許可・禁止記法） |
| `license-notes.md` | Anthropic Usage Policy / docs 利用規約整理 |
| `auto-marker-spec.md` | AUTO マーカー仕様（Phase 2） |
| `metrics.md` | レビュー工数実測（Phase 2） |
| `cost-log.md` | API コスト実測（Phase 3） |
| `archived.md` | 廃止記事リスト |

### agent/ (エージェントロジック / 環境非依存)

#### agent/fetchers/

**役割**: 情報源からの取得（HTTP / RSS / GitHub API）

**配置ファイル**:
- ソース種別ごとの実装（例: `rss-fetcher.{ts,py}`, `github-fetcher.{ts,py}`）
- 共通インターフェース定義

**命名規則**: 小文字 + ハイフン（TypeScript）または snake_case（Python）

**依存関係**:
- 依存可能: 標準 HTTP クライアント、`vault/90_meta/sources.md` 読み込みユーティリティ
- 依存禁止: `writers/`, `runners/` への依存（一方向）

#### agent/writers/

**役割**: Markdown 出力、frontmatter 管理、AUTO 領域処理

**配置ファイル**:
- `markdown-writer.*`: Markdown 生成本体
- `auto-section.*`: AUTO マーカー領域分離（Phase 2）
- `frontmatter.*`: frontmatter 読み書き

**依存関係**:
- 依存可能: ファイルシステム、Markdown パーサ
- 依存禁止: `fetchers/`, `runners/` への依存

#### agent/prompts/

**役割**: LLM プロンプトテンプレート

**配置ファイル**:
- カテゴリ別テンプレート（例: `official-summary.md`, `community-translation.md`）
- 共通指示部分（DRY のため共通化）

**命名規則**: 小文字 + ハイフン

**依存関係**:
- 依存可能: なし（純粋なテンプレート）
- 依存禁止: 他層への依存

#### agent/runners/

**役割**: 実行エントリポイント。環境固有の引数解釈・出力フォーマット

**配置ファイル**:
- `local.{ts,py}`: ローカル CLI
- `action.{ts,py}`: GitHub Actions（Phase 3）

**依存関係**:
- 依存可能: `fetchers/`, `writers/`, `prompts/`、Orchestration 層
- 依存禁止: 他のランナー間の相互依存

### tests/ (テストディレクトリ)

#### tests/unit/

**役割**: 各モジュール単体のユニットテスト

**構造**:
```
tests/unit/
└── agent/                       # agent/ と同じ構造
    ├── fetchers/
    ├── writers/
    └── prompts/
```

**命名規則**:
- TypeScript: `[対象].test.ts`
- Python: `test_[対象].py`

#### tests/integration/

**役割**: 複数モジュールの連携テスト（LLM はスタブ化）

**構造**:
```
tests/integration/
├── article-regeneration/        # 1記事再生成シナリオ
├── auto-marker/                 # AUTO 領域分離（Phase 2）
└── frontmatter-validation/
```

#### tests/e2e/

**役割**: ユーザーシナリオ全体（実 LLM 呼び出しは Phase 3 でのみ）

**構造**:
```
tests/e2e/
├── local-cli/                   # ローカル CLI のシナリオ
└── github-action/               # Phase 3
```

### docs/ (プロジェクトドキュメント)

> 注意: `docs/` は Wiki 本体（`vault/`）ではなく、本プロジェクトの設計ドキュメント置き場。

**配置ドキュメント**:
- `docs/core/`: 設計ドキュメント
  - `product-requirements.md`: PRD
  - `functional-design.md`: 機能設計書（ユースケース単位の詳細）
  - `architecture.md`: アーキテクチャ設計書（横断的決定）
  - `repository-structure.md`: 本ドキュメント
  - `development-guidelines.md`: 開発ガイドライン
  - `glossary.md`: 用語集
  - `decisions.md`: 設計判断記録（ADR）
- `docs/ideas/`: ブレインストーミング成果物
- `docs/plan/`: 計画ドキュメント

### .github/ (GitHub 連携)

**役割**: Phase 3 でメインに使用

**配置ファイル**:
- `workflows/weekly-update.yml`: 週次 cron
- `CODEOWNERS`: レビュー担当の自動割当
- `pull_request_template.md`: PR テンプレ

### .obsidian/ (Obsidian 設定)

**役割**: Obsidian Vault の設定

**Git 管理対象**:
- 共通プラグイン設定（許可記法、テーマ等の最低限）

**Git 管理対象外**:
- `workspace.json`, ユーザー個別の表示設定

### .steering/ (一時タスク管理 / Git 管理外)

**役割**: 個別タスクの作業計画・タスクリスト

**構造**:
```
.steering/
└── [YYYYMMDD]-[task-name]/
    ├── requirements.md
    ├── design.md
    └── tasklist.md
```

**命名規則**: `20260505-add-hooks-articles` 形式

### .claude/ (Claude Code 設定)

**役割**: Claude Code のスラッシュコマンド・スキル・エージェント定義

**構造**:
```
.claude/
├── commands/
├── skills/
└── agents/
```

## ファイル配置規則

### Wiki 記事ファイル

| 種別 | 配置先 | 命名規則 | 例 |
|------|--------|---------|-----|
| source（公式） | `vault/sources/official/<category>/` | 機能名-小文字 | `vault/sources/official/hooks/pre-tool-use.md` |
| source（コミュニティ） | `vault/sources/community/<category>/` | トピック名-小文字 | `vault/sources/community/tips/efficient-workflow.md` |
| concept | `vault/concepts/` | `<Name>.md`（PascalCase 推奨） | `vault/concepts/AUTO-marker.md` |
| entity | `vault/entities/` | `<Name>.md` | `vault/entities/Bash-tool.md` |
| comparison | `vault/comparisons/` | `<A>-vs-<B>.md` | `vault/comparisons/hooks-vs-Skills.md` |
| synthesis | `vault/syntheses/` | `<topic>.md`（小文字 + ハイフン） | `vault/syntheses/初心者向けセットアップガイド.md` |
| 下書き | `vault/30_drafts/` | 最終配置先と同名 | `vault/30_drafts/post-tool-use.md` |
| メタ | `vault/90_meta/` | 役割を表す名 | `vault/90_meta/sources.md` |

### エージェントソースファイル

> 言語確定前のため拡張子は仮置き。

| 種別 | 配置先 | 命名規則 | 例 |
|------|--------|---------|-----|
| Fetcher | `agent/fetchers/` | `[source-type]_fetcher.{ts,py}` | `agent/fetchers/http_fetcher.ts` |
| Writer | `agent/writers/` | `[role].{ts,py}` | `agent/writers/markdown_writer.ts` |
| Prompt | `agent/prompts/` | `[purpose].md` | `agent/prompts/source-ingest.md` |
| Validator | `agent/validators/` | `[scope]_validator.{ts,py}` | `agent/validators/frontmatter_validator.ts` |
| Orchestration | `agent/orchestration/` | `[usecase].{ts,py}` | `agent/orchestration/ingest.ts` |
| Runner | `agent/runners/` | `local.*` / `action.*` | `agent/runners/local.ts` |

### Slash Command / Skill パッケージファイル

| 種別 | 配置先 | 命名規則 | 例 |
|------|--------|---------|-----|
| スラッシュコマンド | `.claude/commands/` | `wiki-<verb>.md` | `.claude/commands/wiki-ingest.md` |
| Skill エントリ | `.claude/skills/llm-wiki-for-claude-code/` | `SKILL.md` | `.claude/skills/llm-wiki-for-claude-code/SKILL.md` |
| 参照 | `.../references/` | 内容に応じた名前（多くは `vault/90_meta/` のシンボリックリンク） | `.../references/schema.md` |
| Hook | `.../hooks/` | イベント名 | `.../hooks/session-start.md` |

> Slash Command と Skill の役割分担は [`decisions.md` ADR-014](./decisions.md) を参照。Skill 内に `commands/` サブディレクトリは置かない（公式仕様外）。

### テストファイル

| テスト種別 | 配置先 | 命名規則 | 例（TypeScript） | 例（Python） |
|-----------|--------|---------|------------------|--------------|
| ユニット | `tests/unit/` | 対象と同パス | `tests/unit/fetchers/rss-fetcher.test.ts` | `tests/unit/fetchers/test_rss_fetcher.py` |
| 統合 | `tests/integration/` | シナリオ別ディレクトリ | `tests/integration/auto-marker/scenario.test.ts` | `tests/integration/auto_marker/test_scenario.py` |
| E2E | `tests/e2e/` | 利用シナリオ別 | `tests/e2e/local-cli/regenerate.test.ts` | `tests/e2e/local_cli/test_regenerate.py` |

## 命名規則

### ディレクトリ名

- **Wiki ページ種別**: 小文字 + 複数形
  - 例: `sources/`, `concepts/`, `entities/`, `comparisons/`, `syntheses/`
- **Wiki ドメインカテゴリ**: 小文字 + ハイフン
  - 例: `slash-commands/`, `troubleshooting/`
- **運用ディレクトリ**: 数字プレフィックス + 小文字 + アンダースコア
  - 例: `30_drafts/`, `90_meta/`
- **エージェント層**: 小文字 + 単数形 / 複数形（既存慣例に従う）
  - 例: `fetchers/`, `writers/`, `prompts/`, `validators/`, `orchestration/`, `runners/`
- **Skill 層**: ハイフン区切り
  - 例: `llm-wiki-for-claude-code/`, `commands/`, `references/`, `hooks/`

### Markdown 記事ファイル名

- パターン: 小文字 + ハイフン区切り + `.md`
- 例: `pre-tool-use.md`, `efficient-workflow.md`

### ソースファイル名

> 最終決定は言語確定後。

- TypeScript: 小文字 + ハイフン（例: `rss-fetcher.ts`）
- Python: snake_case（例: `rss_fetcher.py`）

## 依存関係のルール

### 層間の依存

```
runners/  (CLI / Actions)
   ↓ (OK)
orchestration  (ユースケース)
   ↓ (OK)
fetchers / writers / prompts  (各層は同列、相互依存禁止)
   ↓ (OK)
外部リソース（HTTP / FS / LLM）
```

**禁止される依存**:
- `fetchers/` → `writers/` ❌
- `writers/` → `fetchers/` ❌
- `prompts/` → 他層全般 ❌（純粋テンプレート）
- `runners/` 同士の相互依存 ❌

### Wiki ページ間の依存

- 公開記事（`sources/`, `concepts/`, `entities/`, `comparisons/`, `syntheses/`）から `30_drafts/` へのリンク禁止
- 全 `source` 種別記事は `90_meta/sources.md` 記載のソースのみ参照可
- 派生種別（concept / entity / comparison / synthesis）は `sources` frontmatter キーで引用元 wikilink を必須とする
- `comparison` ページは比較対象の `entity` または `concept` 両方への wikilink を必須とする

## スケーリング戦略

### Wiki 記事の追加

- **既存カテゴリ・ページ種別への追加**: 既存ディレクトリに記事ファイルを追加
- **新ドメインカテゴリの追加**: `vault/sources/{official,community}/` 配下にディレクトリを追加し、`90_meta/sources.md` を更新
- **新ページ種別の追加**: 原則として5種別（source/concept/entity/comparison/synthesis）で固定。新種別が必要な場合は ADR を立てて意思決定する
- **記事の廃止**: ファイルは削除せず `status: archived` に変更し、`archived.md` に記録（履歴参照のため）

### エージェント機能の追加

- **新ソース追加**: `agent/fetchers/` に対応 Fetcher を追加し、`vault/90_meta/sources.md` を更新
- **新環境追加**: `agent/runners/` に新ランナー（例: `routines.{ts,py}`）を追加。Orchestration 層は変更不要

### ファイルサイズの管理

**Markdown 記事**:
- 1記事は読みやすさを優先（目安: 100〜300行）
- それ以上になる場合は分割し、目次記事から Wikilinks で結ぶ

**ソースファイル**:
- 1ファイル300行を超えたらリファクタリング検討
- 500行超は分割推奨

## 除外設定

### .gitignore

プロジェクトで除外するファイル:
- `.env`
- `.steering/`（タスク管理用の一時ファイル）
- `node_modules/` または `.venv/`（言語次第）
- `dist/`, `build/`
- `.obsidian/workspace.json`, `.obsidian/cache/` 等の個別設定
- `.DS_Store`
- ログファイル（`*.log`）
- テストキャッシュ（`.pytest_cache/`, `coverage/`）
