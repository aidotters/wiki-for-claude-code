> **ステータス: 計画段階**
> このドキュメントは `docs/ideas/20260505-llm-wiki-for-claude-code.md` から生成されました。
> 実装後・新たな決定後は追記してください。

# 設計判断記録 (Architecture Decision Records)

本プロジェクトで意図的に行った設計判断と、その「なぜ」を時系列で記録する。
将来の自分・他のレビュアー・LLM エージェントが「なぜこの選択になったのか」「不採用案は何だったか」を辿れるようにすることが目的。

## ADR フォーマット

各 ADR は以下を含める:

- **ステータス**: `proposed` / `accepted` / `superseded by ADR-NNN` / `deprecated`
- **コンテキスト**: 何を決めるか、何が制約か
- **決定**: 何を選んだか
- **理由**: なぜそれを選んだか
- **不採用案**: 検討した代替案と却下理由
- **影響**: 後続作業・他 ADR への含意

新しい決定は ADR 番号を採番して追記する。既存 ADR を覆す場合は新 ADR を立て、旧 ADR を `superseded by` でマークする（書き換えない）。

---

## ADR-001: ドメイン特化コンパイル型 Wiki を採用する（Karpathy/Rezvani 折衷案）

**ステータス**: accepted（2026-05-05、本版で訂正）

> **訂正履歴**: 初版（2026-05-05 初版）では Karpathy gist の「A/B/C」を3つの運用案（人間 vs LLM の編集役割）として誤読し「C 案」採用と記載していた。実際の Karpathy gist の A/B/C はアーキテクチャの3レイヤー（Raw Sources / Wiki / Schema）であり、運用案の選択肢ではない。本版（2026-05-05 同日改訂）でこの誤読を訂正し、Karpathy 原案 + Reza Rezvani Medium 記事（2026-04）の Skill パッケージング設計を踏まえた折衷案として再定義する。

**コンテキスト**:

Andrej Karpathy 氏の LLM-Wiki gist（2026-04 公開）は、知識ベースを以下の **3レイヤー** に分離する設計を提案している:

- **Raw Sources 層**: 不変の一次情報（記事、論文、議事録）。LLM は読むのみ
- **Wiki 層**: LLM が生成・維持する Markdown ページ群（要約・エンティティ・概念・比較・統合）
- **Schema 層**: Wiki の構造とワークフローを LLM に伝える設定（CLAUDE.md / Skill 定義）

Rezvani 氏の Medium 記事はこれを **Claude Code Skill** として実装する具体パターン（`SKILL.md` + `commands/` + `hooks/` + `references/`）と、ページ種別5種類（source / concept / entity / comparison / synthesis）を提示している。

本プロジェクトは「日本語話者の Claude Code 開発者向けの常に最新な公開 Wiki」を目指しており、コンテンツ品質・著作権配慮（Anthropic Usage Policy）・LLM 投入素材としての再利用性の両立が必要。

**決定**:

Karpathy 原案の3レイヤー構造とページ種別5種類、および Rezvani 記事の Skill パッケージング設計を採用しつつ、本プロジェクト特有の要件（公開 Wiki、Anthropic Policy 対応、人間レビュー必須）に合わせて以下の独自要素を加える **「ドメイン特化コンパイル型 Wiki」** を採用する。

#### 原案からの主な独自要素

| 観点 | Karpathy/Rezvani 原案 | 本プロジェクト |
|------|---------------------|--------------|
| 主たる利用者 | 自分自身 / チーム（セカンドブレイン） | 不特定の日本語話者（公開 Wiki） |
| ソースの性質 | 自分が選んだ任意の一次資料 | Claude Code ドメイン限定のホワイトリスト済みソース |
| 編集者 | LLM がほぼ100%書く | LLM が PR 提案、人間レビュー必須（公開品質確保のため） |
| 著作権配慮 | 言及なし | `source` 種別に「要約 + リンク + 補足」3部構成を強制（ADR-003） |
| 自動化 | 個人の手動 ingest が中心 | GitHub Actions による週次自動更新を前提（Phase 3、ADR-007） |
| Dataview | 推奨 | 不採用（ADR-004、Web 公開を見据えた portability 重視） |

**理由**:

- ページ種別5種類により「1 source から複数の派生ページが育つコンパイル構造」を実現できる
- Skill 構造により Claude Code との親和性が高く、ローカル開発の入り口が明快
- 人間レビューを残すことで公開 Wiki としての品質ガードを保ちつつ、LLM の帳簿管理（相互参照・矛盾検出）の利点を享受できる
- 著作権配慮の独自制約（3部構成）を加えることで、Anthropic Policy 違反リスクを最小化できる

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| Karpathy/Rezvani 原案そのまま（個人 Vault + LLM 主導書込み） | 公開 Wiki としては引用必須・著作権配慮が不十分 |
| 公式ドキュメントの単純な要約集約（ページ種別なし） | コンパイル型の利点を失い、原典との乖離が大きい |
| 公式ドキュメントの全文翻訳 | 著作権・利用規約リスク。原文更新時の追従コストが高い |

**影響**:
- ADR-002（Vault = Repo 統合）の前提
- ADR-003（`source` 種別への3部構成）の前提
- ADR-011（ページ種別5種類）の前提
- ADR-012（Skill パッケージング）の前提
- 人間レビューの工数を Phase 2 で実測する必要がある（PRD KPI）

---

## ADR-002: Obsidian Vault と Git リポジトリを統合する（Vault = Repo）

**ステータス**: accepted（2026-05-05）

**コンテキスト**:
Wiki コンテンツを Obsidian で編集しつつ、Git で履歴管理・PR レビューしたい。
構成として、Vault と Git リポジトリを別ディレクトリで管理する選択肢もある。

**決定**:
Obsidian Vault と Git リポジトリを同一ディレクトリに統合する（プロジェクトルート = Vault ルート相当）。

**理由**:
- Vault と Repo を別経路で同期する手間と事故リスクを排除できる
- 編集→コミット→PR の流れが1ディレクトリで完結する
- `.obsidian/` のうち個別設定のみ `.gitignore` 除外すれば、共通プラグイン設定は Git 管理できる

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| Vault と Repo を分離（symlink 等で同期） | 同期問題が常時発生し、設計上の主要ボトルネックになる |

**影響**:
- `vault/` ディレクトリが Wiki 本体兼 Vault ルート相当
- `.obsidian/workspace.json` 等は `.gitignore` 対象

---

## ADR-003: 公式コンテンツは「要約 + リンク + 補足」3部構成とする（全文翻訳しない）

**ステータス**: superseded by ADR-017（2026-05-06）— ADR-017 で縮退仕様に切替

**コンテキスト**:
Anthropic Usage Policy / docs.claude.com の利用規約により、公式ドキュメントの全文転載・全文翻訳は著作権・規約上のリスクがある。
一方、日本語話者にとっては要約だけでなく一次情報への到達も重要。

**決定**:
公式由来コンテンツは以下の3部構成を強制する:

```markdown
## 概要 (要約)
（公式の核となるポイントを日本語で要約。3-5文程度）

## 公式ドキュメント
→ {公式 URL}（最終確認: YYYY-MM-DD / 対象バージョン: X.Y.Z）

## 補足解説 (日本語)
（実利用例、ハマりどころ、関連機能との関係など独自価値）
```

