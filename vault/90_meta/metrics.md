# メトリクス記録 (metrics)

> Phase 2-A 以降の生成・レビュー実績を記録する。`vault/90_meta/_schemas/frontmatter.schema.json` の対象外（運用ログとして自由形式）。
> Phase 2-A の中止条件（A-7）の判定および Phase 2-B 着手判断の入力として使用する。

## 列定義

| 列 | 型 | 説明 |
|----|----|------|
| `path` | string | 記事の vault 相対パス（例: `vault/sources/official/cli/installation.md`） |
| `generated_at` | ISO 8601 datetime | 記事生成日時 |
| `reviewer` | string | レビュアー識別子（`tak` 等） |
| `review_minutes` | int | レビュー所要分（分単位） |
| `auto_fix_count` | int | エージェントが自動で修正した件数（誤字修正・lint 自動適用等） |
| `manual_fix_count` | int | 人手で修正した件数（要約書き換え・補足追加等） |
| `llm_input_tokens` | int | 入力トークン数（cache 込み、cache hit / miss 合算） |
| `llm_output_tokens` | int | 出力トークン数 |
| `cache_hit_rate` | float | prompt cache hit 率（0.0-1.0） |

## 記録フォーマット

各レビュー完了時に以下のテーブル末尾に 1 行追記する:

```markdown
| path | generated_at | reviewer | review_minutes | auto_fix_count | manual_fix_count | llm_input_tokens | llm_output_tokens | cache_hit_rate |
|------|--------------|----------|----------------|----------------|------------------|------------------|-------------------|----------------|
| vault/recipes/claude-code-setup.md | 2026-05-06T19:00:00Z | tak | 12 | 0 | 3 | 4500 | 800 | 0.65 |
```

## 集計ビュー（Phase 2-A 完了時）

Phase 2-A 完了時に以下を算出する:

- **修正率** = `sum(manual_fix_count) / count(*)`
- **平均レビュー時間** = `avg(review_minutes)`
- **LLM コスト推計** = `sum(llm_input_tokens × $cache_or_input_price + llm_output_tokens × $output_price)`（モデル単価は計算時に確定）
- **平均 cache hit 率** = `avg(cache_hit_rate)`

## A-7 中止条件

以下のいずれかに該当した場合、Phase 2-B 着手前に再計画する:

| 条件 | 閾値 |
|------|------|
| 修正率 | **> 50%** |
| LLM コスト | **想定の 2 倍超**（想定値は実 SDK 統合時に確定） |
| awesome-claude-code ライセンス問題 | 検出されたら即時停止 |

判定結果は本ファイル末尾の「Phase 2-A 中止条件チェック」セクションに記録する。

## 計測実績テーブル

### 公式 source 縮退（A-2 / 11 本、当初想定 10 本に admin-setup 追加で 11 本に拡大）

> **計測方法**（2026-05-08 機械的算出）: `manual_fix_count` は `git diff a158a41..eb0bd8b -- <path>` の touched lines = `(insertions + deletions)` を採用。Phase 2-A バルク作業時の LLM は `stub` のため `llm_*` / `cache_hit_rate` は計測対象外（`0` で記録、解釈は `N/A` 扱い）。`generated_at` は Phase 2-A 着手日 `2026-05-06`、`review_minutes` は未計測（`0` で記録）。

| path | generated_at | reviewer | review_minutes | auto_fix_count | manual_fix_count | llm_input_tokens | llm_output_tokens | cache_hit_rate |
|------|--------------|----------|----------------|----------------|------------------|------------------|-------------------|----------------|
| vault/sources/official/cli/admin-setup.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 35 | 0 | 0 | 0.0 |
| vault/sources/official/cli/basic-usage.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 62 | 0 | 0 | 0.0 |
| vault/sources/official/cli/configuration.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 45 | 0 | 0 | 0.0 |
| vault/sources/official/cli/installation.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 45 | 0 | 0 | 0.0 |
| vault/sources/official/cli/keybindings.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 48 | 0 | 0 | 0.0 |
| vault/sources/official/cli/permissions.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 54 | 0 | 0 | 0.0 |
| vault/sources/official/hooks/overview.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 49 | 0 | 0 | 0.0 |
| vault/sources/official/hooks/post-tool-use.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 40 | 0 | 0 | 0.0 |
| vault/sources/official/hooks/pre-tool-use.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 50 | 0 | 0 | 0.0 |
| vault/sources/official/hooks/stop.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 43 | 0 | 0 | 0.0 |
| vault/sources/official/hooks/user-prompt-submit.md | 2026-05-06T17:09:57+09:00 | tak | 0 | 0 | 39 | 0 | 0 | 0.0 |

### コミュニティ source 取込み（A-3 / awesome-claude-code 5 本）

> A-7 中止条件発動（CC BY-NC-ND 4.0 検出、2026-05-06）により記録対象なし。Phase 2-B B-3 で別系統に再選定後に開始。

| path | generated_at | reviewer | review_minutes | auto_fix_count | manual_fix_count | llm_input_tokens | llm_output_tokens | cache_hit_rate |
|------|--------------|----------|----------------|----------------|------------------|------------------|-------------------|----------------|

