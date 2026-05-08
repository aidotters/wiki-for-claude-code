# 要求内容: Claude Code バックエンド化（`ClaudeCodeBackend` 追加）

> 起点: `docs/ideas/20260508-claude-code-llm-backend.md`
> 関連 ADR: ADR-018（**accepted**, 2026-05-08 昇格）/ ADR-019（**accepted**, 2026-05-08）
> Phase 2-A 残課題: `acceptance-test-report.md §6`（A-1-6 / A-6-2 / A-6-3 / S-2）
> **実装ステータス**: PASS（2026-05-08）。empirical 検証時に `regenerate.py` の noop stub と `make_backend()` 配線バグが発覚し、ADR-019 として並行解決。

## 概要

`agent/orchestration/llm.py` の `LLMBackend` Protocol に **3 つ目の実装** として `ClaudeCodeBackend` を追加し、Anthropic API 直接呼び出しの代わりに **Claude Code (Max プラン) 経由** で LLM を呼び出せるようにする。`WIKI_LLM_BACKEND=claude-code` で選択し、Max プラン定額枠を活用したローカル日次自動化（cron / launchd）を主用途とする。

## 背景

### なぜ必要か

- Phase 2-A 実装済みの `AnthropicBackend` は `ANTHROPIC_API_KEY` 必須・**従量課金**前提。ユーザーは Max プランを契約済みで定額枠を活用したい
- 想定運用は「Claude Code 関連情報を **ローカル cron / launchd** で定期取り込み → Obsidian で閲覧 → 将来は Web 公開へ同期」というローカル運用主軸
- 記事数増加に伴う API コスト線形増加を回避したい
- `acceptance-test-report.md §6.1` で方針転換が起票済みで、検討事項 5 点（§6.2）が別セッション課題として残置

### 解決したいこと

- Max プラン定額枠を主たる LLM 呼び出し経路として活用
- `AnthropicBackend` を **CI / API 利用者向けの選択肢** として残置、`WIKI_LLM_BACKEND` で切替
- Phase 2-A の規約・実装・テスト 159 件 PASS に **影響を与えない**（既存 Protocol 拡張のみ）
- empirical 検証経路を再設計し、Phase 2-A クローズ判定を `ClaudeCodeBackend` 側で通せるようにする（acceptance-test-report.md §6.1 案 Y 採用）

## 実装対象の機能

### 1. `ClaudeCodeBackend` 実装

- `agent/orchestration/llm.py` に `LLMBackend` Protocol 実装として `ClaudeCodeBackend` クラスを追加
- `claude-agent-sdk`（Anthropic 公式 Python パッケージ）経由で LLM を呼び出す
- 既存 `LLMBackend.invoke(system, prompt, cache_system) -> LLMResult` シグネチャをそのまま実装
- モデル既定 `claude-sonnet-4-6`、`WIKI_LLM_MODEL` で上書き可能
- レスポンスを `LLMResult` データクラスに正規化（`cache_read_input_tokens` 取得不可時は `0` を入れて `usage.cache_hit_rate` が 0.0 を返す状態にする）

### 2. 環境変数拡張

- `WIKI_LLM_BACKEND` の許容値を `stub|anthropic|claude-code` の 3 値に拡張
- 既定値は **段階展開**:
  - empirical 検証 PASS 前: `stub`（既存維持）
  - empirical 検証 PASS 後: `claude-code`（β 案、ADR-018 で明文化）
- `claude-code` 選択時は `ANTHROPIC_API_KEY` を読まない（読まれないことをテストで検証）
- `WIKI_LLM_MODEL` は全バックエンドで有効、`claude-code` でも反映

### 3. 起動時バイナリチェック

- `ClaudeCodeBackend.__init__` で `shutil.which("claude")` により `claude` バイナリが PATH に存在するか確認
- 不在の場合、`ConfigurationError`（exit code 3）で停止
- エラーメッセージに `claude /login` 等への誘導を含める
- 認証エラーは API 呼び出し時の例外で拾い、`LLMInvocationError` にラップ（exit code 3、既存階層）

### 4. ADR-018 起票

- `docs/core/decisions.md` に ADR-018 を追記
- 決定事項: `claude-agent-sdk` 採用 / `AnthropicBackend` 残置 / `StubBackend` 残置 / env var 拡張 / 既定値段階展開
- 影響: Phase 2-A クローズ条件は変更しない（acceptance-test-report.md §6.3 と整合）
- 関連 ADR: ADR-015 / ADR-016 / ADR-017 を踏襲

