> **ステータス: 計画段階**
> このドキュメントは `docs/ideas/20260505-llm-wiki-for-claude-code.md` から生成されました。
> 実装後は `/update-docs` で実態に同期してください。

# プロダクト要求定義書 (Product Requirements Document)

## プロダクト概要

### 名称
**LLM-Wiki for Claude Code** — 人間と LLM が共同で読み書きする日本語 Claude Code Wiki

### プロダクトコンセプト
- **ドメイン特化コンパイル型 Wiki**: Karpathy LLM-Wiki gist のページ種別5種類（source / concept / entity / comparison / synthesis）と Rezvani Medium 記事の Claude Code Skill 構造を採用し、Claude Code ドメインに特化させた折衷案（詳細は [`decisions.md` ADR-001](./decisions.md)）
- **二系統コンテンツ × ページ5種別**: 公式ドキュメント / コミュニティ知見の2系統を `source` 種別として取込み、複数 source 横断の `concept` / `entity` / `comparison` / `synthesis` を派生させる
- **要約 + リンク + 補足**: `source` 種別のみ「要約 + 公式リンク + 日本語補足」3部構成を強制（Anthropic Usage Policy / 著作権リスク回避のため）
- **人間 + LLM 共同編集**: LLM エージェントが下書きを生成し、人間レビューを経てマージ
- **Vault = Repo**: Obsidian Vault と Git リポジトリを同一ディレクトリに統合し、同期問題を排除
- **Claude Code Slash Command + Skill 構造**: 操作の入り口を `.claude/commands/` のスラッシュコマンド `/wiki-ingest` `/wiki-regenerate` `/wiki-lint` で統一し、規約・テンプレート・hook は `.claude/skills/llm-wiki-for-claude-code/` の Skill で context-aware に提供（ADR-012 / ADR-014）
- **常に最新**: 週次自動更新で Claude Code のバージョン揮発性に追従

### プロダクトビジョン
Claude Code を使う日本語話者が、機能追加・変更が早い Claude Code エコシステムの最新情報に、英語コミュニティと同等のスピードでアクセスできる場を提供する。さらに、構造化された Markdown は将来的に LLM のコンテキストへ直接投入可能な素材としても再利用でき、「人間が読む Wiki」と「LLM が読む Wiki」を1つの基盤で兼ねる。

### 目的
- Claude Code の使い方・設定・周辺ツール（hooks, MCP, slash-commands, settings, SDK 等）を日本語で継続的に参照できる Wiki を構築する
- LLM エージェントによる週次自動更新で「常に最新」を担保する（人間レビュー必須）
- 著作権・利用規約リスクを最小化しつつ、独自価値（日本語解説）を付加する
- 将来の LLM 投入用 RAG 素材としても再利用可能な構造化された Markdown を蓄積する

## ターゲットユーザー

### プライマリーペルソナ: 日本語話者の Claude Code 開発者（30-40代、ソフトウェアエンジニア）

#### 基本属性
- 日本語話者で、英語の技術ドキュメントを読む際にコストを感じる
- Claude Code を業務または個人プロジェクトで日常的に利用
- Obsidian / Markdown ベースのナレッジベース運用に慣れている、または学習意欲がある
- GitHub での PR レビュー文化に習熟

#### 技術スタック（ユーザー側）
- ターミナル + Claude Code（CLI）
- Git / GitHub
- Obsidian（ローカル閲覧）または Web ブラウザ（将来公開時）
- VS Code / JetBrains 等の IDE

#### 現在の課題
- Claude Code の機能追加が早く、公式ドキュメントの全体像を追えない
- Reddit や GitHub Discussions の英語コミュニティ知見が日本語に届くまで遅い、または届かない
- 既存の日本語ブログ記事は単発で、半年経つと陳腐化している
- LLM に「最新の hooks 仕様は？」と聞いても、信頼できる構造化された一次資料に近いソースが少ない

#### 期待する解決策
- Claude Code の最新機能・設定が日本語で要約され、公式リンクと補足解説が常に更新されている Wiki
- 英語コミュニティの実践ノウハウが日本語で読める
- ローカル（Obsidian）でも参照でき、将来 Web 公開もされる

