# タスクリスト: `ClaudeCodeBackend` 追加

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを `[x]` にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### スコープ境界（本 tasklist の対象範囲）

本 tasklist は **Phase 1（実装）+ Phase 2（empirical 検証準備）** までを対象とする。
以下は **本タスクの完了条件外** とし、別 PR / 別セッションで実施する:

- empirical 検証の実行本体（`/wiki-regenerate` 実走、AUTO 領域更新確認）
- `WIKI_LLM_BACKEND` 既定値の `claude-code` への昇格
- `CLAUDE.md` の `agent regenerate` ガード注記削除
- `vault/90_meta/metrics.md` への Phase 2-A 16 本の修正率記録

これらは empirical 検証 PASS が前提であり、本実装完了後に手順書として引き継ぐ。

---

## フェーズ1: 依存追加と雛形

- [x] `claude-agent-sdk` を依存に追加
  - [x] `uv add claude-agent-sdk` を実行（実バージョン下限を確認）
  - [x] `pyproject.toml` の `[project] dependencies` に追記されたことを確認
  - [x] `uv.lock` が更新され、ロックされたバージョンを記録

- [x] `claude-agent-sdk` の API 形態を確認
  - [x] SDK の同期 / 非同期 API の有無を確認（公式ドキュメントまたは `pip show claude-agent-sdk` の location から）
  - [x] メッセージ作成 API のシグネチャと引数（system / messages / model）を特定
  - [x] レスポンスオブジェクトのフィールド構造（content / usage / `cache_*_input_tokens` の有無）を特定
  - [x] 確認結果を design.md に追記（実装着手前に確定）

## フェーズ2: `ClaudeCodeBackend` 実装

- [x] `agent/orchestration/llm.py` に `ClaudeCodeBackend` クラスを追加
  - [x] クラス本体を `AnthropicBackend` の直後に追加
  - [x] `__init__(*, model=None, max_tokens=DEFAULT_MAX_TOKENS, client=None)` を実装
  - [x] `client is None` 経路で `shutil.which("claude")` を実行し、不在時 `ConfigurationError("claude バイナリが PATH にありません。`claude /login` を実行してセットアップしてください")` を raise
  - [x] `claude-agent-sdk` を遅延 import（`StubLLMClient` 使用時に依存を読まないため）
  - [x] `model` 既定 `DEFAULT_MODEL`、`WIKI_LLM_MODEL` 環境変数で上書き可能（`AnthropicBackend` と同パターン）

- [x] `invoke(*, system, prompt, cache_system=True) -> LLMResult` を実装
  - [x] SDK のメッセージ作成 API を呼び出し
  - [x] 1 回失敗時にリトライし、再失敗時に `LLMInvocationError` を raise（`AnthropicBackend` と同パターン）
  - [x] レスポンスを `_parse_claude_code_response`（後述）で `LLMResult` に正規化
  - [x] `cache_system=True` 時の振る舞いを SDK 仕様に応じて実装（`cache_control` 相当が無ければ noop）

- [x] `generate(prompt: str) -> str` を後方互換のために実装
  - [x] 内部で `invoke(system="", prompt=prompt, cache_system=False).text` を返す

- [x] `_parse_claude_code_response(response) -> LLMResult` ヘルパを追加
  - [x] `response.content` から text を抽出
  - [x] `response.usage` から `input_tokens` / `output_tokens` を抽出（存在しない場合 0）
  - [x] `cache_creation_input_tokens` / `cache_read_input_tokens` は存在すれば抽出、無ければ 0

## フェーズ3: `make_backend()` 拡張

- [x] `make_backend()` に `claude-code` 分岐を追加
  - [x] `backend_name == "claude-code"` で `ClaudeCodeBackend()` を返す
  - [x] 不明値時の `ConfigurationError` メッセージを `stub` / `anthropic` / `claude-code` の 3 値表記に更新

- [x] `agent/orchestration/llm.py` の docstring を更新
  - [x] `WIKI_LLM_BACKEND=claude-code` の選択肢を追記
  - [x] `ANTHROPIC_API_KEY` は `anthropic` 選択時のみ必須である旨を明記

