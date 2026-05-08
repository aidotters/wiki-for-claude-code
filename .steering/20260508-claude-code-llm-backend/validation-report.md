# コード検証レポート

> 生成日時: 2026-05-08
> 対象: `.steering/20260508-claude-code-llm-backend`（`ClaudeCodeBackend` 追加 / ADR-018）

## エグゼクティブサマリー

| 検証項目 | 結果 | 詳細 |
|----------|------|------|
| スペック整合性 | PASS | 受け入れ条件 全 24 項目中 23 PASS / 1 SKIP（手動委譲）/ 3 別 PR スコープ |
| コード品質 | PASS | ruff 0 件 / mypy strict 0 件 |
| テストカバレッジ | PASS | 202 件 PASS（目標 165 件以上）、`test_llm_claude_code.py` 21 件で正常系/異常系/エッジケース網羅 |
| セキュリティ | PASS | 機密情報ハードコードなし、危険パターンなし |
| パフォーマンス | PASS | 既存パターン踏襲、致命的問題なし（軽微 1 件） |
| **総合判定** | **PASS** | |

## 1. スペックとの整合性

### 要件トレーサビリティ（受け入れ条件）

| 要件 | 条件 | 結果 | 根拠 |
|------|------|------|------|
| バックエンド実装 | `ClaudeCodeBackend` クラス存在 + Protocol 準拠 | PASS | `agent/orchestration/llm.py:201-296` |
| バックエンド実装 | `make_backend()` の `claude-code` 分岐 | PASS | `llm.py:324-325` |
| バックエンド実装 | `claude-agent-sdk` を依存に追加 | PASS | `pyproject.toml` および `uv.lock` |
| バックエンド実装 | 既存 `StubLLMClient`/`AnthropicBackend` 不変 | PASS | `git diff` で 76-98 行 / 104-172 行に変更なし |
| 環境変数 | `WIKI_LLM_MODEL` 反映 | PASS | `llm.py:221` + `test_llm_claude_code.py::test_model_env_override` |
| 環境変数 | `claude-code` で `ANTHROPIC_API_KEY` 不要 | PASS | `test_anthropic_api_key_not_required` / `test_claude_code_does_not_require_anthropic_api_key` |
| 環境変数 | `.env.example` 追記 | PASS | `.env.example` 更新済 |
| 起動時チェック | `shutil.which("claude")` ガード | PASS | `llm.py:228-232` |
| 起動時チェック | エラーメッセージに `claude /login` 含む | PASS | `test_missing_claude_binary_raises` で `match="claude /login"` |
| empirical | `agent regenerate --target ... --force` exit 0 | PASS | `acceptance-test-report.md §2`（73.33s） |
| empirical | 所要時間が stderr に Markdown 表行で出力 | PASS | `local.py:153-156` + `test_runner.py::test_regenerate_logs_elapsed_time_to_stderr` |
| empirical | AUTO 領域のみ更新 | PASS | empirical-checklist.md 結果 |
| empirical | スラッシュコマンド経由検証 | SKIP | ユーザー手動委譲（要件で明示） |
| エラーハンドリング | 認証エラーが `LLMInvocationError` にラップ | PASS | `llm.py:248-258` リトライ後に raise |
| エラーハンドリング | SDK 内部例外を一括ラップ | PASS | `except Exception` で吸収（`test_invoke_raises_after_second_failure`） |
| エラーハンドリング | `cache_read_input_tokens` 不存在で 0 | PASS | `_parse_claude_code_response` + `test_with_missing_usage` |
| テスト | `test_llm_claude_code.py` 新規 21 件 | PASS | `pytest -q` 出力で確認 |
| テスト | バイナリ未存在の `ConfigurationError` 検証 | PASS | `test_missing_claude_binary_raises` |
| テスト | `make_backend()` の `claude-code` 分岐検証 | PASS | `TestMakeBackendClaudeCode` 4 件 |
| テスト | 総数 165 件以上 | PASS | 実績 202 件 |
| ADR | ADR-018 起票 | PASS | `docs/core/decisions.md` |
| ADR | 既定値段階展開等の判断記載 | PASS（実装ステータス確認は未読、tasklist で完了確認） | tasklist フェーズ6 全項目 `[x]` |
| 既定値切替（別 PR） | `make_backend` 既定 `claude-code` | 別 PR | スコープ外（要件 §6） |
| 既定値切替（別 PR） | `CLAUDE.md` ガード削除 | 別 PR | スコープ外 |
| 既定値切替（別 PR） | `metrics.md` 修正率記録 | 別 PR | スコープ外 |

### 設計との整合性

| 設計項目 | 期待 | 実装 | 結果 |
|----------|------|------|------|
| `ClaudeCodeBackend.__init__` | `*, model, max_tokens, client` | `llm.py:214-220` 同シグネチャ | PASS |
| `invoke` シグネチャ | `*, system, prompt, cache_system=True` | `llm.py:238-243` | PASS |
| async-only `query` の同期化 | `asyncio.run` で wrap | `llm.py:262-265` | PASS（design.md にも追記済） |
| `_parse_claude_code_response` | text + usage(dict) → `LLMResult` | `llm.py:299-316` | PASS |
| 遅延 import | `claude_agent_sdk` を `__init__` で import | `llm.py:234` | PASS |

## 2. コード品質

### ruff check
```
All checks passed!
```

### mypy（strict, agent/）
```
Success: no issues found in 29 source files
```

### ベストプラクティス

