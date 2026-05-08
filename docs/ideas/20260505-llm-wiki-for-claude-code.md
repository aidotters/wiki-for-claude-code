# LLM-Wiki for Claude Code

> 作成日: 2026-05-05
> ステータス: verified（Phase 1 完了 / 検証日: 2026-05-06） / **Phase 2 以降は pivot を反映**（2026-05-06） / **Phase 2-A 実 LLM 統合完了**（2026-05-08、`ClaudeCodeBackend` 既定昇格 + AUTO 領域実 LLM 化）
> 優先度: 未定
> 関連 plan: `~/.claude/plans/synchronous-tickling-dragon.md`（Phase 2 pivot 提案）

## 概要

Andrej Karpathy 氏が提唱した「LLM-Wiki」のコンセプトを **Claude エコシステム**（Claude Code を中核に、Claude Design / Skills / Agent SDK 等を含む）というドメインに適用した、人間と LLM が共同で読み書きする日本語 Wiki。LLM エージェントが定期的に **コミュニティに散らばる実践知（英語コミュニティ + 個人発信）** を取得・整理し、横断視点で再構成（ユースケース別 Tips / セットアップ手順 / チートシート等）したものを人間レビューを経てマージすることで、Claude エコシステム最新の使い方・実践知を継続的に参照できる場を提供する。

> **pivot 経緯（2026-05-06）**: 当初は「公式英語ドキュメントの日本語素訳 + 補足」を主軸としていたが、Phase 1 受入れテスト時に **公式日本語版（`code.claude.com/docs/ja/*`）の存在が確認** され、素訳の付加価値が毀損された。本来の付加価値は「コミュニティ実践知の自動整理 + 横断視点での再構成」にあると再定義し、公式 source は縮退仕様に変更、コミュニティ source 取り込みを Phase 2 に前倒し、ユースケース別 `recipe` 種別を Phase 2-A で先行検証する方針に転換した。詳細は plan ファイル `~/.claude/plans/synchronous-tickling-dragon.md` を参照。

## 背景

### 現状の課題

- **コミュニティ実践知の追従困難**: Reddit, GitHub Discussions, awesome-claude-code 系リポジトリ、Anthropic ブログ、X、Karpathy/Rezvani 等の個人発信に有用な実践ノウハウが圧倒的に早く・多く流れるが、量が多く・多角的で、個人が継続的に追いきるのは困難。
- **英語コミュニティ知見の言語障壁**: 上記の有用情報は英語コミュニティが中心で、日本語話者には届きにくい。
- **公式リファレンスとユースケースのギャップ**: `code.claude.com/docs/ja/*` の公式日本語ドキュメントはフラットなリファレンス構造で、「初期セットアップ手順」「ユースケース別 Tips」「機能横断のチートシート」といった目的志向の構成が存在しない。
- **既存日本語情報の陳腐化**: 個人ブログや Zenn/Qiita 記事は単発で更新されにくく、半年経つと内容が古くなる。
- **LLM が参照可能な構造化情報の不足**: ユーザーが Claude 自身に「最新の hooks 仕様は？」「Claude Code で X するレシピは？」と聞いたとき、横断視点で構造化された情報が少なく、回答品質が安定しない。
- **(pivot 前の前提だった課題、現在は解決済み)** ~~公式ドキュメントは英語のみで日本語素訳の付加価値があった~~ → 公式日本語版（`code.claude.com/docs/ja/*`）の存在を 2026-05-06 に確認、素訳の付加価値は無効化された。

### 解決したいこと

- **Claude エコシステム**（Claude Code + Claude Design + Skills + Agent SDK 等）における **コミュニティ実践知の自動整理 + 横断視点での再構成** を、日本語で継続的に参照できる Wiki として構築する。
- LLM エージェントによる定期更新で「常に最新」を担保する（人間レビュー必須）。
- 公式リファレンスにない **目的志向のドキュメント**（ユースケース別 Tips = `recipe`、セットアップ手順 = `guide`、機能横断のチートシート = `cheatsheet`）を派生種別として整備する。
- 人間も LLM も読みやすい構造（プレーン Markdown + Wikilinks）で、Claude に質問した際に引かれる構造化インデックス（A-3 用途）も同時充足する。
- 公式 source は **縮退仕様**（タイトル + 1 段落要約 + 公式リンク + AUTO マーカー）として「公式へのインデックス」役に徹し、付加価値は派生ページ（concept / entity / synthesis / recipe / guide / cheatsheet / comparison）に集中投下する。

## 解決策

### アプローチ: ドメイン特化コンパイル型 Wiki

Karpathy 氏の LLM-Wiki gist が提唱する **「コンパイル型知識ベース」** の構造（ページ種別ごとの分離、相互参照維持、LLM 主導の帳簿管理）を、**Claude Code ドメインに特化した日本語公開 Wiki** に適用する。さらに、Reza Rezvani 氏の Medium 記事（2026-04）が提示する **Claude Code Skill としての実装パッケージング** の発想を採用しつつ、Anthropic 公式ドキュメントとの整合性を踏まえて構造を改訂する。具体的には、**スラッシュコマンドは `.claude/commands/` のトップレベル**、**Skill は規約・テンプレート・hook の context-aware ロード領域**として分離配置する（Skill 内 `commands/` サブディレクトリは公式仕様外のため不採用）。詳細は [`docs/core/decisions.md` ADR-014](../core/decisions.md) を参照。

#### Karpathy 原案の3レイヤー構造を採用

Karpathy gist は Wiki を以下の **3つのレイヤー** に分離する設計を提案している:

- **Raw Sources 層** — 不変の一次情報（記事、ドキュメント、論文）。LLM は読むのみ
- **Wiki 層** — LLM が生成・維持する Markdown ページ群（要約・エンティティ・概念・比較・統合）
- **Schema 層** — Wiki の構造とワークフローを LLM に伝える設定（`SKILL.md` / `CLAUDE.md` 等）

