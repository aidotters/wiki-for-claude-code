# 設計書: `ClaudeCodeBackend` 追加

> **2026-05-08 補遺**: 本設計書は `ClaudeCodeBackend` 単体の並列拡張のみを記述。本実装の empirical 検証で `regenerate.py` の noop stub と `make_backend()` 配線バグが発覚し、ADR-019 として並行で AUTO 領域経路の実 LLM 化・`--force` フラグ追加・`regenerate_source` の `llm` 既定値修正を実施した。ADR-019 関連の設計詳細は `.steering/20260508-adr-019-auto-region-llm/design.md` を参照。

## アーキテクチャ概要

既存の `LLMBackend` Protocol に **3 つ目の実装** を追加する単純な並列拡張。Protocol シグネチャ・既存 2 実装（`StubLLMClient` / `AnthropicBackend`）には一切手を加えない。バックエンド選択は `make_backend()`（`agent/orchestration/llm.py:198-207`）の env var 分岐に `claude-code` 分岐を追加するだけ。

```
agent/orchestration/llm.py
├─ LLMBackend (Protocol)            ← 既存（変更なし）
│   └─ invoke(system, prompt, cache_system) -> LLMResult
│
├─ StubLLMClient                     ← 既存（変更なし）
├─ AnthropicBackend                  ← 既存（変更なし）
└─ ClaudeCodeBackend                 ← 新規追加
    └─ claude-agent-sdk 経由で invoke 実装

make_backend() ← 既存に claude-code 分岐を追加
   ├─ stub      → StubLLMClient
   ├─ anthropic → AnthropicBackend
   └─ claude-code → ClaudeCodeBackend  (新規)
```

レイヤー上は Phase 2-A の Orchestration 層内の純粋拡張で、`agent/orchestration/regenerate.py` は `make_backend()` の戻り値を使うだけなので変更不要。

## コンポーネント設計

### 1. `ClaudeCodeBackend`（新規）

**責務**:
- `claude-agent-sdk` を経由して Claude Code (Max プラン) に system / user プロンプトを送り、`LLMResult` で返却
- 起動時に `claude` バイナリの PATH 存在確認（フェイルファスト）
- SDK 例外 / 認証エラーを `LLMInvocationError` にラップ

**実装の要点**:
- `__init__(*, model=None, max_tokens=DEFAULT_MAX_TOKENS, client=None)`:
  - `client` はテスト用 DI（mock 注入用）
  - `client is None` の本番経路で `shutil.which("claude")` を呼び、不在なら `ConfigurationError("claude バイナリが PATH にありません。`claude /login` でセットアップしてください")`
  - `claude-agent-sdk` の遅延 import（`stub` バックエンド時の依存最小化方針を踏襲、`AnthropicBackend` と同じ）
- `invoke(*, system, prompt, cache_system=True) -> LLMResult`:
  - SDK のメッセージ作成 API を呼び、レスポンスを `_parse_claude_code_response` で `LLMResult` に正規化
  - `cache_system` フラグは現行 SDK が `cache_control` を意識的に扱えない場合 **noop**（caching は Claude Code 内部に委譲）
  - 例外は `LLMInvocationError` にラップ。リトライは `AnthropicBackend` と同じく **1 回**
- `generate(prompt) -> str`: 後方互換のため、`invoke(system="", prompt=prompt, cache_system=False).text` を返す

**`claude-agent-sdk` API 利用方針（Phase 2-A 案 Y で確認）**:
- 同期 API があればそれを使用、非同期 API しかない場合は `asyncio.run` で同期化（既存 `invoke` は同期シグネチャのため）
- 実 API 名は実装着手時に SDK ドキュメントで確認し、テストは mock 経由で固定