## フェーズ4: テスト追加

- [x] `tests/unit/test_llm_claude_code.py` を新規作成
  - [x] `ClaudeCodeBackend` の正常系: mock client 注入で `invoke` が `LLMResult` を返すことを検証
  - [x] `WIKI_LLM_MODEL` 環境変数が `model` に反映されることを検証
  - [x] `shutil.which("claude")` が `None` の時 `ConfigurationError` が raise されることを検証（`monkeypatch.setattr` 使用）
  - [x] `ANTHROPIC_API_KEY` 未設定でも `__init__` が成功することを検証（`client` 注入経路）
  - [x] mock client が例外を投げると `LLMInvocationError` にラップされることを検証
  - [x] mock client が 1 回目失敗 / 2 回目成功すると `invoke` が成功することを検証（リトライ動作）
  - [x] `_parse_claude_code_response` のテスト: usage フィールド有 / 無の両ケースを検証

- [x] `tests/unit/test_llm_anthropic.py` または既存の `make_backend` 関連テストに追記
  - [x] `WIKI_LLM_BACKEND=claude-code` で `ClaudeCodeBackend` インスタンスが返ることを検証
  - [x] 不明値の `ConfigurationError` メッセージが 3 値表記であることを検証

- [x] テスト総数を確認
  - [x] `uv run pytest tests/ --collect-only -q | tail -1` で 165 件以上であることを確認

## フェーズ5: 設定ファイル更新

- [x] `.env.example` を更新
  - [x] `WIKI_LLM_BACKEND` セクションに `claude-code` 例を追記
  - [x] `claude-code` 選択時は `ANTHROPIC_API_KEY` 不要である旨をコメントで記載
  - [x] `claude-code` 選択時の前提（`claude` バイナリ + Max プラン認証済み）をコメントで記載

## フェーズ6: ADR-018 起票

- [x] `docs/core/decisions.md` に ADR-018 を追加
  - [x] タイトル: `ADR-018: LLM バックエンドの Claude Code 経由化（`ClaudeCodeBackend` 追加）`
  - [x] Status: `Proposed`（実装完了の別 PR で `Accepted` に昇格）
  - [x] Context: Max プラン定額枠活用の動機、Phase 2-A acceptance §6 の方針転換
  - [x] Decision: `claude-agent-sdk` 採用 / `AnthropicBackend` 残置 / `StubBackend` 残置 / env var 拡張 / 既定値段階展開
  - [x] Consequences: CI 経路は `anthropic` 維持、caching 効果計測の主指標を修正率に切替、SDK 仕様変動リスク
  - [x] Related: ADR-015 / ADR-016 / ADR-017 を踏襲

## フェーズ7: 品質チェックと修正

- [x] すべてのテストが PASS することを確認
  - [x] `uv run pytest tests/` が exit code 0 で完了
  - [x] テスト件数が 165 件以上

- [x] リントエラーがないことを確認
  - [x] `uv run ruff check .` が exit code 0 で完了
  - [x] 必要に応じて `uv run ruff format .` でフォーマット適用

- [x] 型エラーがないことを確認
  - [x] `uv run mypy agent` が exit code 0 で完了（strict）

- [x] Wiki コンテンツ検証が PASS することを確認
  - [x] `uv run agent validate --all` が exit code 0 で完了
  - [x] `uv run agent lint --all` が違反 0 で完了

- [x] 既存実装に変更がないことを確認
  - [x] `git diff agent/orchestration/llm.py` で `StubLLMClient`（73-98 行相当）と `AnthropicBackend`（101-169 行相当）に変更が入っていないことを確認

## フェーズ8: empirical 検証の準備

