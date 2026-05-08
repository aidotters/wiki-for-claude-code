# LLM-Wiki for Claude Code

Andrej Karpathy 氏の LLM-Wiki コンセプトと Reza Rezvani 氏の Claude Code Skill 実装を下敷きに、Claude Code ドメインに特化したドメイン特化コンパイル型 Wiki プロジェクトです。

## ステータス

- **Phase 1（実装済み）**: 規約確立 + Skill 雛形 + 公式 hooks/cli の `source` 種別 10本
- **Phase 2 / 3**: 派生ページ種別、AUTO セクションマーカー、`/wiki-query`、コミュニティソース、GitHub Actions 自動化（未着手）

## セットアップ

### 前提

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) 0.6+

### インストール

```bash
uv sync
```

### 環境変数

`.env.example` をコピーして `.env` を作成し、`ANTHROPIC_API_KEY` を設定（実 LLM 統合は Phase 3 から、Phase 1 のテストはスタブで動作）。

## 使い方

### Slash Command（Claude Code 経由）

Claude Code セッション内で以下を実行:

- `/wiki-ingest <official-url>` — 公式ドキュメントの URL から `source` ページを生成
- `/wiki-regenerate <vault/sources/official/.../page.md>` — 既存ページの再生成
- `/wiki-lint` — vault 全体の lint 検査（孤立 / 陳腐化 / 低信頼度 / 不足 / index 同期）

### CLI（直接実行）

```bash
# 取込み
uv run agent ingest --source-url https://code.claude.com/docs/ja/hooks --category hooks

# 再生成（既定: claude-code バックエンド経由で AUTO 領域のみ実 LLM で更新）
uv run agent regenerate --target vault/sources/official/hooks/pre-tool-use.md

# lint 検査（人間レビュー支援、終了コード 0 / 4）
uv run agent lint --all

# 機械的検証（CI 用、終了コード 0 / 1）
uv run agent validate --all
uv run agent validate --target vault/sources/official/cli/installation.md

# source_url の HTTP 到達確認 + 連続100文字一致検査（ネットワーク依存）
uv run agent verify-links
uv run agent verify-links --target vault/sources/official/cli/permissions.md
uv run agent verify-links --no-transclusion   # HEAD のみ
```

> **`agent regenerate` の現行仕様**（ADR-018 / ADR-019, 2026-05-08 accepted）: AUTO 領域（`<!-- AUTO:START purpose=... -->` ... `<!-- AUTO:END -->`）のみを実 LLM 経由で再生成。AUTO 外の人手編集は保護される。`auto_section_managed: true` のページは `content_hash` 一致時 no-op、`--force` で強制再生成可能。バックエンドは環境変数で切替: 既定 `WIKI_LLM_BACKEND=claude-code`（`claude` バイナリ + Max プラン認証必須）/ `anthropic`（`ANTHROPIC_API_KEY` 必須・従量課金、CI 向け）/ `stub`（テスト・冪等性検証用）。

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 成功 |
| 1 | 検証エラー（frontmatter / Markdown 制約 / 3部構成違反） |
| 2 | 取得エラー / ホワイトリスト外 |
| 3 | LLM エラー |
| 4 | lint 違反（fail させない人間レビュー支援用） |

### Obsidian で開く

リポジトリルートを Obsidian Vault として開いてください（`.obsidian/app.json` の最小設定が同梱されています）。

## ディレクトリ構造

```
wiki-for-claude-code/
├── vault/                    # Wiki コンテンツ本体兼 Obsidian Vault
│   ├── index.md              # ナビゲーション
│   ├── log.md                # 全操作の追記専用ログ
│   ├── overview.md           # 全体俯瞰
│   ├── sources/official/     # 公式ドキュメント由来の source 種別ページ
│   │   ├── hooks/            # 5本（overview/pre-tool-use/post-tool-use/stop/user-prompt-submit）
│   │   └── cli/              # 5本（installation/basic-usage/configuration/keybindings/permissions）
│   └── 90_meta/              # 規約・ホワイトリスト・schema
├── .claude/
│   ├── commands/wiki-*.md    # Slash Command（明示起動）
│   └── skills/llm-wiki-for-claude-code/  # Skill（context-aware ロード）
├── agent/                    # 環境非依存ロジック
│   ├── fetchers/             # HTTP 取得 + ホワイトリスト検証
│   ├── writers/              # frontmatter / Markdown / nav files
│   ├── validators/           # 7種の検証ロジック
│   ├── prompts/              # プロンプトテンプレート
│   ├── orchestration/        # ingest / regenerate / lint / validate ユースケース
│   └── runners/local.py      # CLI エントリ（agent コマンド）
├── tests/{unit,integration,e2e}/
└── docs/core/                # アーキテクチャ・設計判断・規約参照
```

## テスト・品質チェック

```bash
# テスト実行
uv run pytest tests/

# Lint
uv run ruff check .

# 型チェック
uv run mypy agent

# Wiki コンテンツ検証
uv run agent validate --all
```

## 関連ドキュメント

- 設計: `docs/core/architecture.md`
- ADR: `docs/core/decisions.md`
- PRD: `docs/core/product-requirements.md`
- 規約: `vault/90_meta/{frontmatter-spec,markdown-rules,sources,license-notes,lint-rules}.md`

## ライセンス・著作権

- 取込み元（docs.claude.com 等）の著作権は各社・各個人に帰属。本プロジェクトは「要約 + リンク + 補足」の3部構成で、全文転載を禁止します（ADR-003 / `vault/90_meta/license-notes.md`）。
- 本リポジトリのコード・規約ドキュメントの著作権はリポジトリ著者に帰属。