**SDK API 確認結果（実装着手時に context7 + ローカル `.venv` インストールで確認、claude-agent-sdk 0.1.77）**:
- メッセージ作成 API: `claude_agent_sdk.query(*, prompt: str, options: ClaudeAgentOptions | None = None) -> AsyncIterator[Message]`（async-only）
- `ClaudeAgentOptions` のうち本実装で使用するフィールド: `system_prompt: str | dict | None`, `model: str | None`, `max_turns: int | None`
- レスポンスは AsyncIterator で、`AssistantMessage`（`content: list[ContentBlock]`、`TextBlock.text` でテキスト）と `ResultMessage`（`usage: dict[str, Any] | None`、`is_error: bool`）が混在して yield される
- `ResultMessage.usage` は dict 形式（API 直叩きの `usage` オブジェクトとほぼ同等のキー名を期待）。`input_tokens` / `output_tokens` / `cache_creation_input_tokens` / `cache_read_input_tokens` は存在すれば抽出、無ければ 0
- 同期化方針: `invoke` は同期シグネチャなので、内部で `asyncio.run` で実行
- バイナリ未存在時の SDK 自身の例外: `CLINotFoundError`（`CLIConnectionError` の派生）。本実装では `__init__` で `shutil.which("claude")` を先に確認しフェイルファストするため、SDK 例外に到達するのは稀（保険として `invoke` 内で `LLMInvocationError` にラップ）

### 2. `make_backend()` 拡張（既存変更）

**責務**:
- `WIKI_LLM_BACKEND` 値から適切なバックエンドを返す
- 既存の `stub` / `anthropic` 分岐に `claude-code` を追加

**実装の要点**:
- 既定値は当面 `stub` 維持。empirical 検証 PASS 後の別 PR で `claude-code` に変更（段階展開）
- 不明値時の `ConfigurationError` メッセージを `stub`/`anthropic`/`claude-code` の 3 値に更新
- ハイフン入り env 値（`claude-code`）の正規化は `.lower()` のみで OK（既存と同じ）

### 3. `pyproject.toml` 拡張

**責務**:
- `claude-agent-sdk` を依存に追加

**実装の要点**:
- バージョン下限はピン留め、上限は緩めにして mypy / pytest で破壊検出（リスク表に記載済み方針）
- 仮指定: `claude-agent-sdk>=0.1.0`（実際の利用可能版を `uv add` 時に確認して合わせる）

### 4. `.env.example` 拡張

**責務**:
- 開発者に 3 値の選択肢を提示

**実装の要点**:
- 既存の `WIKI_LLM_BACKEND=stub` セクションに `claude-code` 例を追記
- `claude-code` 選択時は `ANTHROPIC_API_KEY` 不要である旨をコメントで記載

### 5. ADR-018（`docs/core/decisions.md`）

**責務**:
- 採用判断の文書化（採用案・代替案・残置判断・段階展開ポリシー）

**実装の要点**:
- ADR フォーマットは ADR-015〜017 を踏襲
- `Status: Proposed`（実装完了で `Accepted` に昇格、別 PR）

## データフロー

### `agent regenerate` 実行（`claude-code` 経路）

```
1. ユーザー: WIKI_LLM_BACKEND=claude-code uv run agent regenerate --target <path>
2. CLI runner → orchestration/regenerate.py
3. regenerate.py → make_backend() を呼ぶ
4. make_backend() → ClaudeCodeBackend() を返す（__init__ で claude バイナリ確認）
5. regenerate.py → backend.invoke(system=..., prompt=..., cache_system=True) を呼ぶ
6. ClaudeCodeBackend.invoke → claude-agent-sdk → claude CLI subprocess → Max プラン認証
7. SDK レスポンス → _parse_claude_code_response → LLMResult(text, usage)
8. regenerate.py → AUTO 領域のみ書換え、frontmatter 更新、idempotent 確認
```

### 起動時バイナリ未検出経路

```
1. WIKI_LLM_BACKEND=claude-code (claude 未インストール環境)
2. make_backend() → ClaudeCodeBackend()
3. __init__ → shutil.which("claude") → None
4. ConfigurationError 発生 → exit code 3
5. CLI runner → エラーメッセージ表示（claude /login 誘導）
```

## エラーハンドリング戦略

### 既存例外の流用（`agent/errors.py`）

| 状況 | 例外 | exit code |
|------|------|-----------|
| `claude` バイナリが PATH にない | `ConfigurationError` | 3 |
| `WIKI_LLM_BACKEND` が不明値 | `ConfigurationError` | 3 |
| `claude-agent-sdk` 内部例外（認証 / network 等） | `LLMInvocationError` | 3 |