### recipe 種別生成（A-4 / 5 本）

> recipe は LLM 介在なしで人手作成（ADR-016）。`manual_fix_count` は `git diff a158a41..eb0bd8b -- <path>` の insertions（新規作成のため deletions = 0）。`llm_*` は計測対象外（`0` で記録）。

| path | generated_at | reviewer | review_minutes | auto_fix_count | manual_fix_count | llm_input_tokens | llm_output_tokens | cache_hit_rate |
|------|--------------|----------|----------------|----------------|------------------|------------------|-------------------|----------------|
| vault/recipes/claude-code-setup.md | 2026-05-08T15:20:34+09:00 | tak | 0 | 0 | 35 | 0 | 0 | 0.0 |
| vault/recipes/hooks-introduction.md | 2026-05-08T15:20:34+09:00 | tak | 0 | 0 | 35 | 0 | 0 | 0.0 |
| vault/recipes/keybindings-customization.md | 2026-05-08T15:20:34+09:00 | tak | 0 | 0 | 34 | 0 | 0 | 0.0 |
| vault/recipes/permission-control-practice.md | 2026-05-08T15:20:34+09:00 | tak | 0 | 0 | 35 | 0 | 0 | 0.0 |
| vault/recipes/post-tool-use-formatter.md | 2026-05-08T15:20:34+09:00 | tak | 0 | 0 | 34 | 0 | 0 | 0.0 |

### empirical 実行記録（claude-code バックエンド経由）

> ADR-018 empirical 検証および以降の `agent regenerate` 実走を記録。`manual_fix_count` は実 LLM 出力に対する事後人手修正の行数。`review_minutes` 未計測時は `0`。

| path | generated_at | reviewer | review_minutes | auto_fix_count | manual_fix_count | llm_input_tokens | llm_output_tokens | cache_hit_rate | 備考 |
|------|--------------|----------|----------------|----------------|------------------|------------------|-------------------|----------------|------|
| vault/sources/official/cli/basic-usage.md | 2026-05-08T15:00:00+09:00 | tak | 0 | 0 | 0 | 0 | 0 | 0.0 | ADR-018 empirical PASS（73.33s、AUTO 領域のみ更新）|

## Phase 2-A 中止条件チェック

集計結果（Phase 2-A 実装ループ完了時点）:

- 修正率: **算出対象外**（Phase 2-A 16 本は `stub` バックエンド or 手書き作成のため A-7 の `>50%` 閾値判定の前提条件を満たさない）
  - 公式 source 11 本 touched lines 合計 = 510 行、平均 46.4 行/本（縮退仕様 ADR-017 への移行作業による既存内容の置換が大半）
  - recipe 5 本 insertions 合計 = 173 行、平均 34.6 行/本（新規作成）
  - 真の修正率計測は **2026-05-08 の empirical 実行（claude-code 経由）以降**を対象とし、empirical 実行記録テーブルへの追記で判定する
- LLM コスト想定比: empirical 1 回目（73.33s / basic-usage）はトークン計測未取得（`ResultMessage.usage` が SDK で未提供）。Phase 2-B `agent metrics` で自動取得検討
- **ライセンス問題: あり**（awesome-claude-code が CC BY-NC-ND 4.0、2026-05-06 検出）

→ A-7 中止条件発動: A-3 タスクを停止、別系統への切替は Phase 2-B B-3 に持ち越し
→ A-6-2 / A-6-3 解消（2026-05-08）: 16 本の機械的算出値を上記テーブルに記録、empirical 開始日を起点に真のレビュー率計測へ移行

詳細:

- awesome-claude-code の LICENSE は `https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/2d32d46e5e946799bff436210d641eca1153ff63/LICENSE` で確認
- ND（NoDerivatives）が再構成 / 翻訳 / 要約 を許さない可能性 + NC が将来の Web 公開（広告・有料機能等）をブロックすることから、A-3 のリスト経由取込みは安全に進められない
- `vault/90_meta/sources.md` の該当エントリは `enabled: false` に設定し、コードと fetcher は Phase 2-B B-3 で別系統に再利用可能な状態で残置
- Phase 2-A の本質的価値（実 Anthropic SDK 統合 / AUTO マーカー / recipe 種別先行 / 公式 source 縮退 / metrics 計測開始）は A-3 を除いて達成

→ Phase 2-B 着手判断: A-3 停止に伴う再計画必要、ただし他の Phase 2-A 機能（A-1〜A-2 / A-4〜A-6）の検証は完了次第 GO 可能

## 注記

- 本ファイルは **手動更新運用**（Phase 2-A）。Phase 2-B 以降で `agent metrics` サブコマンドによる自動追記化を検討
- LLM コスト計算の単価は `claude-sonnet-4-6` の公式価格表に基づく（実 SDK 統合時に確定）
- prompt caching の cache_hit_rate は Anthropic SDK レスポンスの `cache_creation_input_tokens` / `cache_read_input_tokens` から算出
