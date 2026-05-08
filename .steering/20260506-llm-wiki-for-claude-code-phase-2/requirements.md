# 要求内容

## 概要

LLM-Wiki for Claude Code プロジェクトの **Phase 2（実 LLM 統合 + 派生ページ種別 + 公式 6 カテゴリ展開 + AUTO マーカー + `/wiki-query`）** を実装する。Phase 1 で確立した規約・agent 層・Slash Command + Skill 構造の上に、以下を順次積み上げる:

1. **Phase 1 カリーオーバー解消** — drift 記事 2 本（`cli/installation.md`, `hooks/overview.md`）の全面書き直し、既存 8 本を `status: published`, `confidence ≥ 0.7` に昇格、`agent regenerate` の実 Anthropic SDK 統合
2. **派生ページ種別の実装** — `concept` / `entity` / `synthesis` の frontmatter 規約・テンプレート・lint ルール拡充と、各種別最低 5 本の記事生成
3. **公式 6 カテゴリ展開** — `slash-commands` / `mcp` / `settings` / `sdk` の 4 カテゴリを追加し、各カテゴリ最低 5 本（既存 `cli` / `hooks` 含む計 6 カテゴリ × 5 本以上 = 合計 30 本以上）の `source` 種別記事を整備
4. **AUTO セクションマーカー** — `<!-- AUTO:START --> ... <!-- AUTO:END -->` 仕様確定 + Writer の領域分離書き換え + 全 `source` 記事への適用（ADR-006）
5. **`/wiki-query` コマンド** — クエリから関連 source / concept / entity を集約し `synthesis` 種別として保存
6. **`agent verify-links` の CI 別ジョブ統合** — 許容失敗で URL/内容 drift を週次以上の頻度で監視
7. **人手レビュー工数の実測** — `vault/90_meta/metrics.md` に `(記事数, レビュー時間, 修正件数)` を計測・記録

> **本計画のスコープ外**: Phase 3（`comparison` 自動生成、`vault/sources/community/` 配下の記事作成、GitHub Actions 週次 cron + `agent/runners/action.py`、コミュニティソース取り込み、CODEOWNERS / PR テンプレート、`cost-log.md`）。

## 背景

### Phase 1 から引き継いだ未完了項目（2026-05-06 受入れテストで判明）

- **上流ドキュメント大規模移行**（`docs.claude.com/claude-code/*` → `code.claude.com/docs/{en,ja}/*`）に伴い 2 記事が drift（`status: draft`, `stale: true`）。残 8 本も新ドキュメント基準での個別仕様精査が未完
- **`agent regenerate` の LLM スタブ**: 低品質ダミー本文で記事を上書きするため本番運用記事への実行を運用ガード中。Phase 2 の冒頭で実 Anthropic SDK へ切替えないと、コンテンツ生成の手作業が継続する
- **`agent verify-links` は手動実行のみ**: ネットワーク依存のため CI から外しているが、上流再 redirect / 内容変動の検出が遅れるリスク

### Phase 2 が解決すること

- **コンパイル型 Wiki の本来価値の発現**: `source` 単独では「公式の日本語要約 + リンク + 補足」に留まる。`concept` / `entity` / `synthesis` の派生ページが揃って初めて「1 source から複数の派生が育つ」コンパイル構造が機能する
- **公式 6 カテゴリの面的整備**: 利用者が Claude Code を使う上で必要な領域（cli / hooks / slash-commands / mcp / settings / sdk）を網羅し、Wiki としての網羅性を確保
- **自動 PR と人手編集の両立準備**: AUTO セクションマーカーにより、Phase 3 の自動 PR が人手編集を上書きするリスクを構造的に防ぐ
- **クエリベースの利用体験**: `/wiki-query` により利用者は自然言語で問い合わせ、関連ページの集約結果を得る（Karpathy 原案の `synthesis` 種別の本来用途）

### 関連 ADR