本プロジェクトでは Raw Sources 層を「公式ドキュメント URL + コミュニティ記事のスナップショット」、Wiki 層を `vault/{sources, concepts, entities, comparisons, syntheses}/`、Schema 層を `.claude/skills/llm-wiki-for-claude-code/`（規約・テンプレート・hook）と `.claude/commands/`（Wiki 操作のスラッシュコマンド）の組合せに対応させる。

#### Karpathy/Rezvani 原案からの差分（独自要素）

| 観点 | Karpathy/Rezvani 原案 | 本プロジェクト |
|------|---------------------|--------------|
| 主たる利用者 | 自分自身 / チーム（セカンドブレイン） | 不特定の日本語話者（公開 Wiki） |
| ソースの性質 | 自分が選んだ任意の一次資料 | Claude Code ドメイン限定のホワイトリスト済みソース |
| 価値の源泉 | 個人の問いに答える統合知識 | 言語の壁を越えた最新情報の継続提供 |
| 編集者 | LLM がほぼ100%書く | LLM が PR 提案、人間レビュー必須 |
| 著作権配慮 | 言及なし | Anthropic Usage Policy 遵守のため `source` 種別に「要約 + リンク + 補足」3部構成を強制 |
| 自動化 | 個人の手動 ingest が中心 | GitHub Actions による週次自動更新を前提（Phase 3） |

#### コンテンツの2系統 × ページ種別（pivot 後: 5種別 → **8種別**）

ソース系統（公式 / コミュニティ）とページ種別（pivot 後 8 種類）の2軸で分類する:

- **ソース系統**: 公式ドキュメント由来（縮退仕様）/ コミュニティ知見由来（Phase 2-A から本格導入）
- **ページ種別**:
  - `source`（取込み元の要約 / pivot 後は **縮退仕様** = タイトル + 1段落要約 + 公式リンク + AUTO マーカー）
  - `concept`（複数 source 横断の概念）
  - `entity`（ツール・コマンド・人物・モデル・機能）
  - `comparison`（競合アプローチ比較 / Phase 3 で自動生成）
  - `synthesis`（`/wiki-query` 結果の保存）
  - **`recipe`（ユースケース別 Tips 集 / Phase 2-A で先行導入）**
  - **`guide`（ハウツー / セットアップ手順 / Phase 2-B 以降）**
  - **`cheatsheet`（機能横断のチートシート / Phase 3 以降）**

この2軸設計により、「公式ドキュメントの単純な日本語化」ではなく、**コミュニティ実践知 × 横断視点の派生ページ群**（特に `recipe` / `guide` / `cheatsheet`）が Wiki の本体価値を担う構造になる。`source` は派生ページの引用先 / 公式へのインデックスとしての役割に絞る。

### 設計方針

1. **Vault = Repo**: Obsidian Vault と Git リポジトリを同一ディレクトリに統合。同期問題を排除する。
2. **ページ種別ベースの構造化**: Karpathy 原案の5種別（source / concept / entity / comparison / synthesis）に加え、pivot 後は **目的志向の派生種別**（`recipe` / `guide` / `cheatsheet`）を追加。1 source から複数の派生ページが育つコンパイル構造に、ユースケース別の実用ドキュメントを織り込む。
3. **`source` 種別の縮退仕様**（pivot 後改訂）: Anthropic Usage Policy / 公式日本語版との重複回避のため、`type: source` のページは **「タイトル + 1 段落要約 + 公式リンク + AUTO マーカー」** に縮退。AUTO 領域は自動メンテし、人手が独自価値を付加する場合は派生ページ（`concept` / `recipe` 等）を新設して引用形式で記述する。
4. **規約先行**: Phase 1 で frontmatter 規約・Markdown 制約・情報源ホワイトリスト・利用規約整理を確立してから、コンテンツ生成・自動化に進む。
5. **3操作 + 再生成**: Karpathy/Rezvani の `ingest` / `query` / `lint` に加えて、本プロジェクト独自の `regenerate`（既存 source の再フェッチと派生ページ更新提案）を Phase 1 から実装する。
6. **AUTO セクションマーカー**: 自動生成領域（`<!-- AUTO:START --> ... <!-- AUTO:END -->`）と人手編集領域を明示的に分離。自動 PR が人手編集を上書きする事故を防ぐ（Phase 2 で導入）。
7. **Slash Command + Skill + 環境非依存ロジック**: 4操作（ingest/regenerate/lint/query）は明示起動の `.claude/commands/wiki-*.md` に配置し、規約・テンプレート・hook は context-aware にロードされる `.claude/skills/llm-wiki-for-claude-code/` に集約する（Skill 内に `commands/` サブディレクトリは置かない、ADR-014）。同時に `agent/{fetchers, writers, validators, orchestration, runners}` を環境非依存ロジック層として実装し、Slash Command 層と GitHub Actions の双方から呼び出す。
8. **信頼度スコア（confidence）**: 全ページに `confidence: 0.0-1.0` を必須化し、`lint` で 0.5 未満をフラグする。自動生成記事の品質ガードとなる。
9. **portability 重視の Markdown**: 標準 Markdown + Wikilinks のみ。Obsidian の Dataview や Callout など独自記法は禁止（Karpathy 原案は Dataview を推奨するが、将来 GitHub Pages 等で公開する際の変換コストを下げるため意図的に不採用）。
10. **段階的展開（2軸）**: 「ページ種別軸（コンパイル深度）」と「対象ソース軸（カバレッジ）」の2軸で段階的に拡張する。

### 代替案と比較

