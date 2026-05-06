> **ステータス: 計画段階**
> このドキュメントは `docs/ideas/20260505-llm-wiki-for-claude-code.md` から生成されました。
> 実装言語の最終確定は Phase 1 着手時に行うため、コーディング規約のサンプルは TypeScript / Python 両方を併記しています。
> 実装後は `/update-docs` で実態に同期してください。

# 開発ガイドライン (Development Guidelines)

## 本プロジェクトの特徴

本プロジェクトは「コード」と「コンテンツ（Wiki 記事）」の2系統を扱うため、規約も2系統存在する。

| 規約 | 対象 | 主な参照先 |
|------|------|-----------|
| コーディング規約 | `agent/`, `tests/` 配下のソースコード | 本ドキュメント |
| コンテンツ規約 | `vault/` 配下の Markdown 記事 | `vault/90_meta/{frontmatter-spec,markdown-rules,license-notes}.md` |

## コーディング規約

### 命名規則

#### TypeScript の場合

```typescript
// 変数・関数: camelCase（動詞で始める関数）
const fetchedAt = new Date().toISOString();
function calculateContentHash(content: string): string { ... }

// 定数: UPPER_SNAKE_CASE
const DEFAULT_RATE_LIMIT = 10;

// Boolean: is/has/should プレフィックス
const isPublished = article.status === "published";
const hasAutoMarker = content.includes("<!-- AUTO:START -->");

// クラス・型: PascalCase
class RssFetcher { ... }
interface FetchResult { ... }
type ArticleStatus = "draft" | "reviewed" | "published";
```

#### Python の場合

```python
from typing import Literal
from dataclasses import dataclass

# 変数・関数: snake_case
fetched_at = datetime.now(timezone.utc).isoformat()
def calculate_content_hash(content: str) -> str: ...

# 定数: UPPER_SNAKE_CASE
DEFAULT_RATE_LIMIT = 10

# Boolean: is_/has_/should_ プレフィックス
is_published = article.status == "published"
has_auto_marker = "<!-- AUTO:START -->" in content

# クラス・型: PascalCase
class RssFetcher: ...

@dataclass
class FetchResult: ...

type ArticleStatus = Literal["draft", "reviewed", "published"]
```

**共通原則**:
- 変数・関数名は意味のある単語を選ぶ（`data`, `tmp`, `x` 等の汎用名は避ける）
- 略語は一般的なもの（API, URL, ID 等）以外は避ける
- ドメイン用語は `docs/core/glossary.md` に揃える

### コードフォーマット

| 項目 | 設定 |
|------|------|
| インデント | TypeScript: 2スペース / Python: 4スペース |
| 行の長さ | 100文字以内 |
| トレーリングカンマ | 複数行構造で必須（diff を最小化） |

**フォーマッタ・リンタ**:
- TypeScript: ESLint + Prettier
- Python: Ruff（lint + format）

> 具体ツール選定は Phase 1 で確定（要確認）。

### コメント規約

#### 関数・クラスのドキュメント

**TypeScript（TSDoc）**:
```typescript
/**
 * 指定された記事の AUTO 領域を最新コンテンツで再生成する。
 *
 * @param targetPath 対象記事のパス（vault/ 起点）
 * @returns 書き込み結果。意味のある差分があったかを `changed` で返す
 * @throws {SourceNotWhitelistedError} ソースがホワイトリスト外の場合
 */
async function regenerateArticle(targetPath: string): Promise<WriteResult> { ... }
```

**Python（Google Style Docstring）**:
```python
def regenerate_article(target_path: str) -> WriteResult:
    """指定された記事の AUTO 領域を最新コンテンツで再生成する。

    Args:
        target_path: 対象記事のパス（vault/ 起点）

    Returns:
        書き込み結果。意味のある差分があったかを `changed` で返す。

    Raises:
        SourceNotWhitelistedError: ソースがホワイトリスト外の場合
    """
```

#### インラインコメント

- なぜそうするかを書く。何をしているかは書かない（コードを見れば分かる）
- 利用規約・著作権上の制約に基づく実装は理由を明記
- TODO は `TODO(name): 内容 - 対応予定 Phase` の形式

```typescript
// ✅ 良い例
// 全文転載リスク回避のため、要約のみを LLM に出力させる
const prompt = buildPromptForSummaryOnly(rawContent);

// ❌ 悪い例
// プロンプトをビルドする
const prompt = buildPromptForSummaryOnly(rawContent);
```