- **ADR-006**: AUTO セクションマーカー（Phase 2 で実装する旨が明記）
- **ADR-011**: ページ種別 5 種類採用（Phase 2 で `concept` / `entity` / `synthesis` を追加実装）
- **ADR-014**: Slash Command と Skill の分離（Phase 2 で `.claude/commands/wiki-query.md` を追加）
- **ADR-008**: 情報源ホワイトリスト（Phase 2 で 4 カテゴリ追加。ホワイトリスト本体は Phase 1 で確定済みのまま運用）
- **ADR-007 / ADR-010**: ローカル Claude Code 実行 + Python 3.12+（Phase 2 でも継続）
- **新規 ADR-015 候補**: AUTO マーカー構文規約（`vault/90_meta/auto-marker-spec.md` の確定と同時に起票）
- **新規 ADR-016 候補**: 派生種別（concept/entity/synthesis）の引用必須・テンプレート規約

## 実装対象の機能

### 1. drift 記事 2 本の全面書き直し（カリーオーバー解消）

- **対象**:
  - `vault/sources/official/cli/installation.md`（推奨インストール手段が `npm install -g` から `curl install.sh` ベースに変更）
  - `vault/sources/official/hooks/overview.md`（hook イベント数が 5 種 → ~20 種、handler type が拡張）
- 新ドキュメント基準（`code.claude.com/docs/ja/*`）で要約・補足解説を全面書き直し
- 書き直し後は `status: reviewed → published`、`confidence ≥ 0.7`、`stale: false` を満たす
- drift 内容の frontmatter コメント（Phase 1 で記録）は削除

### 2. 既存 8 記事の `published` 昇格（カリーオーバー解消）

- **対象**: `vault/sources/official/{hooks,cli}/` 配下の `status: reviewed`, `confidence: 0.6〜0.7` の 8 本
- 新ドキュメント基準で個別キー仕様（hooks event 一覧、CLI flag、permission mode 等）を精査
- 必要に応じて補足解説を加筆し、`confidence ≥ 0.7`、`status: published` に昇格
- 変更履歴を `vault/log.md` に追記

### 3. 実 Anthropic SDK 統合（カリーオーバー解消）

- **対象**: `agent/orchestration/llm.py`（現状スタブ）
- Anthropic SDK（`anthropic` Python パッケージ）を導入
- モデルは Claude 4.x 系（**Sonnet 4.6 を既定** とし、`agent regenerate --model` で切替可能）
- `prompt caching`（system プロンプト + 規約 references を `cache_control: ephemeral` で共通化）を実装
- API キーは `.env` の `ANTHROPIC_API_KEY` から読み込む
- 失敗時は記事を更新せず、終了コード 3（LLM エラー）を返す
- `agent regenerate` が本番運用記事に対しても安全に再生成できる状態（`CLAUDE.md` の運用ガード文を Phase 2 完了時点で削除）

### 4. 派生ページ種別の実装（concept / entity / synthesis）

- **frontmatter 規約拡充**: `vault/90_meta/frontmatter-spec.md` に 3 種別の必須キーを追加
  - `concept`: 共通必須 + `tags`（必須複数）+ `sources`（必須 1 件以上の wikilink）
  - `entity`: 共通必須 + `entity_kind`（enum: tool / command / person / model）+ `sources`（必須 1 件以上）
  - `synthesis`: 共通必須 + `query`（必須）+ `query_executed_at`（必須）+ `sources`（必須 1 件以上）
- **JSON Schema 拡充**: `vault/90_meta/_schemas/frontmatter.schema.json` に `oneOf` で 3 種別追加
- **テンプレート追加**: `.claude/skills/llm-wiki-for-claude-code/references/page-templates.md` に 3 種別の実体テンプレートを追加
- **記事配置**: `vault/concepts/`, `vault/entities/`, `vault/syntheses/` に各種別最低 5 本（合計 15 本以上）
- **lint ルール**: 派生種別の引用必須（`sources` 空チェック）、引用先実在チェックを `citation_validator` で本実装
- **comparison 種別はスキーマのみ整備**: テンプレート + JSON Schema は追加するが記事は Phase 3 で自動生成

### 5. 公式 6 カテゴリ展開（slash-commands / mcp / settings / sdk 追加）

- **対象**: `vault/sources/official/{slash-commands,mcp,settings,sdk}/` の 4 カテゴリを新規整備
- 各カテゴリ最低 5 本の `source` 種別記事を作成
- 既存 `cli` / `hooks` 各 5 本以上と合わせ、6 カテゴリ × 5 本以上 = **30 本以上**
- 全記事は Phase 1 規約（3 部構成、共通必須 frontmatter、`source_url` 200 確認、連続 100 文字一致なし、`status: published`, `confidence ≥ 0.7`）を満たす
- `agent ingest` または `agent regenerate`（実 LLM 経由）で生成し、人手レビューで `published` 化