- [x] empirical 検証手順書を `.steering/20260508-claude-code-llm-backend/empirical-checklist.md` に作成
  - [x] 前提条件（`claude` バイナリ存在、Max プラン認証済み）
  - [x] 手順1: `WIKI_LLM_BACKEND=claude-code uv run agent regenerate --target vault/sources/official/cli/basic-usage.md` 実行（recipe は `agent regenerate` 非対応のため source ページに変更、2026-05-08）
  - [x] 手順2: 実行ログから所要時間を `metrics.md` 形式（Markdown 表行）に転記
  - [x] 手順3: `git diff vault/sources/official/cli/basic-usage.md` で AUTO 領域のみ更新されていることを確認
  - [x] 手順4: ローカル Claude Code から `/wiki-regenerate vault/sources/official/cli/basic-usage.md` 実行、同じ AUTO-only 更新を確認
  - [x] PASS / FAIL 判定基準: exit code 0 + AUTO 領域のみ差分 + 所要時間ログ出力

- [x] empirical 検証で PASS した場合の後続タスクを別 PR 用に明記
  - [x] empirical-checklist.md 末尾に「PASS 後の別 PR 作業」として以下を箇条書き:
    - `make_backend()` 既定値を `claude-code` に変更
    - `CLAUDE.md` の `agent regenerate` 運用ガード注記を削除
    - `vault/90_meta/metrics.md` に Phase 2-A 対象 16 本の修正率を記録
    - ADR-018 の Status を `Accepted` に昇格

---

## 実装後の振り返り

### 実装完了日
2026-05-08

### 計画と実績の差分

**計画と異なった点**:
- `claude-agent-sdk` は同期 API を提供せず、`query()` が **async-only** の AsyncIterator のみ。`invoke` の同期シグネチャを維持するため、`asyncio.run` でラップする実装に確定。
- メッセージ作成 API は `messages.create` 形式ではなく、`query(*, prompt, options=ClaudeAgentOptions(...))` 形式（`system_prompt` / `model` / `max_turns` を `ClaudeAgentOptions` に集約）。`AnthropicBackend` の SDK API パターンとは構造が異なるため、`_parse_claude_code_response` を別ヘルパとして切り出した。
- レスポンスは `AssistantMessage`（`content: list[ContentBlock]`、`TextBlock.text`）と `ResultMessage`（`usage: dict[str, Any] | None`、`is_error: bool`）が混在して yield される。テスト側で `isinstance` ではなく `type(x).__name__` で分岐する設計（モックで dataclass の `__name__` を上書き）に着地した。
- `claude-agent-sdk` 0.1.77 のロック版が 57.8MiB と想定より大きい（mcp / cryptography / pydantic-settings / starlette 等のスタックを引き連れる）。CI / dev 環境でのインストールサイズ増は許容範囲だが、将来 Phase 2-B で評価対象。

**新たに必要になったタスク**:
- `_parse_claude_code_response` ヘルパの追加（`AnthropicBackend` の `_parse_response` とはレスポンス形態が違うため共通化せず別関数化）
- `is_error=True` の `ResultMessage` を `LLMInvocationError` にラップする経路の追加（SDK 仕様で「成功 yield 後に is_error の ResultMessage」がありうるため）
- テストヘルパ `_FakeSDK` の `side_effect` 経路の追加（リトライ検証で連続呼び出しの異なるレスポンスを返すため）
- **(2026-05-08 追記) ADR-019 として並行作業を起票・実装**: 当初 empirical 検証実施段階で `agent regenerate` の `auto_section_managed=true` 経路が noop stub のため `ClaudeCodeBackend.invoke` を呼ばないことが判明。さらに `regenerate_source` の `llm` 既定値が `StubLLMClient()` ハードコードで `make_backend()` 経由のバックエンド差し替えが効かない配線バグも発覚。両者を ADR-019（AUTO 領域経路で LLM 実呼び出し）として並行解決し、ADR-018 の empirical PASS まで到達した（73.33s で実走確認）。詳細は `.steering/20260508-adr-019-auto-region-llm/`

**技術的理由でスキップしたタスク**:
- なし（全 8 フェーズのチェックを完走）

### 学んだこと