#### 1日の典型的なワークフロー
1. 朝、Claude Code をアップデートして新機能の有無を確認
2. 不明点があれば本 Wiki を参照（公式リンクへ即遷移可能）
3. 業務で Claude Code を使い、ハマりどころに遭遇 → Wiki のトラブルシュート記事を確認
4. 自分が解決した知見があれば、Wiki に PR を提出（Phase 2 以降）

## 成功指標 (KPIs)

### プライマリーKPI

| 指標 | 目標 | 測定方法 |
|------|------|---------|
| Phase 1 完了時の `source` 種別記事数 | 10本（hooks + cli カテゴリ） | `vault/sources/official/{hooks,cli}` 配下の `status: published` 記事数 |
| Phase 1 全記事の信頼度 | 全 `source` 記事で `confidence ≥ 0.7` | `agent lint --all` の出力 |
| Phase 3 自動 PR の人手修正率 | 30% 以下 | 自動 PR の追加 commit / 総 commit の割合（4週間平均） |
| Phase 3 月次運用継続期間 | 3ヶ月連続成功 | `.github/workflows/weekly-update.yml` の連続成功回数 |

### セカンダリーKPI

| 指標 | 目標 | 測定方法 |
|------|------|---------|
| 公式 全6カテゴリのカバレッジ | 各カテゴリ最低3 `source` 記事（Phase 2 終了時） | `vault/sources/official/*` 各サブディレクトリの記事数 |
| 派生ページ充実度 | `concept` 5本以上 + `entity` 5本以上（Phase 2 終了時） | `vault/concepts/`, `vault/entities/` の記事数 |
| 月額 API コスト | 見積範囲内（具体額は Phase 3 で確定） | `vault/90_meta/cost-log.md` 実測値 |
| `claude_code_version` 更新追従 | 全 `source` 記事の80%以上が直近2マイナーバージョン以内 | frontmatter の `claude_code_version` 集計 |
| 人手レビュー工数 | 1記事あたり [Phase 2 で実測値を基準化] | `vault/90_meta/metrics.md` の実測値 |

## 機能要件

### P0（必須・MVP / Phase 1）

#### 機能1: Vault ディレクトリ構造の確立

**ユーザーストーリー**:
Wiki 編集者として、目的の記事カテゴリへ素早くたどり着くために、明示的に分類されたディレクトリ構造が欲しい。

**受け入れ条件**:
- [ ] `vault/sources/`, `vault/concepts/`, `vault/entities/`, `vault/comparisons/`, `vault/syntheses/`, `vault/30_drafts/`, `vault/90_meta/` が存在する
- [ ] `vault/index.md`, `vault/log.md`, `vault/overview.md` の雛形が存在する
- [ ] `vault/sources/official/` 配下に `cli/`, `hooks/`, `slash-commands/`, `mcp/`, `settings/`, `sdk/` サブディレクトリが存在する
- [ ] `vault/sources/community/` 配下に `tips/`, `workflows/`, `integrations/`, `troubleshooting/` サブディレクトリが存在する
- [ ] Obsidian Vault として認識される（`.obsidian/` の最小設定が含まれる）

**検証方法**:
| 検証項目 | テストデータ | 合格基準 |
|---------|------------|---------|
| ディレクトリ存在チェック | 上記全ディレクトリ | 全て存在 |
| Obsidian で Vault を開く | プロジェクトルート | エラーなく開く |

**優先度**: P0

#### 機能2: frontmatter 規約の確立

**ユーザーストーリー**:
LLM エージェントとして、記事の出典・鮮度・対象バージョンを機械的に判定できるよう、必須キーが定義された frontmatter 規約が欲しい。

**受け入れ条件**:
- [ ] `vault/90_meta/frontmatter-spec.md` に以下が記載:
  - 共通必須キー: `title`, `type`, `confidence`, `sources`, `last_updated`, `stale`, `tags`
  - `type=source` 追加必須キー: `source_url`, `fetched_at`, `source_version`, `claude_code_version`
  - 運用メタ: `reviewer`, `human_edited`, `status`, `auto_section_managed`
- [ ] `vault/90_meta/_schemas/frontmatter.schema.json` に `type` 別 JSON Schema が配置されている
- [ ] `status` の遷移規則（draft → reviewed → published）が定義されている
- [ ] frontmatter 検証スクリプトが存在し、`type` 別の規約違反を検出できる