### 6. AUTO セクションマーカーの実装

- **仕様確定**: `vault/90_meta/auto-marker-spec.md` を新規作成
  - 構文: `<!-- AUTO:START -->` 〜 `<!-- AUTO:END -->`、ネスト不可、`source` 種別の「## 補足解説 (日本語)」内のみ配置可
  - 1 記事あたり最大 1 領域（Phase 2）
  - 自動領域: Writer がバイト単位で書き換え可
  - 人手領域: Writer はバイト一致を保持、書き換え禁止
- **frontmatter `auto_section_managed: true`** の意味を確定（true 時のみ AUTO 領域を Writer が更新）
- **Writer 拡張**: `agent/writers/markdown_writer.py` に AUTO 領域抽出 + 書き換えロジック追加
- **既存記事への適用**: `source` 種別記事 30 本以上の「## 補足解説 (日本語)」配下に AUTO 領域を導入、`auto_section_managed: true` に切替
- **検証**: AUTO 領域外を意図的に変更したテスト記事に対し、`agent regenerate` 後に外側のバイト一致が保持されることを確認

### 7. `/wiki-query` コマンドの実装

- **Slash Command**: `.claude/commands/wiki-query.md` を追加
- **agent サブコマンド**: `agent query --question "..."`
  - 入力: 自然言語クエリ
  - 処理: Vault 配下の関連ページ（`source` / `concept` / `entity`）を frontmatter `tags` + 全文で抽出 → LLM で集約
  - 出力: `vault/syntheses/<slug>.md` を `type: synthesis` で生成（`query`, `query_executed_at`, `sources` を frontmatter に記録）
- **冪等性**: 同一クエリを連続 2 回実行した場合、2 回目は既存ファイルを上書きせず「既存 synthesis があります」を表示（または `--force` で上書き）

### 8. `agent verify-links` の CI 別ジョブ統合

- `.github/workflows/verify-links.yml` を新規作成（既存 `validate.yml` とは分離）
- スケジュール: 週 1 回（cron `0 0 * * 1` 月曜 UTC 0 時）+ 手動実行
- `continue-on-error: true`（許容失敗）で URL drift / 内容 drift を Issue に集約
- 失敗時は GitHub Issue を起票（タイトル: `[verify-links] drift detected: YYYY-MM-DD`）
- ネットワーク依存のため `validate.yml` 本体には組み込まない方針を維持

### 9. 人手レビュー工数の実測（`metrics.md`）

- `vault/90_meta/metrics.md` を新規作成
- Phase 2 で生成・レビューした全記事について以下を記録:
  - 記事パス、生成日時、レビュー時間（分）、レビュアー、自動修正件数、人手修正件数
- 集計値（記事 1 本あたり平均レビュー時間、修正率）を Phase 2 完了時点で算出し PRD KPI と照合

## 受け入れ条件

### Phase 1 カリーオーバー解消

#### drift 記事 2 本の全面書き直し（機能 1）

- [ ] `vault/sources/official/cli/installation.md` が新ドキュメント（`code.claude.com/docs/ja/setup`）基準で書き直され、`status: published`, `confidence ≥ 0.7`, `stale: false` を満たす
- [ ] `vault/sources/official/hooks/overview.md` が新ドキュメント基準で書き直され、hook イベント現行一覧が反映され、`status: published`, `confidence ≥ 0.7`, `stale: false` を満たす
- [ ] 両記事から drift コメント（Phase 1 で記録）が削除されている
- [ ] 両記事が `agent verify-links` で `source_url` 200 + 連続 100 文字一致なしを PASS

#### 既存 8 本の `published` 昇格（機能 2）

- [ ] `vault/sources/official/{hooks,cli}/` 配下の既存 8 本（`status: reviewed`）が全て `status: published`, `confidence ≥ 0.7` に昇格
- [ ] 各記事の補足解説に新ドキュメント基準で精査した内容が反映されている
- [ ] 全 10 本（drift 2 本 + 既存 8 本）の `agent validate --target` が PASS
- [ ] `vault/log.md` に各昇格の操作履歴が追記されている