**理由**:
- 全文転載を避けることで著作権・利用規約リスクを最小化
- 公式リンクへの導線を必須化することで、ユーザーは常に一次情報へアクセス可能
- 「補足解説」が独自価値（実例・関係性・ハマりどころ）を生み、単なる翻訳サイトに劣後しない

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| 公式ドキュメントの全文翻訳 | 著作権・利用規約リスク。原文更新追従コスト高 |
| 要約のみ（公式リンクなし） | 一次情報到達性が損なわれる |
| 補足解説なし | 独自価値が乏しく、ブログ記事に劣後する |

**影響**:
- CI チェックで3部構成の存在を検証する（Phase 1）
- 「連続100文字以上の公式コンテンツ一致」を全文転載検出として扱う（Phase 2 以降検討）
- ADR-008（情報源ホワイトリスト）と組で機能する

---

## ADR-004: 標準 Markdown + Wikilinks のみ許可、Obsidian 独自記法は禁止

**ステータス**: accepted（2026-05-05）

**コンテキスト**:
Obsidian には Dataview, Callout (`> [!note]`) など強力な独自記法がある。
ただし、本プロジェクトは将来的な Web 公開（GitHub Pages 等）を視野に入れており、portability が重要。

**決定**:
許可記法は「標準 Markdown（CommonMark 準拠）+ Wikilinks（`[[file-name]]`）+ Mermaid」のみ。
Dataview / Callout / その他 Obsidian 独自記法は禁止。

**理由**:
- 将来 Web 公開する際の変換コストを下げる
- LLM が記事を読み込む際の解釈一貫性を保つ
- Wikilinks は CommonMark 外だが、Obsidian で機能し、変換も容易なため許容

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| Obsidian 独自記法も許可 | 将来の portability を犠牲にする |
| Wikilinks も禁止 | Obsidian での編集体験が大きく損なわれる |

**影響**:
- CI で禁止記法を検出する（Phase 1）
- `vault/90_meta/markdown-rules.md` に詳細を記載

---

## ADR-005: 規約先行（Phase 1）でコンテンツ生成・自動化に進む

**ステータス**: accepted（2026-05-05）

**コンテキスト**:
LLM-Wiki の運用は frontmatter 規約 / Markdown 制約 / 情報源ホワイトリスト / 利用規約整理が確立していないと、後から大量の修正が必要になる。
一方、規約だけ完璧でもコンテンツが揃わなければ価値が出ない。

**決定**:
Phase 1 では「規約確立 + 公式2カテゴリ手動化」のセットを完成させてから、Phase 2 以降に進む。

**理由**:
- 規約に違反したコンテンツが大量に存在する状態を作らない
- 規約は実コンテンツでの試運転を経て確定するため、少量のコンテンツと並行して詰める
- Phase 1 完了基準が明確になる（規約準拠記事10本 + 再生成スクリプト冪等動作）

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| 規約とコンテンツを完全並行 | 規約変更時の手戻りが大きい |
| コンテンツ先行 → 後から規約整備 | 既存コンテンツの一括修正コストが高い |

**影響**:
- Phase 1 のスコープが「規約 + 2カテゴリ手動」に限定される
- 自動化（Phase 3）は規約成熟後に着手

---

## ADR-006: AUTO セクションマーカーで自動領域と人手領域を分離する（Phase 2 で導入）

**ステータス**: accepted（2026-05-05）— Phase 2 で実装

**コンテキスト**:
Phase 3 で自動 PR が常時走る状態になると、人手で書いた補足解説を自動 PR が上書きするリスクがある。

**決定**:
記事内に `<!-- AUTO:START -->` 〜 `<!-- AUTO:END -->` のマーカーを置き、
- 自動領域: マーカー内（エージェントが書き換える）
- 人手領域: マーカー外（エージェントは触らない、バイト一致で保持）

として分離する。

**理由**:
- 自動 PR が人手編集を上書きする事故を構造的に防げる
- レビュー時、自動領域 / 人手領域の責任主体が明確
- 記事の可読性は維持される（マーカーは HTML コメントで非表示）

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| ファイルごと自動 / 人手で分離 | 1記事内に両者が混在するのが自然なため非現実的 |
| frontmatter 上で `human_edited: true` ならスキップ | 部分的人手編集を許容できない |
| 人手編集後は自動更新を停止 | バージョン陳腐化の追従ができなくなる |

**影響**:
- Phase 2 で `vault/90_meta/auto-marker-spec.md` を確定
- Phase 2 で既存全記事へマーカー反映
- Writer は AUTO 領域のみ書き換え、外側はバイト一致保持の実装が必要

---

## ADR-007: 開発フェーズはローカル Claude Code、本番フェーズは GitHub Actions + Claude Agent SDK で実行する

**ステータス**: accepted（2026-05-05）

**コンテキスト**:
エージェントの実行基盤として、ローカル開発と本番運用で異なる環境が候補にある:
- ローカル: Claude Code（B 案）
- クラウド: GitHub Actions + Claude Agent SDK（A 案）
- スケジュール基盤: Anthropic Routines / Schedule（C 案）

各々のメリット・デメリットを踏まえ、フェーズで使い分ける。

**決定**:
- 開発フェーズ（Phase 1 / 2）: ローカル Claude Code
- 本番フェーズ（Phase 3）: GitHub Actions（cron）+ Claude Agent SDK
- ロジック層は環境非依存とし、`agent/runners/{local,action}` の薄いランナーから共通ロジックを呼ぶ

**理由**:
- ローカル Claude Code は素早いイテレーションに向く（Phase 1/2 のコンテンツ作成・規約調整）
- GitHub Actions は PR レビュー文化と自然に統合され、CODEOWNERS 等の仕組みが使える
- 環境非依存ロジックにすることで、将来の基盤切り替え（例: Anthropic Routines）も低コストで可能

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| ローカル Claude Code のみ（B 案） | マシン依存で常時更新を保証できない |
| GitHub Actions のみ（A 案） | 開発フェーズの初期セットアップコストが高く、イテレーションが遅い |
| Anthropic Routines / Schedule（C 案） | 機能が比較的新しく、長期運用基盤としては未知数（Phase 3 安定後に再検討） |

**影響**:
- `agent/runners/{local,action}` の二系統ランナー構成
- ロジック層（fetchers, writers, prompts）は環境非依存の制約
- ADR-009（将来 Routines 検討）の前提

---

## ADR-008: 情報源はホワイトリスト方式で管理する

**ステータス**: accepted（2026-05-05）

**コンテキスト**:
コミュニティソース（Reddit, GitHub Discussions, awesome-claude-code, X 等）は有用だが、利用規約・API 制限・スクレイピング bot 検知のリスクがある。
無制限に取得すると、利用規約違反や IP 遮断につながる。

**決定**:
`vault/90_meta/sources.md` にホワイトリスト形式で許可ソースを管理する。
エージェントはホワイトリスト外のソースから情報取得しない。
各ソースには利用規約 / 取得方式（RSS / API / スクレイプ）/ レート制限を記載する。

**理由**:
- 利用規約違反を構造的に防ぐ
- レート制限を一元管理できる
- 新規ソース追加時に必ず利用規約検証を経るプロセスを強制できる

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| ブラックリスト方式 | 想定外ソースが許可されてしまう（fail-open） |
| 個別記事ごとに `source_url` で管理 | ソース全体のレート制限・規約検証ができない |

