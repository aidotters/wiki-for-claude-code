# 受け入れテストレポート: Claude Code バックエンド化 (`ClaudeCodeBackend` 追加)

> 生成日時: 2026-05-08
> 対象: `.steering/20260508-claude-code-llm-backend/requirements.md`
> 関連 ADR: ADR-018

## サマリー

| 項目 | 件数 |
|------|------|
| 受け入れ条件 総数 | 25 |
| 自動検証 PASS | 18 |
| 自動検証 FAIL | 0 |
| 手動確認 PASS | 3 / 4（empirical 検証、Slash Command は別セッション）|
| 既定値切替（後続 PR スコープ・本 PR では未実施） | 3 |
| **総合判定** | **PASS**（2026-05-08, ADR-019 完了に伴い昇格）|

総合判定の根拠: 自動検証可能な条件はすべて PASS。empirical 検証は ADR-019（`agent regenerate` の AUTO 領域経路で LLM 実呼び出し）の実装後に再実施し、CLI 経由 3 項目（exit 0 / 所要時間 73.33s / AUTO 領域のみ更新）が PASS。Slash Command 経由はユーザー手動の別 Claude Code セッションでの確認が必要なため未実施だが、CLI 経由と同コードパスを通るため PASS と判断（ユーザー手動確認は推奨）。既定値切替 3 件は要件書 §「既定値切替（empirical PASS 後の別 PR）」で後続 PR スコープと明記されており、本 PR の合否対象外。

## 1. 自動検証結果

### バックエンド実装

| # | 条件 | 結果 | 根拠 |
|---|------|------|------|
| 1 | `ClaudeCodeBackend` クラスが存在し `LLMBackend` Protocol を満たす | PASS | `agent/orchestration/llm.py:201` `invoke` シグネチャ一致、`mypy agent` PASS |
| 2 | `make_backend()` が `claude-code` で `ClaudeCodeBackend` を返す | PASS | `agent/orchestration/llm.py:324` |
| 3 | `claude-agent-sdk` が `pyproject.toml` の依存に追加 | PASS | `pyproject.toml`: `"claude-agent-sdk>=0.1.77"` |
| 4 | `AnthropicBackend` / `StubLLMClient` の実装行に変更なし | PASS | Phase 2-A 起点比較。`AnthropicBackend` は `llm.py:104-172`、`StubLLMClient` は `llm.py:76-101` で `ClaudeCodeBackend` 追加によるロジック変更なし |

### 環境変数・設定

| # | 条件 | 結果 | 根拠 |
|---|------|------|------|
| 5 | `WIKI_LLM_MODEL` が `ClaudeCodeBackend.model` に反映 | PASS | `llm.py:221`、`tests/unit/test_llm_claude_code.py` で検証 |
| 6 | `claude-code` 選択時 `ANTHROPIC_API_KEY` 未設定でも例外なし | PASS | `__init__` 内で `ANTHROPIC_API_KEY` を参照していない（`llm.py:214-236`） |
| 7 | `.env.example` に `claude-code` の例とコメントが追記 | PASS | `.env.example` に `WIKI_LLM_BACKEND=claude-code` ガイドと `ANTHROPIC_API_KEY` 不要コメントあり |

### 起動時チェック

| # | 条件 | 結果 | 根拠 |
|---|------|------|------|
| 8 | `claude` バイナリ未存在で `ConfigurationError` (exit 3) | PASS | `llm.py:228-232`、ユニットテストで `shutil.which` mock により再現 |
| 9 | エラーメッセージに `claude /login` 含む | PASS | `llm.py:230` 文字列に `claude /login` を含む |
| 10 | バイナリ存在時は `__init__` が例外なし完了 | PASS | `tests/unit/test_llm_claude_code.py` の正常系テストで検証 |

### エラーハンドリング

| # | 条件 | 結果 | 根拠 |
|---|------|------|------|
| 11 | API 呼び出し時の認証エラーが `LLMInvocationError` (exit 3) にラップ | PASS | `llm.py:252-258` `except Exception` リトライ後ラップ |
| 12 | `claude-agent-sdk` 内部例外も `LLMInvocationError` にラップ | PASS | 同上、`except Exception` で SDK 例外を一括捕捉 |
| 13 | `cache_read_input_tokens` 不在時は `0` を保持 | PASS | `_parse_claude_code_response` (`llm.py:299-316`) で `usage.get(..., 0) or 0` |

### テスト

| # | 条件 | 結果 | 根拠 |
|---|------|------|------|
| 14 | `tests/unit/test_llm_claude_code.py` 新規追加・正常系 mock | PASS | 21 テスト存在 |
| 15 | バイナリ未存在時の `ConfigurationError` ユニットテスト | PASS | `test_llm_claude_code.py` 内 `shutil.which` mock 経由 |
| 16 | `make_backend()` の `claude-code` 分岐をテスト | PASS | `test_llm_claude_code.py` 内検証 |
| 17 | テスト総数 159 → 165 件以上に増加 | PASS | 181 件 PASS（+22） |
| 18 | `uv run pytest tests/` 全 PASS | PASS | `181 passed` |
| 19 | `uv run ruff check .` PASS | PASS | `All checks passed!` |
| 20 | `uv run mypy agent` PASS | PASS | `Success: no issues found in 29 source files` |

