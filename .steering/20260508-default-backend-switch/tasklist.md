# タスクリスト: 既定バックエンド切替と Phase 2-A クローズ

## フェーズ1: 既定値切替

- [x] `agent/orchestration/llm.py:321` の既定値を `"claude-code"` へ変更
- [x] docstring 冒頭の `WIKI_LLM_BACKEND=stub` (既定) 表記を更新
- [x] `tests/unit/test_llm_anthropic.py::test_default_returns_stub` を更新
  - [x] テスト名を `test_default_returns_claude_code` に変更
  - [x] `shutil.which` を mock し `ClaudeCodeBackend` が返ることを検証
- [x] テスト追加: `WIKI_LLM_BACKEND=stub` 明示時に `StubLLMClient` が返ることを検証（`test_explicit_stub_returns_stub`）

## フェーズ2: CLAUDE.md 運用ガード削除

- [x] L140 のコメント `# ⚠ 後述の運用注意あり` を削除（empirical 表記に置換）
- [x] L144-146 の `> ⚠ agent regenerate の運用注意` ブロックを削除（ADR-018/019 対応の現行仕様注記に置換）
- [x] L159 の `agent regenerate` 本番運用ガード行を empirical PASS 済の現状に合わせて更新

## フェーズ3: metrics.md 記録

- [x] `公式 source 縮退（A-2 / 11 本）` テーブルに 11 本記録（admin-setup 含む。当初想定 10 本に admin-setup 追加で 11 本に拡大した経緯を注記）
- [x] `recipe 種別生成（A-4 / 5 本）` テーブルに 5 本記録
- [x] 集計欄に Phase 2-A 解釈の注記追加（stub バルク作成 / 真の修正率は empirical 以降）
- [x] empirical 実行記録テーブル新設、basic-usage 1 回目（73.33s）を記録

## フェーズ4: ADR-018 改訂履歴

- [x] `docs/core/decisions.md` ADR-018 史的経緯欄に「2026-05-08 既定値昇格」を追記

## フェーズ5: 品質チェック

- [x] `uv run ruff check .` PASS
- [x] `uv run mypy agent` PASS
- [x] `uv run pytest tests/` 全 PASS（203 件）
- [x] `uv run agent validate --all` PASS（16 ファイル）
- [x] `uv run agent lint --all` 違反 0

---

## 実装完了日
2026-05-08

## 計画と実績の差分

**追加で実施したこと**:
- `metrics.md` の Phase 2-A 中止条件チェックセクションを更新（A-6-2 / A-6-3 解消の追記）
- empirical 実行記録テーブルを新設（既存 3 テーブルは Phase 2-A 内訳のため、empirical 以降の行を分離して可視性を上げる）
- 公式 source 縮退テーブルのタイトルを `10 本` → `11 本` に変更（admin-setup 追加分の経緯を注記）

**機械的算出の根拠**:
- `git diff a158a41..eb0bd8b -- <path>` の `--numstat` から `manual_fix_count = insertions + deletions` を採用
- Phase 2-A の LLM は `stub`（recipe は手書き）のため `llm_input_tokens / output_tokens / cache_hit_rate` は 0（解釈は `N/A`）
- `review_minutes` は Phase 2-A 期間中に未計測のため 0 で記録

## 学んだこと

- `make_backend()` 既定値を変更すると `tests/unit/test_llm_anthropic.py::TestMakeBackend` の 1 件のみ影響。CI（`pytest`/`mypy`/`ruff`/`agent validate`）は `agent regenerate` を呼ばないため CI 互換性は保たれた。
- ADR-018 の段階展開設計通り、empirical PASS → 既定昇格の境界が綺麗にスコープ分離できた。`StubLLMClient` を残置する方針が `WIKI_LLM_BACKEND=stub` 明示テストを温存可能にしている。
- 修正率の機械的算出は touched lines（insertions + deletions）が最も保守的な近似値だが、stub バックエンドでのバルク作成が大半を占める Phase 2-A では A-7 閾値判定の前提を満たさない。empirical 開始以降を真の計測対象とする運用へ切替えるのが妥当。