#### 実 Anthropic SDK 統合（機能 3）

- [ ] `agent/orchestration/llm.py` がスタブから Anthropic SDK 呼び出しに置き換わっている
- [ ] `pyproject.toml` の `dependencies` に `anthropic>=0.40` が追加されている
- [ ] `ANTHROPIC_API_KEY` が未設定の場合、`agent regenerate` 実行時にエラー終了コード 3 と分かりやすいメッセージを返す
- [ ] prompt caching が有効化され、system プロンプトと規約 references が `cache_control: ephemeral` で送信される
- [ ] テスト用モック（`tests/integration/llm_mock.py` 等）と実 SDK 呼び出しを切替えるフラグ（環境変数 `WIKI_LLM_BACKEND=stub|anthropic`）が動作する
- [ ] 実 SDK 経由で `agent regenerate --target <path>` を実行した結果、3 部構成・連続 100 文字一致なし・冪等性（連続 2 回で意味のある差分なし）が満たされる
- [ ] `CLAUDE.md` の `agent regenerate` 運用ガード文（「本番運用記事に対して呼ばない」）が削除されている

### 派生ページ種別の実装

#### frontmatter 規約・JSON Schema 拡充（機能 4）

- [ ] `vault/90_meta/frontmatter-spec.md` に `concept` / `entity` / `synthesis` / `comparison` の 4 種別の必須キーが追記されている
- [ ] `vault/90_meta/_schemas/frontmatter.schema.json` に上記 4 種別の `oneOf` 分岐が追加されている
- [ ] `agent/validators/frontmatter_validator.py` が 5 種別全てを `type` 別に検証し、各種別の必須キー欠損を検出する
- [ ] `entity_kind`（enum: `tool` / `command` / `person` / `model`）が enum 外の値の場合に検証エラーを返す
- [ ] `synthesis` の `query` または `query_executed_at` 欠損を検証エラーとして検出する

#### テンプレート追加（機能 4）

- [ ] `.claude/skills/llm-wiki-for-claude-code/references/page-templates.md` に `concept` / `entity` / `synthesis` / `comparison` の実体テンプレートが含まれる
- [ ] 各テンプレートに「引用必須（`sources` 配列、最低 1 件）」のガイダンスが含まれる

#### 派生記事配置（機能 4）

- [ ] `vault/concepts/` 配下に `type: concept` の記事が **5 本以上** 存在し、全て `agent validate` で PASS
- [ ] `vault/entities/` 配下に `type: entity` の記事が **5 本以上** 存在し、全て `agent validate` で PASS
- [ ] `vault/syntheses/` 配下に `type: synthesis` の記事が **5 本以上** 存在（`/wiki-query` 実行結果由来でも可）し、全て `agent validate` で PASS
- [ ] 各記事の `sources` frontmatter キーに最低 1 件の wikilink が存在し、引用先が実在する（`citation_validator` で PASS）
- [ ] 派生種別 15 本以上が `confidence ≥ 0.7`, `status: published` を満たす

### 公式 6 カテゴリ展開（機能 5）

- [ ] `vault/sources/official/slash-commands/` 配下に `type: source` の記事が **5 本以上** 存在
- [ ] `vault/sources/official/mcp/` 配下に `type: source` の記事が **5 本以上** 存在
- [ ] `vault/sources/official/settings/` 配下に `type: source` の記事が **5 本以上** 存在
- [ ] `vault/sources/official/sdk/` 配下に `type: source` の記事が **5 本以上** 存在
- [ ] 既存 `vault/sources/official/{cli,hooks}/` 配下に各 5 本以上が存在（`cli` 6 本 / `hooks` 5 本の現状を維持）
- [ ] 6 カテゴリ合計で **30 本以上** の `source` 種別記事が存在し、全て `status: published`, `confidence ≥ 0.7`, `stale: false`
- [ ] 全記事が `agent verify-links` で `source_url` 200 確認 + 連続 100 文字一致なしを PASS
- [ ] 全記事に共通必須 + source 種別必須 frontmatter キーが揃っている

### AUTO セクションマーカー（機能 6）