| 案 | メリット | デメリット | 採否 |
|----|---------|-----------|------|
| 折衷案: ドメイン特化コンパイル型 Wiki（採用） | 公開 Wiki の目的を維持しつつ Karpathy のコンパイル機構を取り入れる | 設計複雑度が高い | 採用 |
| Karpathy/Rezvani 原案そのまま（個人 Vault + LLM 主導書込み） | 設計が明快、原典忠実 | 公開 Wiki としては引用必須・著作権配慮が不十分 | 不採用 |
| 公式ドキュメントの単純な要約集約（ページ種別なし、現状寄り） | 実装が簡単 | コンパイル型の利点を失い、原典との乖離が大きい | 不採用 |
| 公式の全文翻訳 | ユーザーへの可読性が高い | 著作権・利用規約リスク、原文更新時の追従コスト | 不採用 |
| Vault と Repo を分離 | Obsidian 設定の自由度が高い | 同期問題が常時発生 | 不採用 |
| 実装基盤: ローカル Claude Code のみ | 開発が速い | マシン依存で常時更新を保証できない | 不採用（開発フェーズのみ採用） |
| 実装基盤: GitHub Actions + Agent SDK | クラウド実行・PR レビューと自然に統合 | 初期セットアップコスト高 | 採用（Phase 3 本番フェーズ） |
| 実装基盤: Anthropic Routines / Schedule | クラウド実行・Claude Code 環境 | 機能が比較的新しく長期運用基盤としては未知数 | 不採用（将来検討） |

## 実装する機能

### ロードマップ（2軸の段階的開発 / pivot 後改訂）

「ページ種別軸（コンパイル深度）」と「対象ソース軸（カバレッジ）」の2軸で段階的に拡張する。**Phase 2 は pivot により A/B 分割**:

| Phase | ページ種別軸 | 対象ソース軸 | 主な追加機能 |
|-------|------------|------------|-----------|
| **1** | `source` のみ | 公式 hooks/cli の2カテゴリ | 規約確立、Skill 雛形、ingest / lint / regenerate 操作、手動記事化10本（**pivot 後は縮退仕様で再評価**） |
| **2-A**（MVP） | `+ recipe`（先行検証 1 種別） | **公式 source 縮退**（既存10本） + **コミュニティ source 1系統**（awesome-claude-code 先行） | 実 Anthropic SDK 統合、AUTO マーカー最小実装、recipe 種別 5本生成、metrics 計測開始 |
| **2-B** | `+ concept`, `+ entity`, `+ synthesis` | コミュニティソース追加系統（GitHub Releases / Anthropic blog RSS / 個人発信）、Claude エコシステム拡張カテゴリ（claude-design / skills / agent-sdk） | `/wiki-query` 実装、AUTO マーカー全展開、verify-links CI 統合、fetcher 拡張 |
| **3** | `+ comparison`（自動生成）`+ guide` `+ cheatsheet` | コミュニティホワイトリスト（X/Twitter, Reddit, ブログ等の追加 fetcher 系統） | GitHub Actions 週次 cron、自動 PR、guide / cheatsheet 種別の本格導入、コミュニティ source 大規模展開 |

各 Phase 終了時の動作確認:

- **Phase 1**: `source` 種別記事10本、スラッシュコマンド `/wiki-ingest`, `/wiki-lint`, `/wiki-regenerate`（`.claude/commands/` 配下）がローカルで動作、再生成の冪等性確認 ✅ 2026-05-06 完了
- **Phase 2-A**: 実 LLM 統合動作、公式 source 10本が縮退仕様で安定、awesome-claude-code から 5本以上の community source 取込み、recipe 種別 5本以上が `published`、metrics に修正率記録
- **Phase 2-B**: 派生ページ（concept / entity / synthesis）が育ち、AUTO マーカーで人手編集領域が保護されることを確認、`/wiki-query` 動作、Claude エコシステム拡張カテゴリ整備
- **Phase 3**: 4週連続で自動 PR が立ち、人手修正率30%以下、guide / cheatsheet 整備、コミュニティ source の追加 fetcher 系統運用

### 機能1: Vault ディレクトリ構造（Phase 1 で確定）

ページ種別ベースの構造（Karpathy 流）に、ソース系統（公式 / コミュニティ）を `sources/` 配下のサブディレクトリで表現:

```
vault/
├── index.md                   # ナビゲーションの本体（Rezvani 由来）
├── log.md                     # 全操作の追記専用ログ（Rezvani 由来）
├── overview.md                # Wiki 全体の高レベル俯瞰（5回 ingest ごとに更新）
├── sources/                   # type=source: 取込み元の要約 + 公式リンク + 補足
│   ├── official/              # 公式ドキュメント由来
│   │   ├── cli/
│   │   ├── hooks/
│   │   ├── slash-commands/    # Phase 2 から
│   │   ├── mcp/               # Phase 2 から
│   │   ├── settings/          # Phase 2 から
│   │   └── sdk/               # Phase 2 から
│   └── community/             # Phase 3 から
│       ├── tips/
│       ├── workflows/
│       ├── integrations/
│       └── troubleshooting/
├── concepts/                  # type=concept: 複数 source 横断の概念（Phase 2 から）
├── entities/                  # type=entity: ツール・コマンド・人物（Phase 2 から）
├── comparisons/               # type=comparison: 競合アプローチ比較（Phase 3 で自動生成）
├── syntheses/                 # type=synthesis: クエリ結果の保存（Phase 2 から）
├── 30_drafts/                 # LLM 下書き（レビュー待ち）
└── 90_meta/                   # 情報源リスト、frontmatter 規約、用語集、更新ログ
```

### 機能2: ページ種別とテンプレート（pivot 後: 8 種別に拡張）