**検証方法**:
| 検証項目 | テストデータ | 合格基準 |
|---------|------------|---------|
| 規約準拠記事の検証 | Phase 1 で生成した10本 | 全件 PASS |
| 規約違反記事の検証 | わざと欠損させた記事 | エラー検出 |

**優先度**: P0

#### 機能3: 公式コンテンツの3部構成記事生成

**ユーザーストーリー**:
日本語話者の Claude Code 開発者として、公式機能の核心を日本語で素早く把握し、必要なら一次資料へすぐ遷移できるよう、要約 + 公式リンク + 補足解説の3部構成記事が欲しい。

**受け入れ条件**:
- [ ] `vault/sources/official/hooks/` と `vault/sources/official/cli/` に合計10本の `type: source` 記事が存在
- [ ] 各記事が「## 概要 (要約)」「## 公式ドキュメント」「## 補足解説 (日本語)」の3セクションを持つ
- [ ] 「## 公式ドキュメント」に最終確認日と対象バージョンが明記されている
- [ ] 全文転載が含まれていない（要約のみ、連続100文字一致なし）
- [ ] 全記事の `confidence ≥ 0.7`

**検証方法**:
| 検証項目 | テストデータ | 合格基準 |
|---------|------------|---------|
| 構造チェック | Phase 1 記事10本 | 3セクション全て存在 |
| 公式リンク到達確認 | 各記事の `source_url` | HTTP 200 |
| 全文転載検出 | 公式ページとの類似度比較 | 連続100文字以上の一致なし |

**優先度**: P0

#### 機能4: 情報源ホワイトリスト管理

**ユーザーストーリー**:
プロジェクト管理者として、利用規約違反やレート制限のリスクを抑えるために、利用可能な情報源を明示的にホワイトリスト化したい。

**受け入れ条件**:
- [ ] `vault/90_meta/sources.md` に使用可ソースのリストが存在
- [ ] 各ソースに対し、利用規約・API 制限・取得方式（RSS / 公式 API / スクレイプ可否）が記載
- [ ] `vault/90_meta/license-notes.md` に Anthropic Usage Policy / docs.claude.com 利用規約の整理が記載
- [ ] エージェントはホワイトリスト外のソースから情報取得しない

**検証方法**:
| 検証項目 | テストデータ | 合格基準 |
|---------|------------|---------|
| ソースリスト網羅性 | Phase 1 で使用したソース | 全件記載 |

**優先度**: P0

#### 機能5: Markdown 制約の確立

**ユーザーストーリー**:
将来 Web 公開する開発者として、変換コストを下げるために、portability の高い Markdown のみが使われる規約が欲しい。

**受け入れ条件**:
- [ ] `vault/90_meta/markdown-rules.md` に許可記法（標準 Markdown + Wikilinks）と禁止記法（Dataview, Callout 等の Obsidian 独自記法）が記載
- [ ] 規約違反を検出する CI チェックが存在

**優先度**: P0

#### 機能6: ローカル CLI による記事再生成

**ユーザーストーリー**:
Wiki 編集者として、ローカル環境で記事を生成・更新できるよう、冪等に動作する CLI が欲しい。

**受け入れ条件**:
- [ ] `agent/runners/local.{ts,py}` が存在し、対象記事を引数で指定して再生成できる
- [ ] 同じ入力に対し、意味のある差分のみを出力する（タイムスタンプの差分は最小化）
- [ ] エラー時は記事を更新せず、エラーログを残す

**検証方法**:
| 検証項目 | テストデータ | 合格基準 |
|---------|------------|---------|
| 冪等性 | 同一記事を連続2回再生成 | 2回目は意味のある差分なし |

**優先度**: P0

### P1（重要 / Phase 2）

#### 機能7: AUTO セクションマーカー

**ユーザーストーリー**:
Wiki 編集者として、自分が手で書いた解説を自動 PR で上書きされないよう、自動生成領域と人手編集領域を明示的に分離したい。