- [ ] `vault/90_meta/auto-marker-spec.md` が新規作成され、構文・配置位置・適用範囲が記載されている
- [ ] `docs/core/decisions.md` に AUTO マーカー構文確定の ADR が追加されている（ADR-015 候補）
- [ ] `agent/writers/markdown_writer.py` が AUTO 領域抽出 + 書き換えロジックを実装し、領域外バイト一致を保持する
- [ ] AUTO 領域外を意図的に編集したテスト記事に対し、`agent regenerate` 後も領域外がバイト一致で保持されることをテストで確認
- [ ] `source` 種別 30 本以上の「## 補足解説 (日本語)」配下に AUTO 領域が導入され、`auto_section_managed: true` に切替えられている
- [ ] AUTO 領域がネストしている、または `source` 種別以外で使用されているケースを `markdown_rules_validator` がエラー検出する

### `/wiki-query` コマンド（機能 7）

- [ ] `.claude/commands/wiki-query.md` が存在し、`agent query --question "..."` を呼び出す指示が記載されている
- [ ] `agent query --question "..."` が動作し、`vault/syntheses/<slug>.md` を `type: synthesis` で生成する
- [ ] 生成された `synthesis` ページに `query`, `query_executed_at`, `sources`（参照した source / concept / entity の wikilink）が frontmatter に記録される
- [ ] 同一クエリを連続 2 回実行した場合、2 回目は既存ファイルを上書きせず「既存 synthesis があります（`--force` で上書き）」を表示
- [ ] `--force` フラグで上書きが可能
- [ ] LLM エラー時は終了コード 3 を返し、`vault/syntheses/` を更新しない

### `agent verify-links` CI 統合（機能 8）

- [ ] `.github/workflows/verify-links.yml` が新規作成されている
- [ ] スケジュール: 週 1 回（月曜 UTC 0 時）+ `workflow_dispatch` での手動実行が可能
- [ ] `continue-on-error: true` で許容失敗化されている
- [ ] 失敗時に GitHub Issue が自動起票される（タイトルプレフィックス `[verify-links]`）
- [ ] `validate.yml` 本体には `agent verify-links` が含まれていない（ネットワーク依存のため分離）

### 人手レビュー工数の実測（機能 9）

- [ ] `vault/90_meta/metrics.md` が新規作成され、Phase 2 で生成・レビューした全記事の計測値が記録されている
- [ ] 記録項目: 記事パス、生成日時、レビュー時間（分）、レビュアー、自動修正件数、人手修正件数
- [ ] Phase 2 完了時点で集計値（記事 1 本あたり平均レビュー時間、修正率）が算出されている
- [ ] PRD の KPI（修正率 30% 以下、Phase 3 目標）への到達見込みが評価されている

### CI 拡張

- [ ] `.github/workflows/validate.yml` で派生種別を含む `agent validate --all` が PASS
- [ ] AUTO 領域保持のテスト（unit + integration）が CI で実行される
- [ ] `verify-links.yml` が cron で 1 回以上実行され、Issue 起票挙動が確認される

## 成功指標

- **drift 記事 2 本** が `published` 化、**既存 8 本 + 新規 4 カテゴリ × 5 本以上 = 計 30 本以上** の `source` 種別記事が `status: published`, `confidence ≥ 0.7`
- **派生種別** `concept` / `entity` / `synthesis` の各最低 5 本（合計 15 本以上）が `published` 化
- **実 LLM 統合**: `agent regenerate` の本番運用ガード解除、prompt caching によりトークンコストが連続 2 回目で 50% 以上削減（実測）
- **AUTO マーカー**: 30 本以上の `source` 記事に適用、領域外バイト一致保持テスト 100% PASS
- **`/wiki-query`**: Claude Code から起動可能、`vault/syntheses/` に最低 5 本の query 結果が保存される
- **`agent verify-links`**: CI 別ジョブで週次実行され、URL/内容 drift を Issue として可視化
- **人手レビュー工数**: 記事 1 本あたり平均レビュー時間と自動 / 人手修正件数比が `metrics.md` に記録される
- 関係する PRD 機能（Phase 1 の機能 1〜9 + Phase 2 で追加される機能）の受け入れ条件を全て満たす
- agent 層のテスト件数が **150 件以上** に拡大し、全 PASS

## スコープ外

以下はこのフェーズでは実装しません:

- **`comparison` 自動生成** → Phase 3（Phase 2 ではスキーマ + テンプレートのみ整備）
- **`vault/sources/community/` 配下の記事作成** → Phase 3
- **GitHub Actions 週次 cron** + `agent/runners/action.py` の本実装 → Phase 3
- **コミュニティソース取り込み**（Anthropic ブログ RSS, GitHub Releases, awesome-claude-code 等） → Phase 3
- **CODEOWNERS / PR テンプレート整備** → Phase 3
- **API コスト・運用ログ**（`cost-log.md`） → Phase 3（Phase 2 では `metrics.md` のみ）
- **Anthropic Routines / Schedule への移行** → Phase 3 安定後に再検討
- **Web 公開**（GitHub Pages 等） → 将来別スコープ
- **多言語対応**（日本語のみ） → 永続的にスコープ外
- **セマンティック検索層**（qmd / MCP server） → Phase 3 以降（200 ページ超で検討）

## 前提・依存

- Phase 1 で確立した規約 5 本（`vault/90_meta/{frontmatter-spec, markdown-rules, sources, license-notes, lint-rules}.md`）と JSON Schema を継承し拡張する
- Phase 1 の agent 層（fetchers / writers / validators / orchestration / runners）を継承・拡張する
- **Anthropic API キー** の運用準備（個人キー or 組織キー、月次予算上限の合意、`.env` への配置）
- **`code.claude.com/docs/ja/*`** の URL 構造維持（再 redirect 発生時は再対応）
- Python 3.12+ / uv / pytest / ruff / mypy strict（ADR-010 を継続）

## 主要リスクと対策

| リスク | 影響度 | 対策方針 |
|-------|-------|---------|
| Anthropic API コスト超過 | 中 | prompt caching 必須化、差分検知（content_hash 一致時はスキップ）、月次予算上限を `metrics.md` で監視。Phase 3 で `cost-log.md` 本格運用 |
| LLM ハルシネーション混入 | 高 | `confidence` 必須化継続、引用必須（`sources` 全主張に紐付け）、`/wiki-lint` の矛盾検出強化、人手レビューゲート維持 |
| AUTO マーカーで自動領域と人手領域の境界が曖昧化 | 中 | Phase 2 着手前に `auto-marker-spec.md` + ADR 化、Writer 実装で領域外バイト一致をテストで担保 |
| 公式ドキュメントの再 redirect / 内容大変動 | 高 | `agent verify-links` を CI 別ジョブで週次監視、drift 検出時は Issue 自動起票 |
| ページ種別拡張で既存 source 規約と競合 | 中 | `frontmatter.schema.json` の `oneOf` 分岐で `type` 別に検証経路を分離、`type` 別 validator マトリクスを明確化 |
| 派生種別記事のハルシネーション率上昇（複数 source 横断のため） | 高 | `concept` / `entity` は最低 2 件の `sources` 引用必須、`citation_validator` で引用先実在を強制 |
| 30 本以上の記事生成で人手レビュー工数が肥大化 | 中 | `metrics.md` で実測、PRD KPI（修正率 30% 以下）への到達見込みを Phase 2 中盤で評価し計画調整 |

## 参照ドキュメント

- `.steering/20260506-llm-wiki-for-claude-code-phase-2/plan.md` — Phase 2 起票（本計画の起点）
- `.steering/20260505-llm-wiki-for-claude-code/acceptance-test-report.md` — Phase 1 受け入れテストレポート（PASS / 2026-05-06）
- `.steering/20260505-llm-wiki-for-claude-code/requirements.md` — Phase 1 受け入れ条件（line 192 = Phase 2 送り項目）
- `docs/ideas/20260505-llm-wiki-for-claude-code.md` — 元アイデアファイル（ステータス: verified / 2026-05-06）
- `docs/core/product-requirements.md` — PRD（Phase 2 の機能 1〜9 が本計画の対象）
- `docs/core/architecture.md` — アーキテクチャ設計書（環境非依存ロジック + 薄いランナー方針を継続）
- `docs/core/functional-design.md` — 機能設計書（Article エンティティ + 派生種別を Phase 2 で拡張）
- `docs/core/decisions.md` — ADR（特に ADR-006 / ADR-011 / ADR-014 が Phase 2 の前提）
- `CLAUDE.md` — Phase 1 ステータス + Phase 2 への遷移情報