### エラーハンドリング

**原則**:
- 予期されるエラー（取得失敗・規約違反等）は専用エラークラスを定義
- 予期しないエラーは握りつぶさず、上位に伝播
- ユーザー向けメッセージは原因と対処を明示

**エラークラス例**:

```typescript
// TypeScript
class SourceNotWhitelistedError extends Error {
  constructor(public readonly sourceId: string) {
    super(`Source "${sourceId}" is not in the whitelist`);
    this.name = "SourceNotWhitelistedError";
  }
}

class FetchFailedError extends Error {
  constructor(public readonly sourceId: string, public readonly reason: string) {
    super(`Fetch failed for "${sourceId}": ${reason}`);
    this.name = "FetchFailedError";
  }
}
```

```python
# Python
from dataclasses import dataclass

@dataclass
class SourceNotWhitelistedError(Exception):
    source_id: str

    def __str__(self) -> str:
        return f'Source "{self.source_id}" is not in the whitelist'

@dataclass
class FetchFailedError(Exception):
    source_id: str
    reason: str

    def __str__(self) -> str:
        return f'Fetch failed for "{self.source_id}": {self.reason}'
```

**ハンドリング指針**:
- Fetcher の取得失敗 → 該当記事は更新せず、ログを残し、他記事の処理は継続
- LLM 生成失敗 → PR を作成せず、Actions を fail
- frontmatter 検証エラー → CI を fail（main へのマージ阻止）

## コンテンツ規約（Wiki 記事）

> Wiki 記事の執筆・自動生成に関する詳細規約は **`vault/90_meta/` を single source of truth** とし、本ドキュメントからはリンクのみを提供する（重複防止）。

| 規約領域 | 詳細仕様の置き場所 | 概要 |
|---------|-----------------|------|
| frontmatter スキーマ | `vault/90_meta/frontmatter-spec.md` + `_schemas/frontmatter.schema.json` | 共通必須キー（`title`, `type`, `confidence`, `sources`, `last_updated`, `stale`, `tags`）+ `type` 別必須キー + 運用メタ |
| Markdown 制約 | `vault/90_meta/markdown-rules.md` | 許可記法（標準 Markdown + Wikilinks + Mermaid）と禁止記法（Obsidian Dataview / Callout 等） |
| `source` 種別3部構成 | `vault/90_meta/markdown-rules.md` | `type=source` のみ「概要 (要約)」「公式ドキュメント」「補足解説 (日本語)」の構造強制 |
| AUTO セクションマーカー | `vault/90_meta/auto-marker-spec.md`（Phase 2） | `<!-- AUTO:START --> ... <!-- AUTO:END -->` の仕様 |
| 情報源ホワイトリスト | `vault/90_meta/sources.md` | 取得許可ソースとレート制限・取得方式 |
| 利用規約・著作権整理 | `vault/90_meta/license-notes.md` | Anthropic Usage Policy / docs.claude.com 利用規約・全文転載禁止ルール |
| lint ルール | `vault/90_meta/lint-rules.md` | 孤立ページ・陳腐化・矛盾・低信頼度・不足ページ・index 同期の検出仕様 |

> 上記ファイルは Phase 1 で初版を確定する。なぜこの構造を採るかの判断経緯は [`decisions.md`](./decisions.md) の ADR-001 / ADR-003〜ADR-006 / ADR-008 / ADR-011 / ADR-012 を参照。

### コードから記事規約への接点

エージェント実装側で意識すべきポイントのみここに記す（詳細は上記リンク先）:

- **Fetcher**: ソース ID は `vault/90_meta/sources.md` のホワイトリスト記載のもののみ受け付ける
- **Writer**: 出力 Markdown は `markdown-rules.md` の許可記法に限定。AUTO 領域処理は `auto-marker-spec.md` に従う
- **Validator**: frontmatter / Markdown 制約 / AUTO マーカー整合性の CI チェックを `vault/90_meta/` の規約から導出して実装する

## Git 運用ルール

### ブランチ戦略

- `main`: 公開可能な状態。直 push 禁止、PR 経由のみ
- `feature/[作業名]`: 新機能・新カテゴリ展開
- `content/[記事名]`: 個別記事の追加・更新
- `bot/auto-update-[YYYYMMDD]`: 自動 PR 用ブランチ（Phase 3）