**受け入れ条件**:
- [ ] `vault/90_meta/auto-marker-spec.md` にマーカー仕様 (`<!-- AUTO:START --> ... <!-- AUTO:END -->`) が記載
- [ ] エージェントは AUTO 領域内のみ書き換え、領域外は触らない
- [ ] 既存全記事に AUTO マーカーが反映済み
- [ ] 1記事の手動再生成で、AUTO 領域のみ更新され、人手編集領域は保持されることを検証するテストが PASS

**優先度**: P1

#### 機能8: 公式全6カテゴリへの手動展開と派生種別の追加

**ユーザーストーリー**:
日本語話者の Claude Code 開発者として、コア機能だけでなく周辺領域も含めた全体像を把握できるよう、全カテゴリの `source` 記事と複数 source 横断の `concept` / `entity` 派生ページが欲しい。

**受け入れ条件**:
- [ ] `vault/sources/official/` の全6サブカテゴリ（cli, hooks, slash-commands, mcp, settings, sdk）に最低3 `source` 記事ずつ存在
- [ ] `vault/concepts/` に最低5本の `concept` 記事
- [ ] `vault/entities/` に最低5本の `entity` 記事
- [ ] `/wiki-query` コマンドで Wiki 横断検索 → `vault/syntheses/` への保存が動作する

**優先度**: P1

#### 機能9: 人手レビュー工数の実測

**ユーザーストーリー**:
プロジェクト管理者として、Phase 3 の自動化を設計するために、現実の人手レビュー工数を把握したい。

**受け入れ条件**:
- [ ] `vault/90_meta/metrics.md` に「記事1本あたりのレビュー時間」が記録されている
- [ ] サンプル数が10件以上

**優先度**: P1

### P2（できれば / Phase 3）

#### 機能10: GitHub Actions 週次自動更新

**ユーザーストーリー**:
プロジェクト管理者として、開発者個人のマシン稼働に依存せずに Wiki が常に最新であることを担保するため、クラウドで週次自動更新が走って欲しい。

**受け入れ条件**:
- [ ] `.github/workflows/weekly-update.yml` が存在し、週次 cron で `agent/runners/action.{ts,py}` を起動
- [ ] 変更があれば自動 PR を作成し、PR テンプレに変更ソース・diff サマリ・`claude_code_version` を含める
- [ ] CODEOWNERS でレビュー担当が自動割当される
- [ ] 4週連続で cron が成功し、自動 PR が4本立っている
- [ ] 失敗時に Actions ログから原因が特定できる

**優先度**: P2

#### 機能11: コミュニティソースの取り込み

**ユーザーストーリー**:
日本語話者の Claude Code 開発者として、英語コミュニティの最新ノウハウに早くアクセスできるよう、ホワイトリスト済みのコミュニティソースから自動で記事化されて欲しい。

**受け入れ条件**:
- [ ] ホワイトリスト済みコミュニティソース（Anthropic ブログ RSS、anthropics/claude-code Releases 等）から最低1ソースが取り込まれている
- [ ] 取得失敗時はエラーログを残し、PR は作成されない

**優先度**: P2

#### 機能12: コスト・運用ログ

**受け入れ条件**:
- [ ] `vault/90_meta/cost-log.md` に月額 API コスト実測値が記録され、見積範囲内である
- [ ] 月次運用が3ヶ月連続で回っている

**優先度**: P2

## 非機能要件

### パフォーマンス

| 処理 | 目標 | 測定条件 |
|------|------|---------|
| 週次更新ジョブ全体の実行時間 | 30分以内 | 全カテゴリ更新（差分検知あり）/ GitHub Actions 標準ランナー |
| ローカル CLI による1記事再生成 | 60秒以内 | 標準的な開発マシン（Apple Silicon Mac, 16GB RAM 想定） |
| frontmatter 検証 CI | 30秒以内 | 全記事を対象 |

### ユーザビリティ

- Obsidian で Wiki を開いた際、Wikilinks がリンクとして機能する
- 公式ドキュメントへの導線（リンク）が記事先頭から3スクロール以内に存在
- 全記事が「3部構成」で統一されており、読み手が構造を学習する必要がない

### 信頼性

- 情報源の取得失敗時は記事を更新せず、エラーログを残す（古い情報の保持を優先）
- LLM 生成失敗時は PR を作成せず、Actions を fail させる
- frontmatter 検証エラー時は CI を fail させる