新規例外クラスは追加しない（Phase 2-A の例外階層に乗せる）。

### リトライ戦略

- `invoke` 内で SDK 呼び出しに失敗時、**1 回リトライ**して再失敗なら `LLMInvocationError`
- `AnthropicBackend` と同一方針（コードパターンも揃える）
- リトライ間隔は 0（即時）。指数バックオフ等は Phase 2-B 検討

### `cache_read_input_tokens` 不可視時の扱い

- SDK レスポンスに `cache_read_input_tokens` フィールドがない場合、`LLMUsage.cache_read_input_tokens = 0` のまま返す
- `cache_hit_rate` は 0.0 を返すが、`metrics.md` 記録時は `N/A` で書ける（運用ルールで合意、ADR-018 に明記）

## テスト戦略

### ユニットテスト（`tests/unit/test_llm_claude_code.py` 新規）

- **正常系**: mock client を `__init__(client=mock)` で注入し、`invoke` が `LLMResult` を返すことを検証
- **モデル指定**: `WIKI_LLM_MODEL=claude-opus-4-7` 環境で `ClaudeCodeBackend().model == "claude-opus-4-7"`
- **バイナリ未存在**: `monkeypatch.setattr(shutil, "which", lambda _: None)` で `ConfigurationError` 発生を検証
- **API キー無視**: `ANTHROPIC_API_KEY` 未設定でも `__init__` が成功することを検証（ただし `client` 注入経路で）
- **SDK 例外ラップ**: mock client が例外を投げる → `LLMInvocationError` でラップされる
- **リトライ**: mock client が 1 回目失敗 / 2 回目成功 → `invoke` が成功する
- **`make_backend()` 分岐**: `WIKI_LLM_BACKEND=claude-code` で `ClaudeCodeBackend` インスタンスが返る

### 統合テスト

- ~~既存の regenerate 統合テストは `stub` バックエンドで動作するため変更不要~~（**2026-05-08 訂正**: ADR-019 で AUTO 領域経路を実 LLM 化したことに伴い、stub レスポンスを `auto_section_managed: true` + AUTO マーカー対応に更新。詳細は `.steering/20260508-adr-019-auto-region-llm/`）
- empirical 検証は手動実施（受入れ条件「empirical 検証」セクションで規定）

### CI への影響

- `pytest` / `ruff` / `mypy` / `agent validate --all` は変更なし（テスト件数のみ増加）
- 新規依存 `claude-agent-sdk` は `uv sync` でインストールされ CI で型チェック対象になる

## 依存ライブラリ

```toml
# pyproject.toml [project.dependencies]
"claude-agent-sdk>=0.1.0"  # 実際の最低互換版は uv add 時に確認
```

既存依存（変更なし）: `anthropic>=0.40`, `httpx`, `pyyaml`, `pydantic` 等。

## ディレクトリ構造

```
wiki-for-claude-code/
├── agent/
│   ├── orchestration/
│   │   └── llm.py                    # ClaudeCodeBackend クラス追加 + make_backend 分岐追加
│   └── errors.py                     # 変更なし（既存 ConfigurationError / LLMInvocationError を流用）
├── tests/
│   └── unit/
│       └── test_llm_claude_code.py   # 新規追加
├── pyproject.toml                    # claude-agent-sdk 依存追加
├── uv.lock                           # uv lock 後の更新
├── .env.example                      # WIKI_LLM_BACKEND=claude-code 例追記
├── docs/
│   └── core/
│       └── decisions.md              # ADR-018 追記
└── CLAUDE.md                         # empirical PASS 後の別 PR でガード注記削除
```

## 実装の順序