### コミットメッセージ規約

**フォーマット**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 機能追加
- `fix`: バグ修正
- `docs`: プロジェクトドキュメント（`docs/` 配下）
- `content`: Wiki 記事の追加・更新（`vault/` 配下）
- `chore`: ビルド・補助ツール
- `refactor`: 振る舞いを変えない変更
- `test`: テスト追加・修正

**Scope 例**:
- `agent`, `fetchers`, `writers`, `prompts`, `runners`
- `vault`, `meta`, `hooks`, `cli`（Wiki カテゴリ）
- `ci`, `actions`

**例**:
```
content(hooks): pre-tool-use の補足解説を追加

公式の説明だけでは伝わりにくい「コマンド実行前の確認パターン」の
具体例を補足セクションに追加した。

claude_code_version: 1.5.0
```

```
feat(fetchers): RSS フェッチャーを追加

Anthropic ブログ RSS の取得実装。レート制限処理と
contentHash による差分検知を含む。
```

### プルリクエストプロセス

**作成前のチェック**:
- [ ] frontmatter 検証 PASS
- [ ] Markdown 制約 PASS
- [ ] テストが PASS（コード変更時）
- [ ] リンタが PASS

**PR テンプレ**（Phase 3 で `.github/pull_request_template.md` に配置予定）:

```markdown
## 概要
[変更内容]

## 種別
- [ ] コード変更（`agent/`, `tests/`）
- [ ] Wiki 記事変更（`vault/`）
- [ ] 規約変更（`vault/90_meta/`）

## 変更ソース（Wiki 記事の場合）
- source_url: [URL]
- claude_code_version: [X.Y.Z]
- 自動生成 / 人手 / 自動 + 人手修正

## レビュー観点
- [ ] 全文転載が含まれていないか
- [ ] frontmatter が規約準拠か
- [ ] 公式リンクが到達可能か

## 関連 Issue
Closes #[Issue番号]
```

**自動 PR の取り扱い（Phase 3）**:
- bot 作成 PR は自動マージ禁止
- CODEOWNERS による人間レビュー必須
- 人手修正がある場合は追加コミットで対応

## テスト戦略

### ユニットテスト

**対象**: 各モジュール単体

**カバレッジ目標**: 80%（要確認、Phase 1 で確定）

**TypeScript（Vitest）例**:
```typescript
import { describe, it, expect, vi } from "vitest";
import { RssFetcher } from "./rss-fetcher";

describe("RssFetcher", () => {
  describe("fetch", () => {
    it("returns parsed entries on success", async () => {
      const fetcher = new RssFetcher({ httpClient: mockHttp });
      const result = await fetcher.fetch("anthropic-blog-rss");
      expect(result.entries).toHaveLength(3);
    });

    it("throws FetchFailedError on HTTP 500", async () => {
      const fetcher = new RssFetcher({ httpClient: mockHttp500 });
      await expect(fetcher.fetch("anthropic-blog-rss"))
        .rejects.toThrow(FetchFailedError);
    });
  });
});
```

**Python（pytest）例**:
```python
import pytest
from agent.fetchers.rss_fetcher import RssFetcher
from agent.errors import FetchFailedError

class TestRssFetcher:
    class TestFetch:
        async def test_returns_parsed_entries_on_success(
            self, fetcher: RssFetcher
        ) -> None:
            """成功時にパース済みエントリを返す"""
            result = await fetcher.fetch("anthropic-blog-rss")
            assert len(result.entries) == 3

        async def test_raises_fetch_failed_on_http_500(
            self, fetcher_with_500: RssFetcher
        ) -> None:
            """HTTP 500 で FetchFailedError を投げる"""
            with pytest.raises(FetchFailedError):
                await fetcher_with_500.fetch("anthropic-blog-rss")
```

### 統合テスト

**対象**: 複数モジュールの連携（LLM スタブ化）

**シナリオ**:
- 1記事の再生成（Fetcher → Writer）が冪等動作する
- AUTO 領域内のみが更新され、外側のバイト列が保持される
- frontmatter 検証エラー時に処理を中断する

### E2E テスト

