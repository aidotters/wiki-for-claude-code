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

### 公式 source 縮退（A-2 / 10 本）

| path | generated_at | reviewer | review_minutes | auto_fix_count | manual_fix_count | llm_input_tokens | llm_output_tokens | cache_hit_rate |
|------|--------------|----------|----------------|----------------|------------------|------------------|-------------------|----------------|

### コミュニティ source 取込み（A-3 / awesome-claude-code 5 本）

| path | generated_at | reviewer | review_minutes | auto_fix_count | manual_fix_count | llm_input_tokens | llm_output_tokens | cache_hit_rate |
|------|--------------|----------|----------------|----------------|------------------|------------------|-------------------|----------------|

### recipe 種別生成（A-4 / 5 本以上）

| path | generated_at | reviewer | review_minutes | auto_fix_count | manual_fix_count | llm_input_tokens | llm_output_tokens | cache_hit_rate |
|------|--------------|----------|----------------|----------------|------------------|------------------|-------------------|----------------|

## Phase 2-A 中止条件チェック

集計結果（Phase 2-A 実装ループ完了時点）:

- 修正率: 算出未了（A-3 中止により記事数が想定の 75% に縮小、A-2 / A-4 のみ計測対象）
- LLM コスト想定比: 算出未了（実 SDK 統合の empirical 検証は API キー設定の上で別セッションで実施）
- **ライセンス問題: あり**（awesome-claude-code が CC BY-NC-ND 4.0、2026-05-06 検出）

→ A-7 中止条件発動: A-3 タスクを停止、別系統への切替は Phase 2-B B-3 に持ち越し

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