1. **依存追加** — `uv add claude-agent-sdk` → `pyproject.toml` / `uv.lock` 更新
2. **`ClaudeCodeBackend` 雛形** — `agent/orchestration/llm.py` にクラス追加、`__init__` のバイナリチェックを実装、`invoke` は最小スケルトン
3. **`claude-agent-sdk` API 確認** — SDK の実 API 名と sync/async 形態を確認し、`invoke` の本実装を書く
4. **`_parse_claude_code_response`** — レスポンス → `LLMResult` 変換ヘルパ
5. **`make_backend()` 拡張** — `claude-code` 分岐を追加、不明値メッセージ更新
6. **ユニットテスト追加** — `tests/unit/test_llm_claude_code.py`（mock client / バイナリ未存在 / 例外ラップ / リトライ / `make_backend` 分岐）
7. **`.env.example` 更新** — `WIKI_LLM_BACKEND=claude-code` 例とコメント追記
8. **品質チェック** — `uv run pytest tests/` / `uv run ruff check .` / `uv run mypy agent` を全 PASS させる
9. **ADR-018 起票** — `docs/core/decisions.md` に追記
10. **empirical 検証準備** — 検証手順を別ドキュメント or PR 説明に記載（実行は別セッション）

> **注**: 既定値切替（`make_backend` の既定 `claude-code` 化）と `CLAUDE.md` ガード注記削除と `metrics.md` 修正率記録は **empirical 検証 PASS 後の別 PR** で実施し、本タスクには含めない。

## セキュリティ考慮事項

- **認証情報の取扱い**: `~/.claude/` の認証情報は `claude` CLI が管理する。本プロジェクトは追加 env var を導入せず、認証情報をコードベースに持ち込まない
- **subprocess 経由のコマンド注入リスク**: `claude-agent-sdk` 内部の subprocess 実行は SDK 側の責務。本実装では SDK API のみを呼ぶので注入リスクは増えない
- **CI 事故防止**: CI 環境で誤って `claude-code` が選択されないよう、`.github/workflows/*.yml` 側で `WIKI_LLM_BACKEND=anthropic` または `stub` を明示する運用方針（ADR-018 に明記、本 PR では CI 設定変更なし）

## パフォーマンス考慮事項

- **subprocess 起動オーバヘッド**: `claude-agent-sdk` は内部で claude CLI を起動するためネイティブ API より遅い。記事数 ~20 本 × 週次 = 数十回/週なので許容範囲
- **caching 効果の不確定性**: Claude Code が独自にプロンプトキャッシュを管理するため、`AnthropicBackend` で明示付与した `cache_control: ephemeral` とは別レイヤー。定額プラン前提なので金銭的影響は無視可能
- **並列性**: Phase 2-A と同様シーケンシャル処理を維持。並列化は Phase 2-B 以降

## 既存設計判断との整合性

| 確認項目 | 参照 | 結果 |
|---|---|---|
| レイヤー配置（architecture） | Phase 1 確立の Orchestration 層 | OK — `agent/orchestration/llm.py` 内に追加 |
| 既存ユースケース | `agent/orchestration/regenerate.py` | OK — `make_backend()` の戻り値を使うだけで影響なし |
| 既存 ADR | ADR-015 / 016 / 017 | OK — 矛盾なし。ADR-018 で本拡張を明文化 |
| 命名規則 | `development-guidelines.md` | OK — `ClaudeCodeBackend`（PascalCase）、Protocol 命名と整合 |
| エラー処理 | 既存階層 | OK — `ConfigurationError` / `LLMInvocationError` を流用 |
| ファイル配置 | `repository-structure.md` | OK — `agent/orchestration/llm.py` 内追加、テストは `tests/unit/` |

## 将来の拡張性

- **GitHub Actions 週次 cron（Phase 3）**: CI 経路は `AnthropicBackend` で確定、ローカル経路は `ClaudeCodeBackend`。本設計の env var 切替で容易に対応
- **SDK 例外型の精緻化（Phase 2-B）**: `claude-agent-sdk` の例外型階層が安定したら `except Exception` を絞り込む（`AnthropicBackend` と並行）
- **モデル切替 / プロファイル管理（将来）**: env var で十分だが、複数モデルでの A/B 比較が必要になれば設定ファイル化を検討
- **Web 公開パイプライン分離（将来）**: 生成パイプライン（`ClaudeCodeBackend` 主軸）と公開パイプライン（静的サイト生成 + push）を分離可能な構造を維持
