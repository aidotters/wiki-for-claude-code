> **ステータス: 計画段階**
> このドキュメントは `docs/ideas/20260505-llm-wiki-for-claude-code.md` から生成されました。
> 実装後は `/update-docs` で実態に同期してください。

# 技術仕様書 (Architecture Design Document)

## 本ドキュメントの責務

本ドキュメントは横断的な技術決定を扱う。具体的には:

- テクノロジースタック（言語・ランタイム・フレームワーク・ツール）
- アーキテクチャパターン（レイヤー構造・各層の責務・依存ルール）
- データ永続化戦略・同期戦略
- 非機能要件（パフォーマンス・セキュリティ・スケーラビリティ）
- テスト戦略（種別・カバレッジ目標・モック方針）
- 技術的制約・依存関係管理

ユースケース単位の詳細（データモデル定義・コンポーネントのインターフェース・シーケンス図・アルゴリズム）は [`functional-design.md`](./functional-design.md) を参照。
設計判断の経緯（なぜこの選択か）は [`decisions.md`](./decisions.md) を参照。

## テクノロジースタック

> 実装言語の最終確定は Phase 1 着手時に行う（CLAUDE.md 記載通り）。
> アイデアファイル中で `agent/runners/local.ts` `action.ts` と例示されているため、TypeScript を第一候補として記載。Python になる可能性もある（要確認）。

### 言語・ランタイム

| 技術 | バージョン |
|------|-----------|
| TypeScript（要確認） | 5.x |
| Node.js（要確認） | 20+ LTS |
| 代替: Python | 3.12+ |

### フレームワーク・ライブラリ

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|---------|
| Claude Agent SDK | 最新 | LLM 呼び出し・エージェント実装 | クラウド実行と長期運用を前提とした公式 SDK |
| octokit（@octokit/rest） | 最新 | GitHub API クライアント | リポジトリ・PR 操作の公式 SDK |
| RSS パーサ（要確認） | - | RSS フィード取得 | TypeScript なら `rss-parser`、Python なら `feedparser` |
| YAML パーサ | - | frontmatter 読み書き | TypeScript なら `yaml` / `gray-matter` |
| Markdown パーサ | - | AUTO マーカー領域抽出 | `remark` / `unified` 系（要確認） |

### 開発ツール

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|---------|
| ESLint / Ruff（言語次第） | 最新 | リンタ | 標準的な静的解析 |
| Prettier / Ruff format | 最新 | フォーマッタ | 一貫したコードスタイル |
| Vitest / pytest | 最新 | テストランナー | エコシステム標準 |
| tsx / uv（言語次第） | 最新 | 開発時ランナー | TypeScript なら `tsx`、Python なら `uv run` |
| Obsidian | 最新 | Wiki 閲覧・編集 UI | Wikilinks・グラフ・全文検索 |

### ランタイム環境

| 環境 | 用途 |
|------|------|
| Claude Code（ローカル） | 開発フェーズ・手動運用 |
| GitHub Actions（ubuntu-latest） | Phase 3 の週次 cron 実行基盤 |

## アーキテクチャパターン

### Slash Command + Skill + 環境非依存ロジック + 薄いランナー（4要素）

エージェントの中核ロジックは環境（Claude Code Slash Command / Skill / ローカル CLI / GitHub Actions）に依存せず、薄いランナーから呼び出される構造とする。Slash Command 層は明示起動の操作エントリ、Skill 層は規約・テンプレートを context-aware に提供する自動参照領域として機能し、両者から環境非依存ロジック層を起動する。

```
┌──────────────────────────────────────────┐
│  Slash Command 層 (明示起動の操作)           │
│  .claude/commands/wiki-{ingest,regenerate, │
│  lint,query}.md                            │
└────────────────────┬─────────────────────┘
                     │ 自然言語指示
                     │
┌────────────────────┴─────────────────────┐
│  Skill 層 (規約・テンプレート・hook)         │
│  .claude/skills/llm-wiki-for-claude-code/  │
│  ・SKILL.md  ・references/                  │
│  ・hooks/session-start.md                  │
│  （Skill 内に commands/ は置かない）         │
└────────────────────┬─────────────────────┘
                     │ 自動コンテキストロード
┌────────────────────▼─────────────────────┐
│  Runners (環境固有のエントリポイント)        │
│  ・runners/local      Skill から呼ばれるラッパ │
│  ・runners/action     GitHub Actions (Phase 3)│
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│  Orchestration (ユースケース層)             │
│  ・ingest_source                           │
│  ・regenerate_source                       │
│  ・lint_all                                │
│  ・query (Phase 2)                         │
└────────────────────┬─────────────────────┘
                     │
        ┌────────────┼────────────┬───────────┐
        ▼            ▼            ▼           ▼
┌──────────────┐ ┌──────────┐ ┌────────────┐ ┌───────────────┐
│  fetchers    │ │ prompts  │ │  writers   │ │  validators   │
│  情報取得層   │ │ LLM 指示 │ │ Markdown 生成│ │ type 別検証   │
└──────┬───────┘ └────┬─────┘ └──────┬─────┘ └───────┬───────┘
       │              │              │                │
       ▼              ▼              ▼                ▼
┌────────────┐  ┌──────────┐  ┌─────────────┐  ┌─────────────┐
│ 情報源       │  │ Claude   │  │  vault/     │  │ vault/90_meta│
│ (RSS/API/   │  │ Agent SDK│  │ Obsidian    │  │  / _schemas  │
│  scrape)    │  │          │  │  Vault      │  │              │
└────────────┘  └──────────┘  └─────────────┘  └─────────────┘
```

