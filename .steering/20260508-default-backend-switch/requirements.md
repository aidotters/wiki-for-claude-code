# 要求内容: 既定バックエンド切替と Phase 2-A クローズ

> 起点: `.steering/20260508-claude-code-llm-backend/acceptance-test-report.md §4`「次のアクション > empirical PASS 後の後続 PR」
> 関連 ADR: ADR-018（accepted, 2026-05-08）/ ADR-019（accepted, 2026-05-08）
> 前提: empirical 検証 PASS（73.33s で `ClaudeCodeBackend.invoke` 実走確認、2026-05-08）

## 概要

ADR-018 で段階展開設計とした既定バックエンドを `stub` から `claude-code` に昇格させ、Phase 2-A 受入れの残課題（A-1-6 / A-6-2 / A-6-3）をクローズする。

## 背景

- ADR-018 で `WIKI_LLM_BACKEND` 既定値の切替を **empirical PASS 後の別 PR** スコープと明記
- 2026-05-08 に empirical PASS（CLI 経由 73.33s 実走、AUTO 領域のみ更新確認）
- Phase 2-A の `acceptance-test-report.md §6` 残課題 A-1-6（`agent regenerate` 運用ガード注記）/ A-6-2 / A-6-3（metrics 記録）が解消可能なフェーズに到達
- ADR-018 は既に `accepted` に昇格済（要件書段階で確認）。追加で `Status` の文面修正は不要

## 実装対象

### 1. `make_backend()` 既定値切替

- `agent/orchestration/llm.py:321` の `os.environ.get("WIKI_LLM_BACKEND", "stub")` を `"claude-code"` に変更
- 既存テスト `tests/unit/test_llm_anthropic.py::test_default_returns_stub` を `claude-code` 既定前提に書換え（`shutil.which` mock 経由で `ClaudeCodeBackend` が返ることを検証）
- docstring の冒頭の既定値説明を更新

### 2. `CLAUDE.md` 運用ガード削除

- L140 末尾コメント `# ⚠ 後述の運用注意あり` を削除
- L144-146 の `> ⚠ agent regenerate の運用注意` ブロックを削除
- L159 の `**\`agent regenerate\` 本番運用ガード**` 行を、empirical PASS 済の現状に合わせて更新（または削除）

### 3. `vault/90_meta/metrics.md` への 16 本記録

> Phase 2-A バルク作成時の LLM は `stub`（または recipe は手書き）であり、トークン値・cache_hit_rate は計測対象外。`manual_fix_count` は `git diff HEAD~1 -- <path>` の touched lines を機械的に算出する。

- `公式 source 縮退（A-2 / 10 本）` テーブルに 11 本（cli 6 + hooks 5）を追記
- `recipe 種別生成（A-4 / 5 本以上）` テーブルに 5 本を追記
- 集計コメントを末尾に追記: 修正率の解釈は "stub バックエンドでのバルク作成 + 人手レビュー" のため A-7 の `>50%` 閾値判定からは除外、empirical 開始（2026-05-08 / `claude-code`）以降の計測が真のレビュー率となる旨を注記

### 4. ADR-018 既定値段階展開の状態同期

- ADR-018 本文中の「既定値段階展開」記述に「2026-05-08: 既定値 `claude-code` に昇格」の改訂履歴行を追加（または史的経緯セクションに追記）

## 受け入れ条件

- [ ] `agent/orchestration/llm.py:321` の既定値が `"claude-code"` になっている
- [ ] `tests/unit/test_llm_anthropic.py::test_default_returns_stub` が新仕様（`claude-code` 既定）に合わせて更新され、PASS する
- [ ] `uv run pytest tests/` 全 PASS（202 件以上）
- [ ] `uv run ruff check .` PASS
- [ ] `uv run mypy agent` PASS
- [ ] `uv run agent validate --all` PASS
- [ ] `uv run agent lint --all` 違反 0
- [ ] `CLAUDE.md` の `agent regenerate` 運用注意ブロック / 注記行が削除または empirical PASS 済の文面に更新されている
- [ ] `vault/90_meta/metrics.md` に Phase 2-A 対象 16 本（公式 11 + recipe 5）が記録されている
- [ ] ADR-018 本文に既定値昇格の改訂履歴が追記されている

## 成功指標

- Phase 2-A 受入れ §6 残課題 A-1-6 / A-6-2 / A-6-3 が解消
- `WIKI_LLM_BACKEND` 未設定で `agent regenerate` を呼ぶと `ClaudeCodeBackend` 経由で実 LLM 呼出しが行われる（CI 経路は本変更で影響なし、§次節リスク参照）

## CI / 既存環境への影響

- `.github/workflows/validate.yml` は `pytest` / `mypy` / `ruff` / `agent validate` のみ実行し、`agent regenerate` を呼ばない → 既定切替で CI が壊れない
- `make_backend()` をテストから呼んでいる箇所は `tests/unit/test_llm_anthropic.py::TestMakeBackend` 内 1 件のみ（既定値依存）。本要件 §1 で更新

## スコープ外

- `agent metrics` サブコマンドによる metrics 自動追記（Phase 2-B 検討事項）
- AUTO マーカーの cache_hit_rate 実計測（Phase 2-B 検討事項）
- `AnthropicBackend` の廃止 / 既定降格（CI / API 利用者向けに残置）

## 参照

- `.steering/20260508-claude-code-llm-backend/acceptance-test-report.md` §4
- `agent/orchestration/llm.py:319-331` `make_backend()` 本体
- `CLAUDE.md` L140 / L144-146 / L159
- `vault/90_meta/metrics.md` 計測実績テーブル
- `docs/core/decisions.md` ADR-018