### セキュリティ

- 機密情報（API キー）は環境変数 / GitHub Secrets で管理し、コードベースに含めない
- 取得元への過度なアクセスを避ける（差分検知で更新対象を絞る、レート制限遵守）

## 技術スタック

> 実装言語の最終確定は Phase 1 着手時に行う（CLAUDE.md 記載通り）。
> 以下はアイデアファイル（`agent/runners/local.ts` 等の表記）からの推測値であり、要確認項目を含む。

| 項目 | 技術 | 選定理由 |
|------|------|---------|
| エージェント実装言語 | TypeScript（要確認）または Python | アイデアファイル中で `.ts` 拡張子で例示。Claude Agent SDK は両言語対応 |
| エージェント基盤 | Claude Agent SDK | クラウド実行（GitHub Actions）と長期運用を前提 |
| クラウド実行 | GitHub Actions（cron） | PR レビュー文化と自然に統合 |
| ローカル実行 | Claude Code | 開発フェーズの素早いイテレーション |
| バージョン管理 | Git / GitHub | PR ベースのレビュー文化 |
| Wiki UI（ローカル） | Obsidian | Wikilinks・グラフビュー・全文検索 |
| コンテンツフォーマット | Markdown + YAML frontmatter | portability、機械可読性 |
| 情報取得 | RSS パーサ / GitHub API（octokit 等） | 利用規約上問題ない一次取得 |
| 検証・テスト | 要確認（言語確定後） | - |

## スコープ外

- **Wiki 本体の Web 公開**: GitHub Pages / 静的サイトジェネレータでの公開は別スコープ（Phase 3 完了後に検討）
- **プレゼンテーション資料の自動生成**: スライド生成は別アイデアとして切り出し
- **多言語対応**: 日本語のみ。英語ミラー・他言語は対応しない
- **LLM 投入用 RAG インデックスの構築**: ベクトル DB 等の整備は将来検討
- **Anthropic Routines / Schedule での実装**: GitHub Actions が安定するまで保留
- **品質スコアリング**: 生成記事の信頼度・新鮮度の自動評価は将来対応

## リスクと対策

| リスク | 影響度 | 発生可能性 | 対策 |
|-------|-------|-----------|------|
| Anthropic Usage Policy / docs.claude.com 利用規約違反 | 高 | 中 | Phase 1 着手前に規約確認。要約 + リンク + 補足構造を強制し、全文転載を禁止 |
| Reddit API 有料化・GitHub レート制限・スクレイピング bot 検知 | 高 | 中 | Phase 1 で情報源ホワイトリストを確定。RSS / 公式 API / 利用規約上問題ないソースのみに限定 |
| Claude Code バージョン揮発性による記事陳腐化 | 高 | 高 | `claude_code_version` を Phase 1 から frontmatter 必須化。古い記事を識別可能にする |
| Obsidian 独自記法の portability 欠如 | 中 | 中 | Phase 1 で「標準 MD + Wikilinks のみ」を規約化。Dataview 禁止 |
| 自動 PR が人手編集を上書きする事故 | 中 | 中 | Phase 2 で AUTO セクションマーカーを導入し、自動領域と人手領域を分離 |
| API コストの想定超過 | 中 | 中 | Phase 3 で `cost-log.md` に実測値を記録。差分検知で更新対象を絞る。prompt caching を活用 |
| 翻訳・要約の品質低下 | 中 | 中 | 人間レビュー必須。レビュー工数を Phase 2 で実測し、品質基準を Phase 3 で設定 |
| GitHub Actions の IP からのアクセス遮断 | 低 | 低 | RSS / 公式 API を優先。スクレイピングが必要なソースは事前検証 |

## 開発フェーズ

### Phase 1: 規約確立 + Skill 雛形 + 公式 hooks/cli の `source` 種別10本

**目標**: Wiki の骨格・規約・Skill パッケージを確立し、`source` 種別の規約準拠コンテンツが少量でも揃った状態にする