#### Slash Command 層
- **責務**: 明示起動の Wiki 操作（`/wiki-*`）の提供、引数受け取り、`runners/local` の起動指示
- **許可される操作**: `runners/local` への引数渡し（自然言語指示）、Skill `references/` 経由の規約参照
- **禁止される操作**: Markdown ファイルへの直接書き込み（Writer 経由で行う）

#### Skill 層
- **責務**: Wiki ページ編集中の規約・テンプレートの context-aware 提供、起動時 hook（`session-start.md` で `index.md` / `log.md` ロード）
- **許可される操作**: `references/` 経由で `vault/90_meta/` 規約を参照、`hooks/` 経由でセッション初期化
- **禁止される操作**: Markdown ファイルへの直接書き込み（Writer 経由で行う）、Skill 内に `commands/` サブディレクトリを置くこと（公式仕様外）

#### Runners 層
- **責務**: 環境固有の引数解釈・出力フォーマット・終了コード制御
- **許可される操作**: Orchestration 層の関数呼び出し
- **禁止される操作**: Fetcher / Writer / Prompts / Validators への直接アクセス（ロジック共通化のため）

#### Orchestration 層
- **責務**: 「新ソースを取込む」「既存 source を再生成する」「lint 検査する」などのユースケースを実装
- **許可される操作**: fetchers / writers / prompts / validators の呼び出し、LLM 呼び出し
- **禁止される操作**: HTTP・ファイル I/O の直接実行（各層に委譲）

#### Fetchers 層
- **責務**: 情報源からの取得、レート制限遵守、ホワイトリスト検証
- **許可される操作**: HTTP / RSS / GitHub API
- **禁止される操作**: Markdown 生成、ファイル書き込み

#### Writers 層
- **責務**: Markdown 出力、frontmatter 更新、AUTO 領域処理、差分判定、ナビゲーション3点（index/log/overview）の更新
- **許可される操作**: ファイルシステム書き込み、Markdown パース
- **禁止される操作**: HTTP 取得、LLM 呼び出し

#### Prompts 層
- **責務**: LLM プロンプトテンプレートの管理・展開
- **許可される操作**: テンプレート変数の埋め込み
- **禁止される操作**: I/O 全般

#### Validators 層
- **責務**: frontmatter / Markdown 制約 / 3部構成 / 連続100文字一致 / 引用 / lint ルールの検証。`type` 別に適用ルールを切り替える
- **許可される操作**: ファイル読み込み、`vault/90_meta/_schemas/frontmatter.schema.json` 参照、HTTP HEAD（link_validator のみ）
- **禁止される操作**: ファイル書き込み、LLM 呼び出し

## データ永続化戦略

### ストレージ方式

| データ種別 | ストレージ | フォーマット | 理由 |
|-----------|----------|-------------|------|
| Wiki 記事本体 | Git リポジトリ + ローカルファイル | Markdown + YAML frontmatter | portability、人間も LLM も読める |
| 情報源ホワイトリスト | `vault/90_meta/sources.md` | Markdown（YAML ブロック） | 編集・レビュー対象として PR で管理 |
| API コスト実測 | `vault/90_meta/cost-log.md` | Markdown 表 | Phase 3 の運用ログ |
| エージェントログ | GitHub Actions 標準ログ | テキスト | クラウド実行時。ローカル時は標準出力 |
| 認証情報（API キー） | GitHub Secrets / 環境変数 | - | コードベースに含めない |

### バックアップ戦略

- **頻度**: Git のコミット単位（PR ごと）。Wiki 本体は GitHub に push されることがバックアップを兼ねる
- **世代管理**: Git 履歴で永続的に保持
- **復元方法**: `git revert` / `git checkout`

### 同期戦略（Vault = Repo）

- Obsidian Vault と Git リポジトリを同一ディレクトリに統合し、別経路の同期を不要にする
- `.obsidian/` のうち、ユーザー個別設定（workspace, themes など）は `.gitignore` で除外
- 共通プラグイン設定（許可記法など）のみ Git 管理