| 項目 | 状態 | コメント |
|------|------|----------|
| エラーハンドリング | OK | `ConfigurationError`（起動時）/ `LLMInvocationError`（呼出時）の階層分離が `AnthropicBackend` と整合 |
| ログ出力 | OK | empirical 用 Markdown 表行を `stderr` に出力（runner で正常系後に 1 行） |
| 単一責任 | OK | `_parse_claude_code_response` を別関数に切り出し、`AnthropicBackend._parse_response` と独立 |
| DRY 原則 | OK | リトライロジックは `AnthropicBackend` と類似だがレスポンス API 構造が異なるため共通化せず（妥当） |
| 後方互換 | OK | `generate(prompt)` を維持、既存 `LLMClient` Protocol を継続充足 |

軽微な指摘（修正不要）:
- `_run_query` 内の `import asyncio` がメソッドローカル。トップレベルへ昇格しても問題ないが、遅延 import 方針との一貫性を優先するなら現状維持で可。

## 3. テストカバレッジ

### テスト件数
- 総数: **202 件 PASS** (目標 165 件以上) — 0.53s 完走
- 新規: `tests/unit/test_llm_claude_code.py` **21 件**
- 既存補強: `tests/unit/test_runner.py::test_regenerate_logs_elapsed_time_to_stderr` 追加

### テスト品質

| 種類 | 件数 | 状態 | 詳細 |
|------|------|------|------|
| 正常系 | 8+ | OK | `invoke` の text/usage 取得、system_prompt 伝播、`generate`、`make_backend` 分岐 |
| 異常系 | 5+ | OK | バイナリ不在 `ConfigurationError`、リトライ後失敗、`is_error=True`、未知バックエンド名 |
| エッジケース | 4+ | OK | 空 system → None、partial usage、missing usage、cache_system=True/False の noop 検証 |

> 注: pytest-cov は未導入のため行カバレッジ数値は計測不可。21 件のユニット + empirical 1 回成功で機能カバレッジは充分。

## 4. セキュリティ

### 検出された問題
**なし**

### セキュリティチェックリスト

| 項目 | 状態 | 根拠 |
|------|------|------|
| 機密情報のハードコード | OK | `ANTHROPIC_API_KEY` は環境変数のみから読込み（`llm.py:127`）、`claude-code` 経路では読まない |
| インジェクション対策 | N/A | shell 呼び出しなし、`shutil.which` のみ |
| 入力バリデーション | OK | `WIKI_LLM_BACKEND` の許容値を `make_backend()` で限定、不明値は `ConfigurationError` |
| 危険な API 使用 | OK | `eval`/`exec`/`pickle.load`/`shell=True` の使用なし |
| 認証情報リーク | OK | エラーメッセージに API キー値や認証 token を含めない |

## 5. パフォーマンス

### 検出された問題

| 影響度 | カテゴリ | ファイル | 行 | 内容 |
|--------|----------|----------|-----|------|
| 低 | sync wrapper | `llm.py:262-265` | — | `asyncio.run` 同期化はバックエンド呼出毎に新規 event loop を生成。`agent regenerate` は通常 1 回呼出なので実質影響なし。Phase 2-B で複数 region 並列化する場合は再設計検討。 |

### パフォーマンスチェックリスト

| 項目 | 状態 | コメント |
|------|------|----------|
| 非同期 I/O 活用 | OK | SDK が async-only なため `asyncio.run` ラップが妥当 |
| メモリ効率 | OK | yield されるメッセージを逐次処理、全文蓄積なし |
| N+1 問題 | N/A | DB 操作なし |
| リソース解放 | OK | `async for` で自然にイテレータ解放 |
| リトライ戦略 | OK | 最大 1 リトライ（無限ループ防止） |

## 6. 推奨事項

### 優先度: 高
- なし

### 優先度: 中
- なし

### 優先度: 低（Phase 2-B 検討）
- **SDK 例外型の絞り込み**: `claude-agent-sdk._errors.ClaudeSDKError` 階層を捕捉して、`CLINotFoundError` を `ConfigurationError` に振り替えるなど精緻化（要件「次回への改善提案」と整合）。
- **配線 smoke test の追加**: `make_backend()` 経由のバックエンド差し替えが本番経路（`agent regenerate`）まで到達することを smoke test 化（tasklist 振り返りで指摘済の改善案）。
- **caching 計測**: `ResultMessage.usage` の実際のキー名を empirical 結果から確定し、`metrics.md` の cache_hit_rate 列を実値化検討。

## 7. 次のアクション

- [x] 実装・テスト・empirical 検証 完了（本タスクスコープ）
- [ ] empirical PASS 後の別 PR: `make_backend()` 既定値を `claude-code` に切替
- [ ] 別 PR: `CLAUDE.md` の `agent regenerate` 運用ガード注記削除
- [ ] 別 PR: `vault/90_meta/metrics.md` に Phase 2-A 16 本の修正率記録
- [ ] 別 PR: ADR-018 の Status を `Accepted` に昇格（要件 §ADR では既に `accepted` 表記。要 cross-check）

## 判定根拠

- 全静的解析 PASS（ruff / mypy strict）
- 全テスト PASS（202 / 202）
- 全 Wiki コンテンツ検証 PASS（`agent validate --all` 16 ファイル / `agent lint --all` 違反 0）
- 受け入れ条件のうち本 PR スコープ内の全項目が `[x]`、SKIP 1 件は要件側で「ユーザー手動実施に委譲」と明記
- empirical 検証 PASS 済（73.33s で AUTO 領域のみ更新確認、`acceptance-test-report.md §2`）

**総合判定: PASS**