### 5. empirical 検証（Phase 2-A 案 Y 経路）

> **対象ページ**: 現行 `agent regenerate` は `type=source` のみ処理対象（`agent/orchestration/regenerate.py:55`）であり recipe を渡すと `FrontmatterValidationError` で弾かれる。本検証スコープは `ClaudeCodeBackend` の動作確認であり、AUTO マーカー導入済みの公式 source ページで十分検証可能。recipe の regenerate 対応は Phase 2-B 以降。

- `WIKI_LLM_BACKEND=claude-code uv run agent regenerate --target vault/sources/official/cli/basic-usage.md` を成功させる
- ローカル Claude Code から `/wiki-regenerate vault/sources/official/cli/basic-usage.md` で AUTO 領域のみ更新されることを確認
- 実行時の所要時間を `metrics.md` に追記可能な形式（Markdown 表行）でログ出力する

### 6. 既定値切替（empirical PASS 後）

- `WIKI_LLM_BACKEND` 既定を `make_backend` 内で `claude-code` に昇格
- `CLAUDE.md` の `agent regenerate` 本番運用ガード注記を削除（Phase 2-A A-1-6 の解消）
- `metrics.md` に Phase 2-A 対象 16 本（公式 11 + recipe 5）の修正率を記録（Phase 2-A A-6-2 / A-6-3 の解消）

## 受け入れ条件

### バックエンド実装

- [x] `agent/orchestration/llm.py` に `ClaudeCodeBackend` クラスが存在し、`LLMBackend` Protocol を満たす（mypy strict で検証）
- [x] `make_backend()` が `WIKI_LLM_BACKEND=claude-code` のとき `ClaudeCodeBackend` インスタンスを返す
- [x] `claude-agent-sdk` が `pyproject.toml` の依存に追加されており、`uv lock` 後にロックファイルへ反映されている
- [x] `AnthropicBackend`（`llm.py:104-172`）と `StubLLMClient`（`llm.py:76-101`）の実装行に変更がない（`git diff` で確認）

### 環境変数・設定

- [x] `WIKI_LLM_MODEL` 環境変数の値が `ClaudeCodeBackend.model` に反映される（mock テストで検証）
- [x] `WIKI_LLM_BACKEND=claude-code` 選択時、`ANTHROPIC_API_KEY` が未設定でも `ConfigurationError` が発生しない
- [x] `.env.example` に `WIKI_LLM_BACKEND=claude-code` の例とコメントが追記されている

### 起動時チェック

- [x] `claude` バイナリ未存在環境で `WIKI_LLM_BACKEND=claude-code` 指定時、`ConfigurationError`（exit code 3）が発生する
- [x] エラーメッセージに `claude /login` 文字列が含まれる
- [x] バイナリ存在時は `__init__` が例外なく完了する

### empirical 検証（Phase 2-A 案 Y 経路）

> **2026-05-08 実施結果**: PASS。ADR-019 完了後に `--force` フラグ付きで再実行し、73.33s（実 LLM 実走の確証）で AUTO 領域のみ更新を確認。詳細は `empirical-checklist.md` および `acceptance-test-report.md §2`。

- [x] `WIKI_LLM_BACKEND=claude-code uv run agent regenerate --target vault/sources/official/cli/basic-usage.md --force` が exit code 0 で完了する（実績: 0）
- [x] 実行ログから所要時間（秒）が stderr に Markdown 表行形式で出力される（実績: `| 2026-05-08 | sources/official/cli/basic-usage.md | claude-code | 73.33s | N/A | 0 |`）
- [x] 実行後、`vault/sources/official/cli/basic-usage.md` の AUTO 領域のみが更新され、AUTO 外（`## 公式ドキュメント` 以降）は変更されない（実績: `git diff` で確認）
- [⏭] ローカル Claude Code から `/wiki-regenerate vault/sources/official/cli/basic-usage.md --force` を実行し、上記と同じ条件を満たす（**ユーザー手動実施に委譲**: スラッシュコマンドは別 Claude Code セッション要、CLI と同コードパスで実装上 PASS）

### 既定値切替（empirical PASS 後の別 PR）

- [ ] `make_backend()` 内の既定値が `claude-code` になっている
- [ ] `CLAUDE.md` の `> ⚠ agent regenerate の運用注意` 注記が削除されている
- [ ] `vault/90_meta/metrics.md` に Phase 2-A 対象 16 本の修正率（人手修正件数 / 全件数）が表形式で記録されている