**シナリオ**:
- ローカル CLI で `agent ingest --source-url <url> --category <cat>` 実行 → `source` 記事生成と nav 更新
- ローカル CLI で `agent regenerate --target [path]` 実行 → 想定差分一致（連続2回で差分0件）
- スラッシュコマンド `/wiki-ingest`, `/wiki-regenerate`, `/wiki-lint`（`.claude/commands/` 配下）の実行 → エンドツーエンド動作確認
- GitHub Actions ワークフローのドライラン（Phase 3）

### テスト命名規則

**TypeScript**:
- `describe` でモジュール → メソッド階層
- `it` は「条件 + 期待結果」の英文（例: `"returns null when not found"`）

**Python**:
- クラス階層 `TestClassName.TestMethodName`
- メソッド名は `test_[条件]_[期待結果]` または日本語 docstring

### モック・スタブの方針

| 対象 | 扱い |
|------|------|
| HTTP / GitHub API / RSS フィード | モック化（ユニット・統合） |
| ファイルシステム | 一時ディレクトリで実 I/O（統合） |
| LLM 呼び出し | スタブ化（決定的応答） |
| ビジネスロジック | 実装を使う（モックしない） |

## CI / CD

### CI チェック項目（Phase 1 で最低限、Phase 3 で本格）

| チェック | タイミング | 失敗時挙動 |
|---------|-----------|-----------|
| frontmatter 規約検証 | PR / push | 失敗で fail |
| Markdown 制約検証（禁止記法検出） | PR / push | 失敗で fail |
| AUTO マーカー整合性（Phase 2） | PR / push | 失敗で fail |
| ユニットテスト | PR / push | 失敗で fail |
| 統合テスト | PR / push | 失敗で fail |
| 公式リンク到達確認 | 週次 | 失敗で警告（警告のみ） |

### GitHub Actions ワークフロー（Phase 3）

| ワークフロー | トリガー | 役割 |
|------------|---------|------|
| `weekly-update.yml` | cron（週次）+ 手動 | エージェント実行・PR 作成 |
| `validate.yml` | PR / push | CI チェック |
| `link-check.yml` | cron（週次） | 公式リンク到達確認 |

## コードレビュー基準

### レビューポイント

**コード変更**:
- [ ] レイヤー間依存ルールを守っているか（fetchers → writers の禁止 等）
- [ ] エラーハンドリングが適切か
- [ ] テストが追加されているか
- [ ] 命名が明確か

**Wiki 記事変更**:
- [ ] 全文転載が含まれていないか
- [ ] frontmatter が規約準拠か
- [ ] 3部構成が崩れていないか
- [ ] 公式リンクが到達可能か
- [ ] `claude_code_version` が現実のバージョンと一致するか

### コメントの優先度ラベル

- `[必須]`: 修正必須（マージブロック）
- `[推奨]`: 修正推奨
- `[提案]`: 検討してほしい
- `[質問]`: 理解のための質問

## 開発環境セットアップ

> 言語確定後に詳細を確定（要確認）。以下は想定手順。

### 必要なツール

| ツール | 用途 |
|------|------|
| Git | バージョン管理 |
| Node.js 20+ または Python 3.12+ | ランタイム（言語次第） |
| Obsidian（オプショナル） | Wiki ローカル閲覧 |
| Claude Code | ローカル開発 |

### セットアップ手順（想定）

```bash
# 1. リポジトリのクローン
git clone https://github.com/[org]/wiki-for-claude-code.git
cd wiki-for-claude-code

# 2. 環境変数の設定
cp .env.example .env
# .env を編集（API キー等）

# 3. 依存関係のインストール（言語次第）
# TypeScript の場合:
npm install
# Python の場合:
uv sync

# 4. 動作確認
agent validate --all
```

### 推奨開発ツール

- **VS Code**: Wiki 記事と TypeScript/Python の両方を扱いやすい
- **Obsidian**: `vault/` を Vault として開く
- **Claude Code**: ローカルでのエージェント実行・記事作成支援

## チェックリスト（実装着手時）

Phase 1 着手時に以下を確定すること:

- [ ] 実装言語（TypeScript / Python）
- [ ] パッケージマネージャ（npm/pnpm/yarn または uv/pip）
- [ ] テストフレームワーク
- [ ] リンタ・フォーマッタ
- [ ] CI ワークフローの最小セット
- [ ] `vault/90_meta/` 各規約ファイルの初版
- [ ] 情報源ホワイトリスト（`vault/90_meta/sources.md`）の初版