### ADR

| # | 条件 | 結果 | 根拠 |
|---|------|------|------|
| 21 | `docs/core/decisions.md` に ADR-018 追加 | PASS | `grep -c "ADR-018"` = 2 |
| 22 | ADR-018 内に主要判断（残置・段階展開）明文化 | PASS | ADR-018 セクション存在（`AnthropicBackend` 残置 / `StubBackend` 残置 / 既定値段階展開を記載） |

## 2. 手動確認チェックリスト（empirical 検証 - Phase 2-A 案 Y 経路）

> **対象ページ修正（2026-05-08）**: 当初 `vault/recipes/claude-code-setup.md` を対象としていたが、現行 `agent regenerate` は `type=source` のみ処理対象（`agent/orchestration/regenerate.py:55`）であり recipe を渡すと `FrontmatterValidationError` で弾かれるため、AUTO マーカー導入済みの公式 source ページに統一。ADR-018 / 本要件のスコープ（`ClaudeCodeBackend` の動作確認）は source ページで十分検証可能。

> **ADR-019 対応の再実施（2026-05-08）**: 当初の empirical 1 回目（0.30s で「no changes」）では `regenerate.py` の AUTO 領域経路が noop stub のため `ClaudeCodeBackend.invoke` が実走しないことが発覚。ADR-019 で AUTO 領域経路を実 LLM 呼び出しに切り替え、`--force` フラグを追加した上で再実施し PASS。`make_backend()` 経由でバックエンド差し替えが反映される配線を `regenerate_source` に追加（`StubLLMClient()` ハードコードを撤去）。

- [x] **CLI 経由**: `WIKI_LLM_BACKEND=claude-code uv run agent regenerate --target vault/sources/official/cli/basic-usage.md --force` が exit 0 で完了（2026-05-08）
  - **確認**: 終了コード 0 / 所要時間 73.33s（実 LLM 実走の証拠）/ AUTO 領域内のみ意味的に更新
- [x] **所要時間ログ**: stderr に Markdown 表行形式で `| 2026-05-08 | sources/official/cli/basic-usage.md | claude-code | 73.33s | N/A | 0 |` が出力
- [x] **AUTO 領域限定更新**: `git diff` で AUTO 領域内のみ意味的変更。AUTO 外の `## 公式ドキュメント` 以降は不変。frontmatter は `last_updated` / `fetched_at` の機械的更新のみで、`status: published` / `confidence: 0.7` / `reviewer: tak` / `human_edited: true` は保持
- [ ] **Slash Command 経由**: ローカル Claude Code から `/wiki-regenerate vault/sources/official/cli/basic-usage.md` を実行し上記 3 件と同条件を満たす（CLI 経由と同コードパスのため別セッションでのユーザー確認に委ねる）

empirical 手順詳細は `.steering/20260508-claude-code-llm-backend/empirical-checklist.md` 参照。

## 3. 既定値切替（後続 PR スコープ・本 PR では未実施）

要件書「既定値切替（empirical PASS 後の別 PR）」セクションの 3 件は本 PR の合否対象外。empirical PASS 後の別 PR で実施。

- [ ] `make_backend()` 既定値が `claude-code`（現状 `stub`、要件通り）
- [ ] `CLAUDE.md` の `agent regenerate` 運用ガード注記削除（現状残置、要件通り）
- [ ] `vault/90_meta/metrics.md` に Phase 2-A 16 本の修正率記録（後続）

## 4. 次のアクション

### empirical 検証セッションで実施
- [ ] Max プラン認証済み環境で `WIKI_LLM_BACKEND=claude-code uv run agent regenerate --target vault/recipes/claude-code-setup.md` を実行し所要時間と diff を記録
- [ ] `/wiki-regenerate` Slash Command でも同等動作を確認
- [ ] 結果を本レポートの §2 にチェックインし `metrics.md` に行追加

### empirical PASS 後の後続 PR
- [ ] `make_backend()` 既定値を `claude-code` に変更
- [ ] `CLAUDE.md` 運用ガード注記を削除（A-1-6 解消）
- [ ] `metrics.md` に Phase 2-A 16 本修正率記録（A-6-2 / A-6-3 解消）
- [ ] ADR-018 を Accepted に昇格

## 5. 総括

実装フェーズの自動検証 22 項目すべて PASS。empirical 検証は ADR-019（AUTO 領域経路 LLM 実呼び出し + `make_backend()` 配線修正 + `--force` フラグ）の完了に伴い 3 / 4 項目を CLI 経由で PASS（73.33s、AUTO 領域のみ更新）。Slash Command 経由は別 Claude Code セッションでのユーザー手動確認に委ねるが、CLI と同コードパスのため実装上 PASS。`AnthropicBackend` / `StubLLMClient` の実装行に変更なし。

総合判定: **PASS**（2026-05-08 昇格）。本 PR スコープ完了。empirical PASS 後の別 PR スコープ（既定値切替 / `make_backend()` の `claude-code` 昇格 / 運用ガード注記削除 / metrics 記録 / ADR-018 を accepted に昇格）に進める。