| 種別 | 配置 | 役割 | Anthropic Policy 適合 | 導入 Phase |
|------|------|------|---------------------|----------|
| `source` | `vault/sources/{official,community}/<category>/<slug>.md` | **縮退仕様**: タイトル + 1段落要約 + 公式リンク + AUTO マーカー（pivot 後改訂） | AUTO 領域は引用形式を遵守 | 1（公式）/ 2-A（コミュニティ） |
| `concept` | `vault/concepts/<Name>.md` | 複数 source 横断の概念（例: 「AUTO マーカー」「permission mode」） | 引用必須 | 2-B |
| `entity` | `vault/entities/<Name>.md` | ツール・コマンド・人物・モデル・機能（例: 「Bash tool」「Skills」「MCP server」「Claude Design」） | 引用必須 | 2-B |
| `comparison` | `vault/comparisons/<A>-vs-<B>.md` | 競合アプローチ比較（例: 「hooks vs Skills」） | 引用必須 | 3（自動生成） |
| `synthesis` | `vault/syntheses/<topic>.md` | `/wiki-query` の結果保存 | 引用必須 | 2-B |
| **`recipe`** | `vault/recipes/<use-case>.md` | **ユースケース別 Tips 集**（例: 「Claude Code セットアップ」「Hooks 入門」「MCP 連携 Tips」） | 引用必須（`sources` ≥ 2 件） | **2-A**（先行検証） |
| **`guide`** | `vault/guides/<topic>.md` | **ハウツー / 手順書**（recipe より系統的、初心者向け） | 引用必須 | 2-B 〜 3 |
| **`cheatsheet`** | `vault/cheatsheets/<topic>.md` | **機能横断のチートシート**（キーボードショートカット一覧、コマンド一覧、設定キー一覧等） | 引用必須 | 3 |

### 機能3: frontmatter 規約（Phase 1 で確定）

`type` で必須キーが切り替わる構造:

```yaml
---
# 共通必須（全種別）
title: "ページタイトル"
type: source | concept | entity | comparison | synthesis
confidence: 0.0-1.0          # lint で 0.5 未満をフラグ（Rezvani 由来）
sources: [vault/sources/official/hooks/pre-tool-use.md]  # 引用元 wikilink 配列
last_updated: 2026-05-05
stale: false
tags: [hooks, pre-tool-use]

# type=source のときのみ必須（Anthropic Policy 対応）
source_url: "https://docs.claude.com/..."
fetched_at: "2026-05-05T10:00:00Z"
source_version: null
claude_code_version: "1.5.0"

# 運用メタ
reviewer: "tak"
human_edited: true
status: draft | reviewed | published
auto_section_managed: false  # Phase 2 で AUTO マーカー導入時に true 化
---
```

### 機能4: `source` 種別の構成（pivot 後: **縮退仕様**）

Phase 1 では「要約 + 公式リンク + 補足解説」3部構成を強制していたが、**公式日本語版（`code.claude.com/docs/ja/*`）の存在確認（2026-05-06）により、補足解説の付加価値が薄くなった**。pivot 後は以下の縮退仕様に変更:

```markdown
## 概要 (要約)
<!-- AUTO:START -->
（タイトル + 1段落要約 = 公式ページの主旨を1段落で示す。AUTO マーカーで自動メンテ）
<!-- AUTO:END -->

## 公式ドキュメント
→ {公式日本語 URL}（最終確認: YYYY-MM-DD / 対象バージョン: X.Y.Z）
```

**3部構成の「補足解説」は廃止**。実際の利用例・ハマりどころ・横断視点の解説は **派生種別（`concept` / `recipe` / `guide` 等）に新ページとして起こし、`source` を引用元として参照する** 形に変更する。これにより:

- `source` は「公式へのインデックス」役に徹する → ハルシネーション混入面が縮小
- 付加価値は派生ページに集中 → 公式リファレンスにない目的志向ドキュメント（recipe / guide / cheatsheet）が Wiki の本体価値に
- 法務リスクは引用形式の派生ページで自然に局所化（全文転載の余地なし）

### 機能5: Slash Command + Skill 構造（Phase 1 で雛形、Phase 2/3 で機能追加）

Claude Code 公式仕様に整合する形で、Wiki 操作の **Slash Command**（明示起動）と、規約・テンプレートを context-aware に提供する **Skill** を分離配置する（ADR-014）:

```
.claude/
├── commands/                       # Wiki 操作のスラッシュコマンド（明示起動）
│   ├── wiki-ingest.md              # 新ソース取込み（Phase 1）
│   ├── wiki-regenerate.md          # 既存 source の再フェッチ + 派生更新提案（Phase 1）
│   ├── wiki-lint.md                # 矛盾・孤立・陳腐化検出（Phase 1）
│   └── wiki-query.md               # Wiki 横断検索 → synthesis 保存（Phase 2 で追加）
└── skills/
    └── llm-wiki-for-claude-code/   # 規約・テンプレート・hook の context-aware 提供
        ├── SKILL.md                # Skill エントリ（Wiki ページ編集時に自動ロード）
        ├── references/
        │   ├── schema.md           # frontmatter 仕様 + ページ種別定義
        │   ├── page-templates.md   # 5種別のテンプレート
        │   ├── three-part-rule.md  # source 種別の3部構成 + Anthropic Policy 規約
        │   ├── sources-whitelist.md # 情報源ホワイトリスト（vault/90_meta/ から導出）
        │   └── lint-rules.md       # 健全性チェック仕様
        └── hooks/
            └── session-start.md    # 起動時に index.md / log.md 直近10件をロード
```

> Skill 内に `commands/` サブディレクトリは置かない。Anthropic 公式ドキュメント（claude-code/skills.md）によれば Skill は `SKILL.md` + 同階層のサポートファイルの flat 構造が前提で、サブコマンドを束ねる仕組みは公式仕様に存在しない。Rezvani 記事のレイアウト依存を排し、公式仕様に整合させる（ADR-014）。

#### コマンド体系