**実装内容**:
- `vault/` ディレクトリ構造（ページ種別ベース）の作成
- ナビゲーション3点（`index.md`, `log.md`, `overview.md`）の雛形配置
- frontmatter 規約（`type` 別必須キー）・Markdown 制約・情報源ホワイトリスト・利用規約整理・lint ルール
- `vault/sources/official/hooks/` と `vault/sources/official/cli/` の手動記事化（合計10本、`type: source`）
- `.claude/commands/wiki-{ingest,regenerate,lint}.md` のスラッシュコマンド配置 + `.claude/skills/llm-wiki-for-claude-code/`（`SKILL.md` + `references/` + `hooks/`）の Skill パッケージ配置（ADR-014）
- `agent/runners/local.{ts,py}` の最小実装（`ingest` / `regenerate` / `lint` / `validate` サブコマンド）

**成功基準**:
- [ ] PRD 機能1〜6 の受け入れ条件全クリア
- [ ] `source` 種別記事10本が `status: published` かつ `confidence ≥ 0.7` で存在
- [x] `agent regenerate` の冪等動作
- [ ] スラッシュコマンド `/wiki-ingest` / `/wiki-regenerate` / `/wiki-lint` がローカルで動作（`.claude/commands/` 配下）

### Phase 2: 派生ページ種別追加 + AUTO マーカー + 公式全6カテゴリ展開

**目標**: 派生ページ種別（concept / entity / synthesis）を導入し、全カテゴリへの展開で運用上の課題を洗い出し、自動化に向けた人手領域分離の仕組みを導入する

**実装内容**:
- AUTO セクションマーカー仕様の確定と既存記事への適用
- `vault/concepts/`, `vault/entities/` への派生ページ作成（各5本以上）
- `/wiki-query` コマンドの実装と `vault/syntheses/` への保存
- 公式全6カテゴリへの展開（最低3 `source` 記事/カテゴリ）
- 人手レビュー工数の実測

**成功基準**:
- [ ] PRD 機能7〜9 の受け入れ条件全クリア
- [ ] 1記事の `/wiki-regenerate` で AUTO 領域のみ更新されることを検証
- [ ] `/wiki-query` で synthesis 保存が動作

### Phase 3: GitHub Actions 自動化 + コミュニティソース拡張 + comparison 自動生成

**目標**: 人手介入を最小化した週次自動更新を本番運用に乗せる

**実装内容**:
- `agent/runners/action.{ts,py}` の実装
- `.github/workflows/weekly-update.yml` の追加
- CODEOWNERS / PR テンプレ整備
- ホワイトリスト済みコミュニティソースの取り込み
- コスト・運用ログの整備

**成功基準**:
- [ ] PRD 機能10〜12 の受け入れ条件全クリア
- [ ] 4週連続で自動 PR が立ち、人手修正率30%以下
- [ ] 月次運用3ヶ月連続成功

## APIインターフェース（想定）

### スラッシュコマンド（Claude Code から起動、`.claude/commands/` 配下）

```
/wiki-ingest <official-url>          # 新ソース取込み
/wiki-regenerate <path>              # 既存 source の再生成
/wiki-lint                           # 矛盾・孤立・陳腐化検出
/wiki-query <question>               # Wiki 横断検索（Phase 2）
```

### ローカル CLI（要確認: 言語確定後に最終化）

```bash
# 新ソース取込み
agent ingest --source-url https://code.claude.com/docs/ja/hooks --category hooks

# 単記事の再生成
agent regenerate --target vault/sources/official/hooks/pre-tool-use.md

# lint 検査
agent lint --all

# 機械的検証（CI 用）
agent validate --all
```

### GitHub Actions エントリポイント

```yaml
# .github/workflows/weekly-update.yml（想定）
on:
  schedule:
    - cron: "0 0 * * 1"  # 毎週月曜 UTC 00:00
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: agent action --create-pr
```

### エージェント内部の責務分割（想定）

| モジュール | 責務 |
|-----------|------|
| `agent/fetchers/` | 情報源からの取得（RSS, GitHub API, スクレイプ） |
| `agent/writers/` | Markdown 生成・更新ロジック（AUTO マーカー対応） |
| `agent/prompts/` | LLM への指示テンプレート |
| `agent/runners/local.*` | ローカル CLI エントリポイント |
| `agent/runners/action.*` | GitHub Actions エントリポイント |