**影響**:
- ADR-003（3部構成）と組で利用規約リスクを最小化
- Phase 1 で初版ホワイトリストを確定（PRD 機能4）
- Phase 3 のコミュニティソース取り込みもこの仕組みに乗る

---

## ADR-009: Anthropic Routines / Schedule での実装は当面採用しない

**ステータス**: accepted（2026-05-05）— 将来再検討

**コンテキスト**:
Anthropic Routines / Schedule はクラウド実行基盤として有力候補だが、機能が比較的新しい。

**決定**:
Phase 3 では GitHub Actions + Claude Agent SDK を採用し、Anthropic Routines / Schedule は採用しない。
Phase 3 安定後（月次運用3ヶ月連続成功後）に移行を再検討する。

**理由**:
- 長期運用基盤としての成熟度が GitHub Actions より低い
- PR レビュー文化との統合が GitHub Actions の方が自然
- 環境非依存ロジック設計（ADR-007）により、将来の移行コストは小さい

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| 最初から Routines / Schedule を採用 | 未知数を抱えたまま本番運用に進むリスク |

**影響**:
- Phase 3 完了後に再評価する。再評価の結果、移行する場合は新 ADR で記録

---

## ADR-011: ページ種別を5種類（source / concept / entity / comparison / synthesis）で構造化する

**ステータス**: accepted（2026-05-05）

**コンテキスト**:

Karpathy gist と Rezvani Medium 記事は、Wiki ページを以下の5種類に分類することを提示している:

- `source`: 取込み元の要約
- `concept`: 複数 source 横断の概念
- `entity`: ツール・コマンド・人物
- `comparison`: 競合アプローチ比較
- `synthesis`: クエリ結果の保存

本プロジェクトの当初設計（2026-05-05 初版）は「公式ドキュメントカテゴリ別の単純な要約集約」だったが、これでは1 source から複数の派生ページが育つ「コンパイル型」の利点が得られない。

**決定**:

Karpathy/Rezvani 原案のページ種別5種類を採用する。ディレクトリ構造は以下:

```
vault/
├── sources/{official,community}/<category>/   # type=source
├── concepts/                                    # type=concept
├── entities/                                    # type=entity
├── comparisons/                                 # type=comparison
└── syntheses/                                   # type=synthesis
```

frontmatter の `type` キーで種別を識別し、`agent/validators` は `type` 別に適用ルールを切り替える。

**理由**:

- 1つの公式ドキュメントから派生する `entity`（例: 「Bash tool」）や `concept`（例: 「permission mode」）が育ち、コンパイル型 Wiki の利点を得られる
- ドメイン分類（cli/hooks/mcp 等）はサブディレクトリと `tags` で表現できるため、種別軸との両立が可能
- `synthesis` 種別により `/wiki-query` の結果を保存・再利用できる（Phase 2）
- `comparison` 種別により Phase 3 で「hooks vs Skills」「Bash vs MCP」などの比較を自動生成できる

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| ドメインカテゴリ（cli/hooks/...）のみで分類（ページ種別なし） | コンパイル型の利点を失う |
| ページ種別を採用するが、ドメインカテゴリを `tags` で表現しない | 公式ドキュメント整理の見通しが悪化する |

**影響**:
- ADR-001（折衷案）の構成要素
- frontmatter 規約に `type` キーが必須化される
- Phase 1 では `source` のみ実装、Phase 2 で派生種別を追加
- `agent/validators/frontmatter_validator` が `type` 別に切り替わる構造を要する

---

## ADR-012: Claude Code Skill としてパッケージングする

**ステータス**: accepted（2026-05-05）／ 2026-05-05 に ADR-014 で構造を改訂

**コンテキスト**:

Rezvani Medium 記事は LLM-Wiki を **Claude Code Skill** として実装する具体パターンを提示している（`SKILL.md` + `commands/` + `hooks/` + `references/`）。これにより Wiki 操作を Claude Code から直接起動できる。

当初設計（2026-05-05 初版）は `agent/runners/local.{ts|py}` のスタンドアローン CLI のみを想定しており、Skill 化は考慮していなかった。

**決定**:

`.claude/skills/llm-wiki-for-claude-code/` に Skill パッケージを配置し、Claude Code 統合の入り口とする。同時に `agent/` を環境非依存ロジック層として保持し、スラッシュコマンドからも GitHub Actions からも同じロジックを呼ぶ二段構造とする。

> **改訂（ADR-014）**: 当初は Skill 内に `commands/` サブディレクトリを置く Rezvani 記事のレイアウトを踏襲する想定だったが、公式ドキュメント（claude-code/skills.md）を確認した結果、**Skill 内 `commands/` サブディレクトリは公式仕様外**であり、スラッシュコマンドは `.claude/commands/*.md`（トップレベル）または独立 Skill `.claude/skills/<name>/SKILL.md`（1コマンド = 1 Skill）として配置するのが正しい。本プロジェクトでは `.claude/commands/` と Skill `references/` を分離する構造を採用する（詳細は ADR-014）。

**理由**:

- Claude Code との親和性が圧倒的に高く、ユーザーがスラッシュコマンドで操作可能
- `hooks/session-start.md` で起動時に Wiki コンテキストを自動ロードでき、シームレスな対話を実現できる
- `agent/` ロジック層を分離して残すことで、Phase 3 の GitHub Actions も同じロジックを呼べる
- `references/` は `vault/90_meta/` のシンボリックリンクとすることで、規約の二重管理を回避できる

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| `agent/` CLI のみ（Skill 化なし） | Claude Code 統合の利便性を失う、Rezvani 記事の中核価値を取り入れられない |
| Skill のみ（`agent/` ロジック層なし） | GitHub Actions から同じロジックを再利用できない（Phase 3） |
| Skill `references/` を独立配置（`vault/90_meta/` 不在） | 規約の二重管理が発生し、CI 検証と Skill ガイダンスがズレるリスク |

**影響**:
- ADR-001（折衷案）の構成要素
- ADR-007（環境非依存ロジック）と組み合わさり、二段構造を成立させる
- Phase 1 タスクに「Skill パッケージ構築」が追加される
- frontmatter `category` キーは廃止し、ディレクトリパスと `tags` で代替する
- 構造の詳細は ADR-014 で改訂（Skill と Slash Command の分離）

---

## ADR-014: Slash Command と Skill を分離して配置する

**ステータス**: accepted（2026-05-05）

**コンテキスト**:

ADR-012 初版では Rezvani Medium 記事のレイアウトに倣い、Skill 内に `commands/` サブディレクトリを置く構造（`.claude/skills/llm-wiki-for-claude-code/commands/wiki-*.md`）を想定していた。しかし Anthropic 公式ドキュメント（claude-code/skills.md）を確認すると以下の事実が判明した:

1. **スラッシュコマンドと Skill は技術的に等価**: `.claude/commands/deploy.md` と `.claude/skills/deploy/SKILL.md` はどちらも `/deploy` を生成する（公式 doc 引用: "Custom commands have been merged into skills"）
2. **既存 `.claude/commands/` は引き続きサポート**: 非推奨化アナウンスは存在しない
3. **Skill 内 `commands/` サブディレクトリは公式仕様にない**: Skill は `SKILL.md` 直下にサポートファイル（references/, scripts/ 等）を置く flat 構造が前提。複数のサブコマンドを Skill 配下に束ねる仕組みは公式仕様に存在しない