| コマンド | 機能 | 導入 Phase |
|---------|------|----------|
| `/wiki-ingest <official-url \| community-path>` | 新ソースを取込み、`source` ページ生成、関連派生ページ更新提案 | 1（公式のみ）、3（コミュニティ） |
| `/wiki-regenerate <source-path>` | 既存 source を再フェッチし、派生 concept/entity の更新を提案 | 1 |
| `/wiki-lint` | 矛盾検出、信頼度監査、孤立ページ検出、`claude_code_version` 古いものの検出 | 1 |
| `/wiki-query <question>` | Wiki 横断検索 → 必要なら `synthesis` ページとして保存 | 2 |

### 機能6: 環境非依存ロジック層（Phase 1 で雛形、Phase 3 で本格実装）

Slash Command / Skill とは別に、フェッチや検証ロジックを言語実装として配置。スラッシュコマンドからも GitHub Actions からも同じロジックを呼び出す:

```
agent/
├── fetchers/             # 情報収集（HTTP, RSS, GitHub API 等）
├── writers/              # Markdown 生成・更新、frontmatter シリアライズ
├── validators/           # frontmatter, 3部構成, 連続100文字一致, lint ルール
├── orchestration/        # ingest / query / lint / regenerate のユースケース実装
└── runners/
    ├── local             # Skill から呼ばれるラッパ
    └── action            # GitHub Actions エントリポイント（Phase 1 ではスタブ）
```

### 機能7: AUTO セクションマーカー（Phase 2 で導入）

自動生成領域と人手編集領域を分離:

```markdown
## 概要
<!-- AUTO:START -->
（エージェントが上書きする領域）
<!-- AUTO:END -->

## 補足解説 (日本語)
（人手編集領域。エージェントは触らない）
```

### 機能8: GitHub Actions 自動化（Phase 3）

- 週次 cron で `agent/runners/action` を起動
- Claude Agent SDK で `/wiki-regenerate` 相当を全 source に対して実行 + 必要に応じて新規コミュニティ source の `/wiki-ingest`
- 変更があれば自動 PR 作成
- PR テンプレに変更ソース・diff サマリ・`claude_code_version` を含める
- CODEOWNERS でレビュー担当を自動割当

## 受け入れ条件

### Phase 1: 規約確立 + Skill 雛形 + 公式 hooks/cli の `source` 種別10本

> **Phase 1 ステータス**: 2026-05-06 verified（CLAUDE.md「Phase 1 ステータス」節と整合）。

#### 構造とドキュメント
- [x] `vault/` ディレクトリ構造（ページ種別ベース）が作成され、Obsidian Vault として認識される
- [x] `vault/index.md`, `vault/log.md`, `vault/overview.md` の雛形が配置されている
- [x] `vault/90_meta/sources.md` に情報源ホワイトリストが確定（Phase 1 では公式 docs.claude.com 系のみ。2026-05-06 に日本語版 `code.claude.com/docs/ja/*` への切替を反映）
- [x] `vault/90_meta/frontmatter-spec.md` に frontmatter 規約（`type` 別必須キーを含む）が確定
- [x] `vault/90_meta/markdown-rules.md` に Markdown 制約（標準 MD + Wikilinks のみ、Dataview 禁止、`source` 種別の3部構成強制）が記載（**Phase 2-A の ADR-017 で縮退仕様に superseded**）
- [x] `vault/90_meta/license-notes.md` に Anthropic Usage Policy・docs.claude.com の利用規約整理が記載

#### Skill と環境非依存ロジック
- [x] `.claude/skills/llm-wiki-for-claude-code/SKILL.md` が配置され、Claude Code から認識される
- [x] スラッシュコマンド `/wiki-ingest`, `/wiki-regenerate`, `/wiki-lint`（`.claude/commands/` 配下）がローカルで動作する
- [x] Skill `hooks/session-start.md` が起動時に `index.md` と `log.md` 直近10件を自動ロードする
- [x] `agent/orchestration` の最小実装で `regenerate` ユースケースが冪等動作（意味のある差分のみ出る）
- [x] `agent/runners/action` のスタブが配置されている（Phase 3 用）

#### コンテンツ
- [x] `vault/sources/official/hooks/` と `vault/sources/official/cli/` に `type: source` の記事が合計10本生成済み（hooks 5 + cli 5、Phase 2-A で cli に keybindings 1本追加して計 11 本）
- [x] 全 `source` 記事に必須 frontmatter（`type`, `confidence`, `sources`, `source_url`, `fetched_at`, `claude_code_version`, `status` 等）が揃っている
- [x] 全 `source` 記事が「要約 + 公式リンク + 補足」の3部構成を満たしている（**Phase 2-A の ADR-017 で縮退仕様に書換、当受入条件は superseded**）
- [x] `/wiki-lint` 実行で全件 confidence ≥ 0.7、3部構成違反0件、孤立ページ0件（Phase 1 受入時。Phase 2-A pivot 後は drift 検出 2本を `status: draft` + `stale: true` で扱い、Phase 2-A の縮退仕様適用で解消）
- [x] Obsidian で Wikilinks と `[[wikilinks]]` がリンクとして機能する

### Phase 2-A（MVP / pivot 後新規）: 実 LLM 統合 + 公式 source 縮退 + コミュニティ source 1系統 + recipe 種別先行

#### 実 Anthropic SDK 統合
- [x] `agent/orchestration/llm.py` がスタブから実 LLM 呼び出しに置換、Sonnet 4.6 既定、prompt caching 有効（`AnthropicBackend` 側、`ClaudeCodeBackend` 追加で 3 系統）
- [x] `WIKI_LLM_BACKEND=stub|anthropic|claude-code` の切替フラグ動作（既定は `claude-code`、ADR-018 で確定）
- [x] `agent regenerate` の本番運用ガード（CLAUDE.md 注記）が解除されている（2026-05-08、ADR-018 / ADR-019 完了に伴い）