### エラーハンドリング

- [x] API 呼び出し時の認証エラーが `LLMInvocationError`（exit code 3）にラップされる
- [x] `claude-agent-sdk` 内部例外（型は SDK 提供の例外基底クラス、不明時は `Exception`）も `LLMInvocationError` にラップされる
- [x] `cache_read_input_tokens` が SDK レスポンスに存在しない場合、`LLMUsage.cache_read_input_tokens` は `0` を保持し、`metrics.md` への記録時は `N/A` で書ける

### テスト

- [x] `tests/unit/test_llm_claude_code.py` が新規追加され、mock 経由で `invoke` の正常系を検証する（21 件）
- [x] バイナリ未存在時の `ConfigurationError` をユニットテストで再現する（`shutil.which` を mock）
- [x] `make_backend()` の `claude-code` 分岐をテストで検証する
- [x] テスト総数が **159 → 165 件以上**に増加する（実績: ADR-018 で 181 件 → ADR-019 完了後 **202 件**）
- [x] `uv run pytest tests/` が全 PASS（exit code 0）
- [x] `uv run ruff check .` が PASS（exit code 0）
- [x] `uv run mypy agent` が PASS（exit code 0）

### ADR

- [x] `docs/core/decisions.md` に ADR-018 が追加されている
- [x] ADR-018 内に「`AnthropicBackend` を CI / API 利用者向けに残置」「`StubBackend` をテスト DI / オフライン用途に残置」「既定値段階展開」の判断が明文化されている
- [x] ADR-018 / ADR-019 が `accepted` に昇格されている（2026-05-08）

## 成功指標

- [x] ユニットテスト 165 件以上 PASS（実績: **202 件**）
- [x] empirical で `agent regenerate --force` がローカル Max プランで動作し、API 課金 0 円で 1 記事再生成できる（実績: 73.33s で AUTO 領域更新確認）
- [x] Phase 2-A 残課題 4 点（A-1-6 / A-6-2 / A-6-3 / S-2）が本機能完成後の後続 PR で解消可能な状態に到達（empirical PASS 済みで残作業は規定通り別 PR スコープ）

> **追加で副次的に解消した課題（ADR-019 で対応）**:
> - `regenerate.py` の AUTO 領域 noop stub → 実 LLM 呼び出しに昇格
> - `regenerate_source` の `llm = StubLLMClient()` ハードコード → `make_backend()` 配線に修正
> - AUTO マーカーの `purpose` メタデータ導入（per-region prompt ディスパッチ）
> - 旧 `source-regenerate` フルファイル経路（デッドコード）削除

## スコープ外

以下はこのフェーズでは実装しない:

- **GitHub Actions / CI 環境での `claude-code` バックエンド対応**: Max プラン認証は個人サブスクで CI では一般に通らない。CI は `anthropic` または `stub` で運用（ADR-018 に明記、追加実装なし）
- **caching 効果の積極的計測**: Claude Code 経由では `cache_read_input_tokens` の観測可否が不確定。caching 検証は `AnthropicBackend` 側に残置
- **`AnthropicBackend` の廃止・既定降格**: CI / API 利用者向けに残置
- **`agent metrics` サブコマンドによる metrics.md 自動追記**: Phase 2-B 検討事項
- **モデル切替 UI / 設定ファイル化**: env var で十分
- **Web 公開パイプライン本体**: 生成側のみが本機能スコープ
- **`claude-agent-sdk` 内部例外型の精緻な絞り込み**: Phase 2-B で `AnthropicBackend` の `except Exception` 絞り込みと並行実施

## 参照ドキュメント

- `docs/ideas/20260508-claude-code-llm-backend.md` — 起点アイデア
- `.steering/20260506-llm-wiki-for-claude-code-phase-2a/acceptance-test-report.md` §6 — 方針更新の起点
- `agent/orchestration/llm.py:61-71` — `LLMBackend` Protocol
- `agent/orchestration/llm.py:73-98` — `StubLLMClient`
- `agent/orchestration/llm.py:101-169` — `AnthropicBackend`
- `agent/errors.py:58-67` — `ConfigurationError` / `LLMInvocationError`
- `docs/core/decisions.md` — ADR-018 起票先
- `CLAUDE.md` — Phase 2-A ステータスと運用ガード注記（A-1-6 解消対象）