## パフォーマンス要件

### レスポンスタイム

| 操作 | 目標時間 | 測定環境 |
|------|---------|---------|
| ローカル CLI で1記事再生成 | 60秒以内 | Apple Silicon Mac, 16GB RAM 想定 |
| GitHub Actions 週次更新ジョブ全体 | 30分以内 | ubuntu-latest 標準ランナー |
| frontmatter 検証 CI | 30秒以内 | 全記事を対象 |
| 単記事のフェッチ（差分検知のみ） | 5秒以内 | レート制限内 |

### リソース使用量

| リソース | 上限 | 理由 |
|---------|------|------|
| メモリ（ジョブあたり） | 1GB | GitHub Actions 標準ランナー範囲内 |
| 月額 API コスト | Phase 3 で実測値ベースに設定 | `cost-log.md` 参照 |
| API コール数（週次） | 差分検知で最小化 | レート制限・コスト両面 |

## セキュリティアーキテクチャ

### データ保護

- **暗号化**: 記事本体は機密情報を含まない前提のため、特殊な暗号化はしない
- **アクセス制御**: GitHub リポジトリの権限設定で制御（main ブランチへの直 push は禁止）
- **機密情報管理**: API キーは GitHub Secrets / `.env`（`.gitignore` 済み）

### 入力検証

- **ホワイトリスト**: 情報源 URL は `vault/90_meta/sources.md` 記載のドメインに限る
- **frontmatter スキーマ検証**: 必須キー・型チェック
- **生成コンテンツの全文転載検出**: 公式コンテンツとの長文一致を CI で検出（Phase 2 以降の検討項目）

### CI/CD セキュリティ

- 自動 PR の自動マージは禁止。CODEOWNERS による人間レビュー必須
- GitHub Actions の権限は最小化（`contents: write`, `pull-requests: write` のみ）

## スケーラビリティ設計

### データ増加への対応

- **想定データ量**: Phase 3 終了時で記事数100〜500本想定
- **パフォーマンス劣化対策**: 差分検知で更新対象を絞り込み、全件再生成を回避
- **アーカイブ戦略**: 廃止記事は `vault/90_meta/archived.md` に記録するのみで、ファイルは保持（履歴参照のため）

### 機能拡張性

- **情報源の追加**: `vault/90_meta/sources.md` に追記し、対応する `fetchers/` 実装を追加するだけで完結
- **新ドメインカテゴリの追加**: `vault/sources/{official,community}/` 配下にディレクトリを追加
- **新ページ種別の追加**: 原則 5種別固定。新種別が必要なら ADR を立てて意思決定
- **環境追加**: `runners/` に新エントリポイント（例: Anthropic Routines / Schedule）を追加

## テスト戦略

### ユニットテスト
- **対象**: Fetcher / Writer / Prompt の各モジュール
- **カバレッジ目標**: 80%（要確認、Phase 1 着手時に確定）
- **モック化対象**: HTTP / GitHub API / LLM

### 統合テスト
- **方法**: Fetcher → Writer の連携（LLM はスタブ化）
- **対象**: 冪等性、AUTO 領域分離、frontmatter 整合性

### E2E テスト
- **ツール**: 言語確定後に決定
- **シナリオ**:
  - ローカル CLI で1記事再生成 → 想定差分一致
  - GitHub Actions ドライラン（Phase 3）

### CI チェック
- frontmatter 規約準拠
- Markdown 制約準拠（Dataview 等の禁止記法検出）
- AUTO マーカーの整合性（Phase 2 以降）

## 技術的制約

### 環境要件
- **OS**: macOS / Linux（Windows は要確認）
- **必要な外部依存**: Git, Node.js または Python（言語確定次第）, Obsidian（オプショナル）

### パフォーマンス制約
- 即時性は不要（週次更新が前提）
- LLM への単一リクエスト最大コンテキストは Claude Agent SDK の制約に従う

### セキュリティ・利用規約制約
- Anthropic Usage Policy 準拠（要約 + リンク + 補足構造の強制）
- docs.claude.com の利用規約準拠（全文転載禁止）
- 取得元のレート制限・robots.txt 遵守

## 依存関係管理

| ライブラリ | 用途 | バージョン管理方針 |
|-----------|------|------------------|
| Claude Agent SDK | LLM 呼び出し | メジャーバージョン固定、マイナーは追従 |
| octokit | GitHub API | メジャーバージョン固定 |
| RSS パーサ | RSS 取得 | メジャーバージョン固定 |
| Markdown パーサ | AUTO 領域処理 | メジャーバージョン固定 |
| YAML パーサ | frontmatter 処理 | メジャーバージョン固定 |

> 具体的なライブラリ選定は Phase 1 着手時に確定（要確認）。