#### 公式 source 縮退（既存10本 → 11本一括処理）
- [x] `vault/sources/official/{cli,hooks}/*.md` 11本（cli 6 + hooks 5）が縮退仕様（タイトル + 1段落要約 + 公式リンク + AUTO 領域）に書き換え済み
- [x] 全11本が `confidence ≥ 0.7`, `status: published`, AUTO マーカー反映済み
- [x] 3部構成強制ルール（`vault/90_meta/markdown-rules.md`）が縮退仕様に書き換え済み（ADR-017）
- [x] drift 記事 2本（`cli/installation.md`, `hooks/overview.md`）が縮退仕様適用で drift 解消
- [x] 公式 6 カテゴリ展開（旧計画の 4 カテゴリ × 5本追加）は **撤回**

#### コミュニティ source 1系統取り込み（awesome-claude-code 先行）
- [ ] ~~`vault/90_meta/sources.md` のホワイトリストに `awesome-claude-code` が追加済み~~ → **A-7 中止条件発動（2026-05-08）**: ライセンスが CC BY-NC-ND 4.0 と判明し A-3 を停止、`enabled: false` 設定。Phase 2-B B-3 で別系統に切替予定（fetcher 実装は流用可能な状態で残置）
- [ ] ~~`vault/sources/community/awesome-claude-code/` 配下に最低 5本の `type: source` 記事~~ → **同上、Phase 2-B 送り**
- [x] `vault/90_meta/license-notes.md` に awesome-claude-code のライセンス整理記載（CC BY-NC-ND 検出を含む）

#### recipe 種別先行検証
- [x] `vault/90_meta/frontmatter-spec.md` に `recipe` 種別の必須キー追加（共通 + `use_case`, `sources` ≥ 2 件）
- [x] `vault/90_meta/_schemas/frontmatter.schema.json` に `recipe` 分岐追加
- [x] `.claude/skills/llm-wiki-for-claude-code/references/page-templates.md` に recipe テンプレート追加
- [x] `vault/recipes/` 配下に **5本** 配置（claude-code-setup / hooks-introduction / permission-control-practice / post-tool-use-formatter / keybindings-customization）、全て `confidence ≥ 0.7`, `status: published`, `citation_validator` PASS

#### AUTO マーカー（最小実装）
- [x] AUTO セクションマーカー仕様（`<!-- AUTO:START --> ... <!-- AUTO:END -->`）が `vault/90_meta/auto-marker-spec.md` に確定（ADR-015）
- [x] `agent/writers/markdown_writer.py` に AUTO 領域抽出 + 領域外バイト一致保持ロジック実装（`extract_auto_regions` / `replace_auto_regions`）
- [x] 公式 source 11本 + recipe 5本 = 16本に AUTO 領域導入、領域外バイト一致保持テスト PASS（テスト総数 159 件 PASS）

#### 運用実測
- [x] `vault/90_meta/metrics.md` に Phase 2-A の全記事計測値（記事パス、レビュー時間、修正件数）が記録（対象 16 本）
- [x] 修正率が算出され、Phase 2-B 着手判断の材料になる

### Phase 2-B（pivot 後新規）: 派生ページ本格化 + コミュニティ拡張 + Claude エコシステム拡張

#### ページ種別の拡張
- [ ] `vault/concepts/` に `type: concept` ページが最低5本（複数 source を引用するもの）
- [ ] `vault/entities/` に `type: entity` ページが最低5本（Bash tool / Skills / MCP server / Claude Design 等）
- [ ] `/wiki-query` コマンドが実装され、Wiki 横断検索結果を `vault/syntheses/<topic>.md` として保存できる
- [ ] `vault/syntheses/` に `type: synthesis` ページが最低5本

#### コミュニティ source の追加系統取り込み
- [ ] GitHub Releases (anthropics/claude-code), Anthropic 公式ブログ RSS の取り込み実績あり
- [ ] 個人発信（Karpathy / Rezvani 等）の取り込み実績あり
- [ ] `agent/fetchers/` に RSS / GitHub API 系統の fetcher 追加

#### Claude エコシステム拡張カテゴリ
- [ ] `vault/sources/official/claude-design/`, `vault/sources/official/skills/`, `vault/sources/official/agent-sdk/` のいずれか（最低 1 つ）に縮退仕様の source 記事

#### AUTO マーカー全展開・verify-links CI
- [ ] 全 source 記事に AUTO マーカーが反映済み
- [ ] `agent verify-links` の CI 別ジョブが週次稼働、drift 検出時の Issue 自動起票が動作

### Phase 3: GitHub Actions 自動化 + コミュニティ source + comparison 自動生成

#### 自動化基盤
- [ ] `agent/runners/action` が実装済み
- [ ] GitHub Actions の週次 cron が設定され、`.github/workflows/weekly-update.yml` 等として存在
- [ ] CODEOWNERS と PR テンプレが整備済み
- [ ] 4週連続で cron が成功し、自動 PR が4本立っている（うち N 本マージ済み）
- [ ] 自動 PR の人手修正率が 30% 以下

#### コミュニティ source 取込み
- [ ] ホワイトリスト済みコミュニティソース（Anthropic ブログ RSS、anthropics/claude-code Releases、awesome-claude-code 等）から最低1ソースが取り込まれている
- [ ] `vault/sources/community/` 配下に `type: source` 記事が最低5本（うち1本以上は自動 PR 由来）

#### comparison 自動生成
- [ ] `vault/comparisons/` に `type: comparison` ページが最低3本（自動生成1本以上を含む）

#### 運用品質
- [ ] `vault/90_meta/cost-log.md` に月額 API コスト実測値が記録され、見積範囲内
- [ ] 月次運用が3ヶ月連続で回っている
- [ ] 失敗時に Actions ログから原因が特定できる構造になっている

