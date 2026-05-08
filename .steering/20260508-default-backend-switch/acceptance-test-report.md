# 受け入れテストレポート

> 生成日時: 2026-05-08
> 対象: `.steering/20260508-default-backend-switch/requirements.md`
> 関連 ADR: ADR-018（accepted, 2026-05-08）/ ADR-019（accepted, 2026-05-08）

## サマリー

| 項目 | 件数 |
|------|------|
| 受け入れ条件 総数 | 10 |
| 自動検証 PASS | 10 |
| 自動検証 FAIL | 0 |
| 手動確認 必要 | 0 |
| **総合判定** | **PASS** |

総合判定の根拠: 全 10 条件が `Bash` / `Grep` / 既存 CLI 経由で機械検証可能であり、すべて PASS。Phase 2-A 受入れ §6 残課題 A-1-6 / A-6-2 / A-6-3 を本 PR で解消、Phase 2-A の真のクローズに到達。

## 1. 自動検証結果

### バックエンド既定値切替

| # | 条件 | カテゴリ | 結果 | 根拠 |
|---|------|----------|------|------|
| 1 | `agent/orchestration/llm.py:321` の既定値が `"claude-code"` | CODE_EXISTS | PASS | `agent/orchestration/llm.py:321` `os.environ.get("WIKI_LLM_BACKEND", "claude-code").lower()` |
| 2 | `test_default_returns_stub` を新仕様に合わせて更新し PASS | BEHAVIOR | PASS | `tests/unit/test_llm_anthropic.py:120` `test_default_returns_claude_code`、`:131` `test_explicit_stub_returns_stub` 追加。`pytest -q tests/unit/test_llm_anthropic.py` 16 件 PASS |

### 品質ゲート

| # | 条件 | カテゴリ | 結果 | 根拠 |
|---|------|----------|------|------|
| 3 | `uv run pytest tests/` 全 PASS（202 件以上） | BEHAVIOR | PASS | **203 件 PASS**（+1: `test_explicit_stub_returns_stub`） |
| 4 | `uv run ruff check .` PASS | BEHAVIOR | PASS | `All checks passed!` |
| 5 | `uv run mypy agent` PASS | BEHAVIOR | PASS | `Success: no issues found in 29 source files` |
| 6 | `uv run agent validate --all` PASS | BEHAVIOR | PASS | `Validated 16 files / All checks PASSED` |
| 7 | `uv run agent lint --all` 違反 0 | BEHAVIOR | PASS | `Total violations: 0`（orphan/stale/low_conf/broken/index/contra すべて 0）|

### ドキュメント更新

| # | 条件 | カテゴリ | 結果 | 根拠 |
|---|------|----------|------|------|
| 8 | `CLAUDE.md` の `agent regenerate` 運用注意ブロック / 注記行が削除または empirical PASS 済の文面に更新 | CONFIG | PASS | 旧文面 `後述の運用注意あり` / `現状の LLM 統合はスタブ` の grep 0 件、新文面 L157 `本番運用ガード解除（2026-05-08）` に置換 |
| 9 | `vault/90_meta/metrics.md` に Phase 2-A 16 本（公式 11 + recipe 5）が記録 | CONFIG | PASS | 公式 source 行 11 本（cli 6 + hooks 5）、recipe 行 5 本、加えて empirical 実行記録 1 行（basic-usage 73.33s）を追記 |
| 10 | ADR-018 本文に既定値昇格の改訂履歴が追記 | CONFIG | PASS | `docs/core/decisions.md:900` `2026-05-08: ADR-018 既定値段階展開の **empirical PASS 後の昇格** を実施` |

## 2. 手動確認チェックリスト

> 本 PR スコープでは手動確認項目なし（`agent regenerate` の実走 / Slash Command 経由検証は ADR-018 側 PR で完了済）。

将来の運用課題:

- [ ] empirical 2 回目以降を `metrics.md` の empirical 実行記録テーブルに継続追記する運用を確立
- [ ] Phase 2-B `agent metrics` サブコマンド検討（自動追記化）

## 3. 総括

本 PR は ADR-018 の段階展開設計通り、empirical PASS 後の既定値昇格を実施した。

**達成事項**:
- `make_backend()` 既定値を `stub` → `claude-code` へ昇格
- 既存テスト 1 件を新仕様に書換、明示 `stub` 指定が機能することの追加テストで保護
- `CLAUDE.md` の `agent regenerate` 運用ガード注記を解除し、ADR-018/019 に基づく現行仕様注記に置換
- `vault/90_meta/metrics.md` に Phase 2-A 対象 16 本を機械的算出（`git diff a158a41..eb0bd8b --numstat`）で記録
- empirical 実行記録テーブルを新設し、basic-usage（73.33s）を初期エントリとして記録
- ADR-018 史的経緯欄に昇格履歴を追記

**Phase 2-A 受入れ残課題の解消**:
- A-1-6（`agent regenerate` 運用ガード）: 解消
- A-6-2 / A-6-3（metrics 16 本記録）: 解消

**CI / 既存環境への影響**: なし。`.github/workflows/validate.yml` は `agent regenerate` を呼ばないため、既定値切替で CI が壊れない。`make_backend()` をテストから呼ぶ箇所は 1 件のみで本 PR で更新済。

**総合判定: PASS**（2026-05-08）。Phase 2-A の真のクローズに到達。