つまり、当初設計は Rezvani 記事の独自慣習に依存しており、公式仕様と乖離している。

**決定**:

スラッシュコマンドと Skill を**分離**して配置する。

- `.claude/commands/{wiki-ingest,wiki-regenerate,wiki-lint}.md`（Phase 1）+ `wiki-query.md`（Phase 2）— **明示起動の操作**
- `.claude/skills/llm-wiki-for-claude-code/{SKILL.md, references/, hooks/}` — **規約・テンプレート・hook の自動参照領域**（`commands/` サブディレクトリは置かない）

```
.claude/
├── commands/
│   ├── wiki-ingest.md
│   ├── wiki-regenerate.md
│   ├── wiki-lint.md
│   └── wiki-query.md                # Phase 2 で追加
└── skills/
    └── llm-wiki-for-claude-code/
        ├── SKILL.md                  # 規約ガイダンスを context-aware に自動ロード
        ├── references/               # vault/90_meta/ へのシンボリックリンク
        │   ├── schema.md
        │   ├── three-part-rule.md
        │   ├── sources-whitelist.md
        │   ├── lint-rules.md
        │   └── page-templates.md
        └── hooks/
            └── session-start.md      # 起動時に index.md / log.md ロード
```

**理由**:

- **公式仕様準拠**: Skill 内 `commands/` サブディレクトリの非公式パターンを排除し、将来の Skill loader 仕様変更に対する耐性を確保
- **責務分離**: 「明示起動の操作」（slash command）と「コンテキスト依存で参照される規約」（skill references）が分離され、責務が明快になる
- **Wiki 操作は明示起動が望ましい**: `/wiki-ingest` 等は副作用が大きく、自動起動されると意図しないファイル生成が発生する可能性があるため、ユーザーの明示的な起動に限定する slash command 形態が適合
- **規約・schema は自動参照されるべき**: frontmatter 規約・3部構成ルール・情報源ホワイトリストは編集中に常時参照したいため、コンテキストに応じて自動ロードされる Skill `references/` が適合
- **ファイルパス変更の影響範囲**: `commands/` 配下から `.claude/commands/` への移動のみで、Skill の `references/` `hooks/` の責務は不変（migration コストは小さい）

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| 各操作を独立 Skill 化（`.claude/skills/wiki-ingest/SKILL.md` 等を4つ作成） | Skill 数が増え、共通 references/ の重複や schema 同期コストが増加。`hooks/session-start.md` も各 Skill に分散する必要が生じ管理が煩雑 |
| ADR-012 初版のまま（Skill 内 `commands/` サブディレクトリ） | 公式仕様外で、Claude Code 内部の Skill loader が将来この階層を解決しなくなる可能性がある。Rezvani 記事のレイアウト依存 |
| Slash Command のみ（Skill 廃止） | `references/` の自動コンテキストロードが失われ、規約参照が手動 `@` 指定に頼る形になる。`hooks/session-start.md` も使えない |

**影響**:
- ADR-012 を改訂（Skill 構造の詳細を本 ADR に委譲）
- Phase 1 タスク「Skill パッケージ構築」が「Slash Command 配置 + Skill `references/`/`hooks/` 配置」に分割される
- `agent/runners/local` から見たエントリポイントは不変（slash command の中身が `agent <subcommand>` を呼ぶ点は同じ）
- `references/` の同期方式に関する ADR-013 の対象はそのまま（シンボリックリンク or ビルド時コピー）
- Skill `SKILL.md` の `description` は「Wiki の規約・テンプレート・schema を提供する。Wiki ページ編集時に自動参照」のように context-aware ロード向けに記述する

---

## ADR-010: 実装言語は Python 3.12+ を採用、ツールチェインは uv / pytest / ruff / mypy で統一する

**ステータス**: accepted（2026-05-05）

**コンテキスト**:
Phase 1 着手時に実装言語を確定する必要がある。候補は TypeScript（Node 20 LTS）と Python 3.12+ の2択。
本プロジェクトの主要関心事は以下:
- Markdown 処理（frontmatter / wikilinks / 構造検証）
- HTTP 取得（公式ドキュメントのフェッチ）
- LLM 呼び出し（Anthropic SDK）
- CLI ランナー（スラッシュコマンドから sub-process 起動）
- 将来の Claude Agent SDK 連携（Phase 3）
- バリデーション（JSON Schema、frontmatter 規約）

`CLAUDE.md` 内で `pytest`/`ruff`/`mypy` を前提にした記述があり、開発ガイドラインも Python サンプルが先行している。

**決定**:
- **言語**: Python 3.12+
- **パッケージマネージャ**: uv（高速・lock 一元管理）
- **テスト**: pytest 8.x（pytest-asyncio）
- **リンタ・フォーマッタ**: ruff 0.6+（lint + format 兼用）
- **型チェッカ**: mypy 1.10+（strict）
- **主要依存**: python-frontmatter, httpx, pyyaml, jsonschema, anthropic（Phase 3）, claude-agent-sdk（Phase 3）

**理由**:
- Markdown / YAML / 文字列処理ライブラリが Python 側で成熟（python-frontmatter, pyyaml）
- Anthropic 公式 SDK と Claude Agent SDK の両方が Python サポートを継続
- uv は依存解決と仮想環境管理を1コマンドで完結し、Node + npm/pnpm の二段構造より導入コストが低い
- ruff は Black + isort + Flake8 + Pyupgrade を統合した単一ツールで、設定ファイルが pyproject.toml に集約できる
- 型チェック strict によりプロジェクト後半（Phase 3 自動化）の保守性が確保される

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| TypeScript + Node 20 LTS + pnpm + Vitest + Biome | Markdown / frontmatter の周辺ツールが Python ほど成熟しておらず、特に `python-frontmatter` 相当の YAML ベース型安全パーサが弱い |
| Python 3.11 以前 | 3.12 の type alias / PEP 695 構文を活用しないと型表現が冗長になる |
| Poetry / pdm | uv より起動・依存解決が遅く、Node 経験者にとって学習コスト高 |
| Black + isort + Flake8 の3点セット | ruff 単一導入で同等以上の機能を提供できる |

**影響**:
- `pyproject.toml` をリポジトリルートに配置
- `agent/` 配下を Python パッケージとして実装（`agent/__init__.py` 含む）
- `tests/unit/`, `tests/integration/`, `tests/e2e/` を pytest で実行
- CI（`.github/workflows/validate.yml`）で `uv sync && uv run pytest && uv run ruff check && uv run mypy agent` を実行
- `agent` コマンドは `[project.scripts]` で `agent.runners.local:main` に紐付け

---

## ADR-013: Skill `references/` は `vault/90_meta/` のシンボリックリンクで同期する

**ステータス**: accepted（2026-05-05）

**コンテキスト**:
Skill `references/` 配下のドキュメント（schema, three-part-rule, sources-whitelist, lint-rules）は `vault/90_meta/` の対応ファイルと内容が完全一致する必要がある（規約の SSoT は `vault/90_meta/` 側）。
同期方式の候補は3つ:

1. **シンボリックリンク**: `references/schema.md → ../../../../vault/90_meta/frontmatter-spec.md`
2. **ビルド時コピー**: `scripts/sync-skill-references.{sh,py}` を CI / pre-commit で実行
3. **手動コピー**: 規約変更時に手で更新

**決定**:
シンボリックリンク方式を採用する。

**理由**:
- 規約変更が即時反映される（同期忘れリスクが構造的にゼロ）
- 追加ツール・スクリプト不要（メンテコスト最小）
- macOS / Linux で標準サポート、Git も `core.symlinks=true`（デフォルト）で追跡可能
- Claude Code の Skill loader はファイルシステム経由で読み取るため、シンボリックリンク経由でも実体が読める想定

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| ビルド時コピー（scripts + CI） | スクリプト管理コスト、コピー忘れリスク、PR 内で実体の二重管理になる |
| 手動コピー | 規約改訂時に高確率で同期漏れが発生 |

**影響**:
- Phase 1 で `.claude/skills/llm-wiki-for-claude-code/references/{schema.md, three-part-rule.md, sources-whitelist.md, lint-rules.md}` を `vault/90_meta/` 配下へのシンボリックリンクで作成
- `references/page-templates.md` のみ Skill 内固有のため実体ファイル（リンクなし）
- **Windows サポートは Phase 1 のスコープ外**（Windows での `core.symlinks` 設定依存はプロジェクト Wiki または README で明示）
- Phase 3 の GitHub Actions は Linux ランナで動作するため、シンボリックリンク経由の解決に問題なし
- 万一 Claude Code Skill loader がシンボリックリンクを解決できない事象が発生した場合は、本 ADR を `superseded by` として ADR-013-bis でビルド時コピー方式に切り替える

---

## ADR-015: AUTO セクションマーカーの構文と境界制御を確定する

**ステータス**: accepted（2026-05-06）— Phase 2-A で実装

**コンテキスト**:

ADR-006（2026-05-05）で AUTO セクションマーカーによる自動領域 / 人手領域の分離方針は確定したが、構文・境界制御・領域外バイト一致保持の規約は Phase 2 に持ち越されていた。Phase 2-A 着手にあたり、Writer 実装と人手レビューが両者ともに参照可能な SSoT を確定する必要がある。

**決定**:

AUTO マーカーの構文と運用規約を以下のとおり確定する:

- **構文**: HTML コメント `<!-- AUTO:START -->` と `<!-- AUTO:END -->` を行頭に置く（行内 inline は禁止）
- **ネスト禁止**: `START` 後に `END` より先に新たな `START` が出現した場合 `MalformedAutoMarkerError`
- **複数領域許容**: 1 ファイル内に順序付きで複数の AUTO 領域を配置可。書き換え API は領域番号で指定する
- **境界制御**: 構文不正（START のみ / END のみ / 順序不正 / ネスト）は Writer で例外を投げ、書き込みを中止する
- **領域外バイト一致保持**: AUTO 領域外の行のバイト列は書き換え前後で完全一致しなければならない（Writer 内部 assert + テストで担保）
- **frontmatter キー連動**: `auto_section_managed: true` を AUTO 導入済みファイルに付与する。Phase 2-A は対象 15 本のみ（公式 10 + recipe 5）、Phase 2-B で全展開

詳細仕様は `vault/90_meta/auto-marker-spec.md` を SSoT とする。

**理由**:

- 公開 Wiki の品質ガードとして、人手編集を構造的に保護する仕組みは Phase 2-A で先行投入する価値が高い（Phase 3 の自動 PR 化前提）
- HTML コメント構文は CommonMark 準拠で、Web 公開時のレンダラ互換性を確保できる
- 行頭限定にすることで正規表現でなく行単位スキャナで構文解析可能となり、誤検知が起きにくい
- 1 ファイル内に複数領域を許容することで、recipe の `## TL;DR` / `## 手順` のような複数の AUTO 領域パターンが自然に表現できる
- 領域外バイト一致保持を構造的に保証することで、ADR-006 の主張（自動 PR が人手編集を上書きしない）を Writer 単位で検証可能になる

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| 行内 inline 構文も許可 | パーサ複雑化、誤検知リスク増 |
| ネスト許可 | 領域の責任主体が曖昧化、自動書き換え範囲が不確定 |
| 1 ファイル 1 領域のみ | recipe 等の複数セクション構造に合わない |
| frontmatter `auto_section_managed: true` のときのみ書き換え許可、領域指定なし | 部分書き換えができず、自動 / 人手の境界が粒度の粗い「ファイル単位」になり ADR-006 の主旨に反する |

**影響**:

- Phase 2-A で `agent/writers/markdown_writer.py` に `extract_auto_regions` / `replace_auto_regions` を実装
- Phase 2-A 対象 15 本（公式 10 + recipe 5）に AUTO 領域を導入し `auto_section_managed: true` を付与
- Phase 2-B で全 source 記事および派生種別へ展開
- ADR-006 の方針を実装レベルで具体化（ADR-006 はそのまま accepted を維持）

---

## ADR-016: Phase 2 を 2-A（MVP）/ 2-B（拡張）に分割し、付加価値の主軸をコミュニティ知見整理に pivot する

**ステータス**: accepted（2026-05-06）

**コンテキスト**:

Phase 1 受け入れテスト（2026-05-06 PASS）時に、上流公式ドキュメントの大規模 URL 移行（`docs.claude.com/claude-code/*` → `code.claude.com/docs/{en,ja}/*`）を検出した。同時に **公式日本語版（`code.claude.com/docs/ja/*`）の存在** を確認したことで、当初の前提「公式は英語のみ → 日本語素訳に付加価値あり」が崩れた。

Phase 1 で生成した `vault/sources/official/` 10 本は「公式日本語ページの劣化コピー」化するリスクが顕在化し、付加価値の再定義が必要となった。

**決定**:

Phase 2 を以下の 2 段階に分割し、付加価値の主軸を pivot する:

- **Phase 2-A（MVP）**: 実 Anthropic SDK 統合 + 公式 source 縮退 + コミュニティ source 1 系統取込み（awesome-claude-code）+ `recipe` 種別先行 + AUTO マーカー最小実装 + metrics 計測開始
- **Phase 2-B（拡張）**: `concept` / `entity` / `synthesis` 種別本格実装 + `/wiki-query` + コミュニティ source 追加系統 + AUTO マーカー全展開 + Claude エコシステム拡張カテゴリ

Phase 2-A 完了時に修正率 / LLM コスト / ライセンス問題の 3 中止条件を判定し、Phase 2-B 着手 / 再計画 / 中止を判断する。

付加価値の再定義:

- 「公式素訳 + 補足」から「**コミュニティに散らばる実践知の定期整理 + 横断視点での再構成**」へ主軸を移す
- ユースケース別の `recipe`（Tips / セットアップ / チートシート）を新種別として先行投入
- 公式 source は「タイトル + 1 段落要約 + 公式リンク + AUTO 領域」の縮退仕様に切り替え（詳細は ADR-017）

**理由**:

- 公式日本語版の存在発覚により、3 部構成（要約 + リンク + 補足）強制での「素訳 + α」は付加価値が著しく低下する
- コミュニティ知見の整理は公式日本語版が代替できない領域で、本プロジェクト独自の付加価値が発揮できる
- Phase 2-A の MVP 検証で metrics（修正率 / コスト）を測定してから Phase 2-B の本格実装に進むことで、不確実性を構造的に低減できる
- `recipe` 種別を先行投入することで、ユースケース志向の Wiki としての方向性を早期に検証できる

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| Phase 2 当初計画のまま進行（公式 6 カテゴリ展開 + 派生種別フル実装） | 付加価値が公式日本語版の劣化コピーに収束するリスクが大、metrics 不在のまま大量生成すると修正コストが膨張 |
| Phase 2 を中止して全面再企画 | Phase 1 で確立した規約・agent 層を活かせない、再立ち上げのオーバーヘッドが大 |
| 公式 source を全削除してコミュニティ知見専業へ転換 | 公式リファレンスへの導線提供は読者ニーズとして残る、削除は破壊的 |

**影響**:

- 旧 Phase 2 計画（`.steering/20260506-llm-wiki-for-claude-code-phase-2/`）は参考用に保持、本フェーズは `.steering/20260506-llm-wiki-for-claude-code-phase-2a/` で再計画
- `CLAUDE.md` の「実装ロードマップ」表を 3 Phase × 2 軸から Phase 2-A / 2-B 分割反映に書き換える（Phase 2-A 完了時に実施）
- ADR-017（公式 source 縮退仕様）と ADR-015（AUTO マーカー）を本フェーズで起票し、規約整合を取る

---

## ADR-017: 公式 source 種別を縮退仕様（タイトル + 1 段落要約 + 公式リンク + AUTO 領域）に切り替える

**ステータス**: accepted（2026-05-06）— Phase 2-A で実装

**コンテキスト**:

ADR-003（2026-05-05）で公式由来コンテンツの「要約 + リンク + 補足解説」3 部構成を強制してきたが、ADR-016 で確認したとおり公式日本語版の存在により、3 部構成 source は「公式の劣化コピー + 限定的な補足」になりやすい。さらに、補足解説セクションは LLM 生成の品質ばらつきが大きく、人手レビューコストの主要因となっていた。

一方で、公式リファレンスへの導線提供と、簡潔な構造化情報（タイトル + 概要 + 公式 URL）は読者にとって価値が残る。

**決定**:

`type: source` の構造を以下の **縮退仕様** に切り替える:

```markdown
---
title: "<カテゴリ + ページ名>"
type: source
...
---

## 概要 (要約)
<!-- AUTO:START -->
（1 段落の日本語要約。3-5 文。公式日本語版の連続 100 文字一致を回避）
<!-- AUTO:END -->

## 公式ドキュメント
→ {公式日本語版 URL}
（最終確認: YYYY-MM-DD / 対象バージョン: X.Y.Z）
```

**変更点**（旧 ADR-003 比）:
- `## 補足解説 (日本語)` セクションを **撤廃**（補足は recipe / concept / entity 種別側で表現する）
- `## 概要 (要約)` を AUTO 領域化し、自動更新の主たる対象とする
- `transclusion_validator`（連続 100 文字一致禁止）は継続適用

ADR-003 は本 ADR で `superseded by ADR-017` とマークする。

**理由**:

- 公式日本語版が存在する以上、本プロジェクトの補足解説は重複コストが大きい。recipe / concept 種別で「横断視点」「ユースケース志向」を提供する方が付加価値が高い
- AUTO 領域化により、上流ドキュメント変更時の自動追従が容易になる（再生成 = AUTO 領域更新）
- 人手レビュー対象が「公式 URL の妥当性」「1 段落要約」のみに縮約され、レビュー時間と修正率が下がる見込み（A-7 中止条件で検証）
- recipe / concept で本プロジェクト独自の価値（ハマりどころ・実例・関係性）を表現することで、source 種別はインデックス的役割に純化される

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| ADR-003 の 3 部構成を維持し、補足解説の品質ガードを LLM プロンプトで強化 | 公式日本語版との重複が解消しない、人手レビューコストが下がらない |
| `source` 種別を完全廃止し、公式リンクは `entity` 種別で表現 | `entity` の責務が肥大化、ホワイトリストとの紐付けが間接的になる |
| 補足解説を `## 関連リンク`（wikilink リスト）に置き換える | 横断視点の表現力が失われる、既存記事の wikilink 再構築コスト大 |

**影響**:

- ADR-003（3 部構成）を `superseded by ADR-017` でマーク
- `vault/90_meta/markdown-rules.md` の 3 部構成強制を縮退仕様に書き換え
- `.claude/skills/llm-wiki-for-claude-code/references/three-part-rule.md` を縮退仕様に改訂
- `agent/validators/three_part_validator.py` を縮退仕様の検証に書き換え（補足解説必須から AUTO 領域 + 公式リンクのみ必須へ）
- Phase 2-A で対象 10 本（cli 6 + hooks 4）を縮退書き換え + AUTO 領域導入
- `transclusion_validator` は継続適用（100 文字一致禁止）

---

## ADR-018: LLM バックエンドの Claude Code 経由化（`ClaudeCodeBackend` 追加）

**ステータス**: accepted（2026-05-08）— ADR-019 完了に伴う empirical 検証 PASS（73.33s で `ClaudeCodeBackend.invoke` 実走を確認）により `proposed` から昇格

**コンテキスト**:

Phase 2-A で実装した `AnthropicBackend`（`agent/orchestration/llm.py:101-169`）は `ANTHROPIC_API_KEY` 必須・**従量課金**前提。利用者は Claude Code Max プランを契約済みで定額枠を活用したい。想定運用は「Claude Code 関連情報を **ローカル cron / launchd** で定期取り込み → Obsidian で閲覧 → 将来は Web 公開へ同期」というローカル運用主軸であり、API コスト線形増加の回避が望ましい。

`acceptance-test-report.md §6.1`（Phase 2-A 受入れ）で方針転換が起票され、検討事項 5 点（§6.2）が別セッション課題として残置されていた。

**決定**:

- `agent/orchestration/llm.py` に **3 つ目のバックエンド** として `ClaudeCodeBackend` を追加し、`claude-agent-sdk`（Anthropic 公式 Python パッケージ）経由で Claude Code (Max プラン) に LLM を委譲する
- `WIKI_LLM_BACKEND` の許容値を `stub|anthropic|claude-code` の 3 値に拡張
- 既定値は **段階展開**:
  - empirical 検証 PASS 前: `stub`（既存維持）
  - empirical 検証 PASS 後: `claude-code` 昇格（別 PR）
- `AnthropicBackend` は **CI / API 利用者向け** の選択肢として残置（廃止しない）
- `StubBackend` はテスト DI / オフライン用途で残置
- `claude-code` 選択時は `ANTHROPIC_API_KEY` を読まない（mock テストで検証）
- `ClaudeCodeBackend.__init__` で `shutil.which("claude")` により `claude` バイナリの PATH 存在を確認、不在時は `ConfigurationError`（exit code 3）でフェイルファスト
- SDK 例外 / 認証エラーは `LLMInvocationError` にラップ（既存例外階層を流用、新規例外なし）
- `cache_system` フラグは noop（Claude Code 内部に caching を委譲、`metrics.md` への記録時は `N/A`）
- リトライ戦略は `AnthropicBackend` と同一（1 回リトライ、再失敗で `LLMInvocationError`）

**理由**:

- Max プラン定額枠の活用により、記事数増加に伴う API コスト線形増加を回避できる
- 既存 `LLMBackend` Protocol に並列実装を追加するだけで、`StubLLMClient` / `AnthropicBackend` には変更が入らず、Phase 2-A の規約・テスト 159 件 PASS に影響しない
- `AnthropicBackend` を残置することで、CI / Max プラン非加入者でも `agent regenerate` を選択肢として実行可能
- 認証情報の管理は `claude` CLI（`~/.claude/`）に委譲され、本プロジェクトに認証情報を持ち込まない（セキュリティ・運用コスト共に有利）

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| `AnthropicBackend` を削除し `ClaudeCodeBackend` に統一 | CI 環境では Max プラン認証が一般に通らない、API 利用者向けの選択肢を失う |
| `AnthropicBackend` を既定のまま維持し `claude-code` を補助選択肢に | ローカル運用主軸（Max プラン定額活用）の動機を満たさない、コスト最適化が後手に回る |
| `subprocess` で `claude -p <prompt>` を直接呼ぶ（SDK を使わない） | 例外・usage 抽出・型安全性で SDK に劣る、SDK 仕様変動に追従しづらい |
| caching 効果を `cache_system=True` で `claude-code` 側にも厳密に積む | Claude Code が独自にプロンプトキャッシュを管理する設計のため、明示制御は不確定。`metrics.md` の caching 計測は `AnthropicBackend` 側に残置する方針 |

**影響**:

- `pyproject.toml` に `claude-agent-sdk>=0.1.77` を追加、`uv.lock` 更新
- `.env.example` に `WIKI_LLM_BACKEND=claude-code` の例とコメントを追記
- `tests/unit/test_llm_claude_code.py` 新規追加（mock 経由で 21 件、テスト総数 159 → 180）
- `agent/orchestration/llm.py` の `make_backend()` に `claude-code` 分岐と 3 値表記の不明値メッセージ
- empirical 検証 PASS 後の別 PR で:
  - `make_backend()` 既定値を `claude-code` に昇格
  - `CLAUDE.md` の `agent regenerate` 運用ガード注記を削除（A-1-6 解消）
  - `vault/90_meta/metrics.md` に Phase 2-A 対象 16 本の修正率を記録（A-6-2 / A-6-3 解消）
  - 本 ADR の Status を `accepted` に昇格
- CI 環境では `WIKI_LLM_BACKEND=anthropic` または `stub` を明示する運用方針（CI 設定変更は本 ADR では行わない）
- `claude-agent-sdk` 内部例外型の精緻な絞り込みは Phase 2-B に持ち越し（`AnthropicBackend` の `except Exception` 絞り込みと並行実施）

**関連 ADR**: ADR-015（AUTO マーカー）/ ADR-016（Phase 2 pivot）/ ADR-017（公式 source 縮退仕様）を踏襲。

---

## ADR-019: `agent regenerate` の AUTO 領域経路で LLM を実呼び出しする（noop stub の解消）

**ステータス**: accepted（2026-05-08）— 実装完了。テスト 202 件 PASS / `agent validate --all` 16 本 PASS / `agent lint --all` 違反 0 / empirical で `WIKI_LLM_BACKEND=claude-code agent regenerate --force` が 73.33s で AUTO 領域を実 LLM 再生成することを確認

**コンテキスト**:

ADR-015（AUTO マーカー）/ ADR-017（source 縮退仕様）の設計意図は「AUTO 領域は取込み元の最新内容に基づき LLM が再生成する」だった。しかし Phase 2-A で実装された `agent/orchestration/regenerate.py` は、`auto_section_managed=true` 経路で次の noop stub に留まっている:

```python
# regenerate.py:100-105
# Phase 2-A 時点では「再生成」プロンプトは AUTO 領域単位の生成に未対応のため、
# スタブ動作のみサポート（実 LLM 統合での AUTO 領域差分生成は Phase 2-B）。
new_inner_contents = ["\n".join(r.inner_lines) for r in regions]
replace_auto_regions(target_path, new_inner_contents)
```

この実装は「AUTO 領域を抽出してそのまま書き戻す」だけで、`llm.generate` を呼ばない。結果として:

- Phase 2-A 縮退仕様（公式 source 11 + recipe 5 = 16 本すべて `auto_section_managed: true`）に対して、`agent regenerate` は **どの LLM バックエンドが選ばれていても LLM を一度も呼ばない**
- ADR-018 で追加した `ClaudeCodeBackend` の empirical 検証（`WIKI_LLM_BACKEND=claude-code agent regenerate ...`）が、表面上 exit 0 / 所要時間ログ条件を満たしても、`ClaudeCodeBackend.invoke` を実走させられない（2026-05-08 の検証で発覚）
- 既存の `regenerate.py:117` の `load_prompt("source-regenerate")` 経路は AUTO マーカー無しの旧構造ページ専用となり、Phase 2-A 縮退仕様（全 source ページが AUTO マーカー導入済み）と矛盾し **実質デッドコード**

「Phase 2-B で実装」とコメントで先送りされていたが、この穴を残したままでは ADR-018 の empirical 検証が成立せず、Phase 2-A の真の完了条件を満たせない。

**決定**:

- `agent regenerate` の `auto_section_managed=true` 経路で **LLM を実呼び出しする**（noop stub を解消）
- AUTO マーカー仕様（`vault/90_meta/auto-marker-spec.md`）を拡張し、各 AUTO 領域に **`purpose` メタデータ** を付与可能にする
- 構文: `<!-- AUTO:START purpose=summary-1-paragraph -->` / `<!-- AUTO:START purpose=recipe-tldr -->` 等。`purpose` 省略時は領域種別に応じた既定値（source 種別なら `summary-1-paragraph`、recipe 種別なら配置順から推論）
- `purpose` は per-region プロンプトテンプレート（`agent/prompts/auto-region/<purpose>.md`）のディスパッチキーとして機能
- 再生成フロー:
  1. fetch source（HTTP）
  2. content_hash 比較で **冪等性早期 return は維持**（`existing.source_version == fetch.source_version` なら no-op、これは正しい挙動）
  3. 不一致 or `--force` 指定時に AUTO 領域を抽出し、各領域の `purpose` から prompt テンプレートを選択して `llm.generate` を呼び出す
  4. 生成結果を `replace_auto_regions` で書き戻し、領域外バイト一致は writer が構造的に保証
  5. frontmatter の `last_updated` / `source_version` / `fetched_at` を更新
- 強制再生成フラグ `--force` を `agent regenerate` CLI に追加（content_hash 一致時も LLM を呼ばせる経路。empirical 検証や手動再生成で使う）
- 既存 16 本の AUTO マーカーに `purpose` を後付けする後方互換マイグレーション（`purpose` 省略時に種別 + 順序から既定値を推論する fallback を実装）
- 旧 `load_prompt("source-regenerate")` 経路（`regenerate.py:117` 以降のフルファイル再生成）は **削除**。Phase 2-A 縮退仕様で AUTO マーカー必須になったため不要

**理由**:

- ADR-015 / ADR-017 の設計意図に沿った「再生成」コマンドとして機能させる
- ADR-018 の empirical 検証が `agent regenerate` で成立する（smoke test を別途用意する応急処置を回避）
- `purpose` メタデータ方式は、種別追加のたびに orchestrator にハードコード分岐を増やすのを回避できる（プロンプトテンプレを足すだけで新種類に対応）
- content_hash 早期 return を維持することで、変化なし時は LLM コストゼロを保つ（運用上重要）
- `--force` で empirical 検証や trouble-shooting 時に LLM を強制起動でき、テスト容易性が上がる

**不採用案**:

| 案 | 却下理由 |
|----|---------|
| noop stub を維持し、別 smoke コマンドで `ClaudeCodeBackend` を検証 | `regenerate` が「再生成」として機能しないままとなる。デッドコード（`source-regenerate` プロンプト）を抱え続ける。設計意図と実装の乖離を温存する応急処置 |
| AUTO 領域に `purpose` を付けず、ファイル種別＋配置順で全プロンプトを内部マップに固定 | 種別追加・領域構成変更のたびに orchestrator のハードコードを更新する必要があり、Phase 2-B での派生種別（concept/entity/synthesis）展開時に技術的負債化する |
| `agent regenerate` を廃止し `agent ingest` に統合 | ingest（新規取込み）と regenerate（既存ページ更新）は冪等性ロジックや frontmatter 保持規則が異なる。統合すると ingest が肥大化し、ADR-015 のコマンド分離設計と矛盾 |
| `purpose` ではなく per-region 任意 prompt テキストを AUTO マーカーコメントに直書き（`<!-- AUTO:START prompt="..." -->`） | プロンプトが Wiki ページに散在し、改善のたびに 16 本以上を一括編集する運用負荷。プロンプトテンプレは集中管理（`agent/prompts/`）が筋 |
| `--force` を設けず、source_version frontmatter を手動クリアして強制再生成させる | 操作手順が煩雑、誤って frontmatter を破壊するリスク。CLI フラグの方が安全かつ明示的 |

**影響**:

- `agent/orchestration/regenerate.py` 大幅改修（AUTO 領域経路で LLM 呼び出し、`--force` 追加）
- `agent/prompts/auto-region/<purpose>.md` 新規作成（最低限 `summary-1-paragraph.md` / `recipe-tldr.md` / `recipe-steps.md` の 3 本）
- `vault/90_meta/auto-marker-spec.md` 改訂（`purpose` 構文・既定値推論ルール・purpose 一覧表）
- `vault/90_meta/_schemas/frontmatter.schema.json` への影響は無し（frontmatter ではなく AUTO マーカー本体の構文拡張のため）
- 既存 16 本の AUTO マーカーに `purpose` を後付けするマイグレーション（一括 sed + レビュー）
- `agent/writers/markdown_writer.py` の `extract_auto_regions` 拡張（`purpose` 属性の parse、`AutoRegion` dataclass に `purpose: str | None` を追加）
- 既存 `agent/prompts/source-regenerate.md` および `regenerate.py:117` 以降のフルファイル再生成経路を削除
- `tests/unit/test_auto_markers.py` に `purpose` 構文テスト追加
- `tests/unit/test_runner.py` / 統合テストに AUTO 領域 LLM 経路の mock テスト追加
- ADR-018 の empirical 検証は **本 ADR の実装完了後に再実施**（`acceptance-test-report.md §2` および `empirical-checklist.md` の手順は変更不要、再実行で `ClaudeCodeBackend.invoke` が実走する想定）
- Phase 2-A の真の完了条件: 本 ADR 実装 PASS + ADR-018 empirical 検証 PASS で、CONDITIONAL_PASS から正式 PASS へ昇格

**関連 ADR**: ADR-006（AUTO 導入方針）/ ADR-015（AUTO 構文確定）/ ADR-017（公式 source 縮退仕様）/ ADR-018（`ClaudeCodeBackend`）。

---

## 未決定事項

以下は Phase 2 以降に持ち越し:

- AUTO セクションマーカーの厳密な構文規約（Phase 2 で `vault/90_meta/auto-marker-spec.md` として確定）
- 派生種別（concept/entity/synthesis）テンプレートの詳細（Phase 2）
- `comparison` 自動生成プロンプト（Phase 3）
- セマンティック検索層の選定（200ページ超で検討）
- Karpathy gist の原文 verbatim 確認（公開物として残す段階で再確認）

## 更新履歴

- 2026-05-05: 初版作成。アイデアファイル（`docs/ideas/20260505-llm-wiki-for-claude-code.md`）から ADR-001〜009 を抽出。
- 2026-05-05: ADR-014 追加（Slash Command と Skill を分離）。公式ドキュメント確認の結果、Skill 内 `commands/` サブディレクトリは公式仕様外と判明したため、ADR-012 を改訂し構造の詳細を ADR-014 に委譲。
- 2026-05-05: ADR-001 訂正（Karpathy A/B/C を運用案ではなくレイヤー構造として正しく解釈、二次資料の Rezvani Medium 記事に依拠）。ADR-011（ページ種別5種類）と ADR-012（Skill パッケージング）を Karpathy gist + Rezvani Medium 記事の精読を踏まえて追加。Karpathy gist の原文 verbatim 引用は Phase 1 着手時に再確認する未決定事項として記録。
- 2026-05-05: Phase 1 実装着手。ADR-010（Python 3.12+ / uv / pytest / ruff / mypy）と ADR-013（Skill `references/` はシンボリックリンクで同期）を追加。
- 2026-05-06: Phase 2-A 着手。公式日本語版発覚（Phase 1 受入れテスト時）を受けて Phase 2 を A/B 分割し、付加価値主軸を「コミュニティ知見整理 + ユースケース志向 recipe」に pivot。ADR-015（AUTO マーカー構文）/ ADR-016（Phase 2 pivot）/ ADR-017（公式 source 縮退仕様）を追加。ADR-003 を superseded by ADR-017 でマーク。
- 2026-05-08: ADR-018 起票（proposed）。Phase 2-A 受入れ §6.1 の方針転換を受けて、`ClaudeCodeBackend` を `LLMBackend` Protocol の 3 つ目の実装として追加し、Max プラン定額枠でのローカル日次自動化を主用途とする。`AnthropicBackend` は CI / API 利用者向けに残置、既定値は段階展開で empirical 検証 PASS 後に `claude-code` へ昇格予定。
- 2026-05-08: ADR-018 の empirical 検証実施時、`agent regenerate` の `auto_section_managed=true` 経路が noop stub であり LLM を呼ばないことが発覚。ADR-019 を起票（proposed）し、AUTO 領域経路で LLM を実呼び出しする設計に切り替え、AUTO マーカーに `purpose` メタデータを導入。Phase 2-A の真の完了条件は ADR-019 実装 + ADR-018 empirical PASS とする。
- 2026-05-08: ADR-019 実装完了。AUTO マーカー `purpose` 属性パーサ追加 / 旧 `source-regenerate` フルファイル経路削除 / 既存 16 本 (`source` 11 + `recipe` 5) のマーカー一括マイグレーション / `--force` フラグ追加 / `regenerate_source` の `make_backend()` 配線修正（`StubLLMClient()` ハードコードを撤去）。テスト 181 → 202 件 PASS、`agent validate --all` / `lint --all` 全 PASS、empirical で `claude-code` バックエンド経由の AUTO 領域再生成 73.33s 実走を確認。ADR-018 / ADR-019 を `accepted` に昇格。