### エラーハンドリング（全 Phase 共通）
- [ ] 情報源の取得失敗時は記事を更新せず、エラーログを残す
- [ ] LLM 生成失敗時は PR を作成せず、Actions を fail させる
- [ ] frontmatter 検証エラー時は CI を fail させる
- [ ] ホワイトリスト外ソース指定時は処理を中断する

### テスト（全 Phase 共通）
- [ ] `agent/orchestration` の単体テストが存在する（ingest / regenerate / lint）
- [ ] 規約準拠（frontmatter `type` 別検証, Markdown 制約, 3部構成, 連続100文字一致検出）を検証する CI チェックが存在する
- [ ] AUTO マーカーが正しく機能することを検証するテストが存在する（Phase 2 以降）
- [ ] スラッシュコマンドの統合テスト（決定的 LLM スタブを使用）

## スコープ外

### 今回対象外

- **Wiki 本体の Web 公開**: GitHub Pages / 静的サイトジェネレータでの公開は別スコープ。本アイデアではあくまでローカル Vault + Git リポジトリの構築まで。
- **プレゼンテーション資料の自動生成**: Wiki からセミナー・勉強会用のスライドを生成する機能は別アイデアとして切り出す。
- **多言語対応**: 日本語のみ。英語ミラーや他言語は対応しない。
- **LLM 投入用 RAG インデックスの構築**: Wiki を LLM のコンテキストに直接投入するベクトル DB 等の整備は将来検討。
- **公式日本語ドキュメントの素訳**: pivot 後は公式 source は「タイトル + 1段落要約 + 公式リンク」の縮退仕様に統一。素訳は公式日本語版（`code.claude.com/docs/ja/*`）に委ねる。
- **`guide` / `cheatsheet` 種別の Phase 2-A 導入**: Phase 2-A では `recipe` 種別のみ先行。残り 2 種別は Phase 2-B / Phase 3 送り。
- **X/Twitter / Reddit / 個人ブログの fetcher**: Phase 2-A は awesome-claude-code（GitHub README 構造化リスト）のみ。RSS / API 系統の fetcher 追加は Phase 2-B 以降。
- **公式 6 カテゴリの面的整備**: 旧計画の `vault/sources/official/{slash-commands,mcp,settings,sdk}/` × 5本以上展開は撤回。Phase 2-B で Claude エコシステム拡張カテゴリ（claude-design / skills / agent-sdk）を縮退仕様で順次追加。

### 将来対応予定

- **Web 公開**: GitHub Pages + MkDocs Material / Astro Starlight 等で公開（Phase 3 完了後）
- **プレゼン資料生成機能**: Wiki から Marp / Reveal.js スライドを自動生成
- **Anthropic Routines / Schedule での実装**: GitHub Actions が安定したら、Anthropic 側スケジューリングへの移行を検討
- **コミュニティソースのさらなる拡張**: X（旧 Twitter）、Zenn、Qiita 等の追加
- **品質スコアリング**: 生成記事の信頼度・新鮮度の自動評価

## 技術的考慮事項

### ディレクトリ構成

```
wiki-for-claude-code/
├── vault/                                  # Obsidian Vault = Wiki コンテンツ（ページ種別ベース）
│   ├── index.md                            # ナビゲーション本体
│   ├── log.md                              # 全操作の追記専用ログ
│   ├── overview.md                         # 全体俯瞰
│   ├── sources/                            # type=source（Phase 1: 公式 hooks/cli のみ）
│   │   ├── official/
│   │   │   ├── cli/
│   │   │   ├── hooks/
│   │   │   ├── slash-commands/             # Phase 2 から
│   │   │   ├── mcp/                        # Phase 2 から
│   │   │   ├── settings/                   # Phase 2 から
│   │   │   └── sdk/                        # Phase 2 から
│   │   └── community/                      # Phase 3 から
│   │       ├── tips/
│   │       ├── workflows/
│   │       ├── integrations/
│   │       └── troubleshooting/
│   ├── concepts/                           # type=concept（Phase 2 から）
│   ├── entities/                           # type=entity（Phase 2 から）
│   ├── comparisons/                        # type=comparison（Phase 3 で自動生成）
│   ├── syntheses/                          # type=synthesis（Phase 2 から）
│   ├── 30_drafts/
│   └── 90_meta/                            # 規約・ホワイトリスト・運用ログ
├── .claude/
│   ├── commands/                           # Wiki 操作のスラッシュコマンド
│   │   ├── wiki-ingest.md
│   │   ├── wiki-regenerate.md
│   │   ├── wiki-lint.md
│   │   └── wiki-query.md                   # Phase 2 で追加
│   └── skills/
│       └── llm-wiki-for-claude-code/       # 規約・テンプレート・hook の Skill パッケージ
│           ├── SKILL.md
│           ├── references/
│           └── hooks/
├── agent/                                  # 環境非依存ロジック（Phase 1 で雛形、Phase 3 で本格）
│   ├── fetchers/
│   ├── writers/
│   ├── validators/
│   ├── orchestration/
│   └── runners/
│       ├── local
│       └── action
├── .github/
│   ├── workflows/
│   │   └── weekly-update.yml               # Phase 3
│   ├── CODEOWNERS                          # Phase 3
│   └── pull_request_template.md            # Phase 3
├── docs/
│   ├── core/
│   ├── ideas/
│   └── plan/
└── .obsidian/                              # Obsidian 設定（一部のみ Git 管理）
```

### 既存コードとの関係

- 現状 `src/`, `scripts/` は空。新規構築。
- `.claude/skills/steering/` のテンプレート群を参照（既に活用中）。
- 本アイデアの後続で `/plan-feature --from-idea 20260505-llm-wiki-for-claude-code` により詳細計画を作成する想定。

### 依存コンポーネント