**技術的な学び**:
- `claude-agent-sdk` の `query()` は **async-only** で、同期コードからは `asyncio.run` で呼び出す必要がある。既存 `LLMBackend.invoke` の同期シグネチャを保ったまま、内部で AsyncIterator を消費するパターンが綺麗に収まった。
- `ClaudeAgentOptions` に `system_prompt` / `model` / `max_turns` を集約する設計は、`AnthropicBackend` の messages.create API（system / messages を別パラメータ）とは大きく違うが、`LLMBackend` Protocol の `invoke(system, prompt, cache_system)` 抽象を介在することで Orchestration 層からは差を吸収できた。Protocol 設計が拡張に効いた。
- `claude-agent-sdk` の `CLINotFoundError` が SDK 内部から raise される経路もあるが、`__init__` で `shutil.which("claude")` による先行チェックを置く方が、`ConfigurationError` との階層分離（exit code 3 / 起動時 vs 呼び出し時）が明確になった。

**プロセス上の改善点**:
- Phase 2-A で確立した `LLMBackend` Protocol と `make_backend()` の env-var 分岐が、3 つ目のバックエンド追加で **完全に並列拡張のみで完結**（既存実装に変更なし）。Phase 1〜2-A のレイヤー設計が想定通りに機能した。
- `client` 注入経路を `__init__` の `client: Any` で維持したことで、本番経路の `shutil.which` チェックを mock しなくてもユニットテストが組めた（`monkeypatch.setattr(llm_module.shutil, "which", ...)` も併設）。
- **(2026-05-08 追記) empirical を「実装フェーズ後の別作業」に切り出した代償**: ユニットテストが全 PASS していてもバックエンド配線が本番経路に届いていない事例を露出させたのは empirical 1 回目だった。「ユニット PASS = 機能する」の思い込みを是正し、Phase 2-B 以降は最低 1 回の empirical 実行を実装 PR の一部として組み込む運用に切り替えるべき。

## レポート指摘事項の対応

> ソース: acceptance-test-report.md (2026-05-08)

### 優先度: 高（FAIL修正）
- [x] #23: `agent regenerate` 実行時の所要時間（秒）を stdout/stderr に出力する
  - 対象: `agent/runners/local.py::_cmd_regenerate`
  - 実装: `time.perf_counter()` で前後を挟み、empirical-checklist の Markdown 表行形式 (`| YYYY-MM-DD | <path> | <backend> | <秒>s | <cache_hit_rate> | 0 |`) を stderr に出力
  - バックエンド名は `WIKI_LLM_BACKEND` 環境変数（未設定時 `stub`）から取得
  - 検証: `tests/unit/test_runner.py` に所要時間ログ出力のユニットテストを追加

### 次回への改善提案

- **SDK 例外型絞り込み**: `claude-agent-sdk._errors` の `ClaudeSDKError` / `CLINotFoundError` / `ProcessError` / `CLIJSONDecodeError` / `MessageParseError` の階層が把握できたので、Phase 2-B で `AnthropicBackend` の `except Exception` 絞り込みと並行して、`ClaudeCodeBackend.invoke` でも `CLINotFoundError` を `ConfigurationError` に振り替えるなどの精緻化が可能。
- **empirical 検証経路の自動化**: `.steering/20260508-claude-code-llm-backend/empirical-checklist.md` の手順 1〜4 は半手動。Phase 2-B の `agent metrics` サブコマンド（修正率自動追記）と組み合わせて、CLI 一発で検証 + ログ出力 + metrics 追記まで実行する案を検討。
- **caching 効果計測**: `cache_read_input_tokens` が `claude-agent-sdk` 経由でも一部観測可能なら、`metrics.md` の cache_hit_rate 列を `N/A` 一律ではなく実値とする運用に切替できる余地あり。empirical 検証時に `ResultMessage.usage` の実際のキー名を記録しておくこと。
- **(2026-05-08 追記) 配線テストのカバレッジ強化**: `make_backend()` 経由のバックエンド差し替えが本番経路（`agent regenerate`）まで到達することを smoke test として 1 件追加することで、`StubLLMClient()` ハードコード回帰を防止できる。
- **(2026-05-08 追記) `yaml.safe_dump` のクォートスタイル安定化**: empirical 後の `git diff` で frontmatter のクォートスタイルが書き換わるノイズを削減するため、カスタム dumper の導入を Phase 2-B で検討。