| コンポーネント | 用途 |
|--------------|------|
| Obsidian | ローカルでの Wiki 閲覧・編集 UI |
| Claude Agent SDK | エージェント実装（Phase 3） |
| GitHub Actions | 週次 cron 実行基盤（Phase 3） |
| Claude Code | ローカル開発・手動運用フェーズの実行環境 |
| Git / GitHub | バージョン管理・PR レビュー |
| Markdown / YAML | コンテンツフォーマット |
| RSS パーサ / GitHub API | 情報源取得（Phase 3） |

### パフォーマンス考慮

- 週次実行のため、1回の実行時間は数分〜数十分を許容（即時性は不要）
- 全カテゴリ更新時の API コール数を抑えるため、差分検知（既存 frontmatter の `fetched_at` と最新ソース更新日時の比較）で更新対象を絞る
- LLM への入力サイズは prompt caching を活用して最適化

### リスクと対策

| リスク | 影響度 | 対策 |
|-------|--------|------|
| Anthropic Usage Policy / docs.claude.com の利用規約違反 | 高 | Phase 1 着手前に規約確認。`source` 種別に「要約 + リンク + 補足」構造を強制し、全文転載を禁止 |
| Reddit API 有料化・GitHub レート制限・スクレイピング bot 検知 | 高 | Phase 1 で情報源ホワイトリストを確定。RSS / 公式 API / 利用規約上問題ないソースのみに限定 |
| Claude Code バージョン揮発性による記事陳腐化 | 高 | `claude_code_version` を Phase 1 から frontmatter 必須化。`/wiki-lint` で古い記事を識別 |
| LLM のハルシネーション（誤った主張の混入） | 高 | `confidence` スコア必須化、引用必須（全主張に `sources` 紐付け）、`/wiki-lint` での矛盾検出、人間レビュー |
| Obsidian 独自記法（Dataview, Callout 等）の portability 欠如 | 中 | Phase 1 で「標準 MD + Wikilinks のみ」を規約化。Karpathy 原案では Dataview 推奨だが Web 公開を見据え不採用 |
| 自動 PR が人手編集を上書きする事故 | 中 | Phase 2 で AUTO セクションマーカーを導入し、自動領域と人手領域を分離 |
| API コストの想定超過 | 中 | Phase 3 で cost-log.md に実測値を記録。差分検知で更新対象を絞る。prompt caching を活用 |
| 翻訳・要約の品質低下 | 中 | 人間レビュー必須。レビュー工数を Phase 2 で実測し、品質基準を Phase 3 で設定 |
| 200ページ超えでインデックスベース検索が劣化 | 中 | Phase 3 以降で qmd 等のセマンティック検索（MCP server）導入を検討。Phase 1-2 では index ベースで十分 |
| 同時編集による Wiki ページ競合 | 中 | 一度に1つの Skill セッション + GitHub Actions の lock ファイルで直列化 |
| GitHub Actions の IP からのアクセス遮断 | 低 | RSS / 公式 API を優先利用。スクレイピングが必要なソースは事前検証 |
| Obsidian Vault と Git リポジトリの分離による同期地獄 | - | 統合構造（Vault = Repo）で回避済み |

## 更新履歴

- 2026-05-05: 初版作成（ブレインストーミングセッション）
- 2026-05-05: Karpathy LLM-Wiki gist と Rezvani Medium 記事の精読を踏まえ、ドメイン特化コンパイル型 Wiki への折衷案として全面改訂（ページ種別5種類、Skill 構造、ロードマップ2軸、3操作 + regenerate、信頼度スコア、log.md / index.md 導入）
- 2026-05-05: Anthropic 公式ドキュメント（claude-code/skills.md）確認の結果、Skill 内 `commands/` サブディレクトリは公式仕様外と判明。Slash Command と Skill を分離する構造に改訂（Wiki 操作は `.claude/commands/wiki-*.md`、規約・テンプレート・hook は `.claude/skills/llm-wiki-for-claude-code/{SKILL.md, references/, hooks/}`）。詳細は ADR-014。
- 2026-05-06: **Phase 2 pivot を反映**（壁打ちセッション由来）。公式日本語版（`code.claude.com/docs/ja/*`）の存在確認により「公式素訳」の付加価値が無効化されたため、主軸を **「コミュニティ実践知の自動整理 + 横断視点での再構成」** に転換。主な改訂:
  - スコープ対象を Claude Code 単体 → **Claude エコシステム全般**（Claude Code + Claude Design + Skills + Agent SDK 等、リポジトリ名は維持）に拡張
  - `source` 種別を **縮退仕様**（タイトル + 1段落要約 + 公式リンク + AUTO マーカー）に変更、3部構成強制を撤回
  - ページ種別を 5 → **8 種別** に拡張（`recipe` / `guide` / `cheatsheet` を追加、うち `recipe` は Phase 2-A で先行検証）
  - Phase 2 を **A（MVP）/ B（拡張）に分割**。コミュニティ source 取り込み（awesome-claude-code 先行）と実 LLM 統合を Phase 2-A に前倒し
  - 公式 6 カテゴリ展開（旧機能 5）と drift 記事 2 本の全面書き直し（旧機能 1）を撤回
  - 詳細な実装計画は plan ファイル `~/.claude/plans/synchronous-tickling-dragon.md` を参照
- 2026-05-08: **Phase 2-A 実 LLM 統合の主要マイルストーン完了**。`AnthropicBackend` に加え `ClaudeCodeBackend`（Max プラン経由）を追加し、empirical PASS 後に既定を `claude-code` に昇格（ADR-018）。AUTO 領域は実 LLM 経由で再生成され、AUTO 外の人手編集は保護される（ADR-019）。`CLAUDE.md` の本番運用ガード注記を解除、`metrics.md` に対象 16 本の運用記録追加。詳細は `docs/ideas/20260508-claude-code-llm-backend.md` を参照。
