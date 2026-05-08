# 設計書（Phase 2-A: MVP / pivot 後）

> 作成日: 2026-05-06
> 関連: `requirements.md`（同ディレクトリ）/ `~/.claude/plans/synchronous-tickling-dragon.md`

## アーキテクチャ概要

Phase 1 で確立した **3 層構造**（Slash Command / Skill / 環境非依存ロジック）を継承し、各層に Phase 2-A 機能（A-1〜A-6）を増設する。新規コンポーネントは追加するが、層構造そのものは不変。

```
ユーザー / Claude Code
        │
        ▼
┌──────────────────────────────────┐
│ .claude/commands/wiki-*.md       │ ← Slash Command 層（明示起動）
│ .claude/skills/.../{SKILL.md,    │ ← Skill 層（context-aware ロード）
│   references/, hooks/}           │   recipe テンプレ追加 / 規約改訂
└──────────────────────────────────┘
        │ 呼び出し
        ▼
┌──────────────────────────────────┐
│ agent/                           │ ← 環境非依存ロジック層
│  ├ orchestration/                │   - llm.py: 実 Anthropic SDK 統合 (A-1)
│  │   ├ ingest.py                 │   - awesome-claude-code 取込みパス追加 (A-3)
│  │   ├ regenerate.py             │   - AUTO 領域処理連携 (A-5)
│  │   ├ lint.py / validate.py     │   - recipe 種別対応 (A-4)
│  │   └ llm.py                    │   - stub | anthropic 切替
│  ├ fetchers/                     │   - awesome_claude_code.py 追加 (A-3)
│  ├ writers/markdown_writer.py    │   - AUTO 領域抽出 + バイト一致保持 (A-5)
│  ├ validators/                   │   - frontmatter / citation: recipe 分岐 (A-4)
│  └ runners/local                 │   - 環境変数 WIKI_LLM_BACKEND 等
└──────────────────────────────────┘
        │ 入出力
        ▼
┌──────────────────────────────────┐
│ vault/                           │ ← Wiki コンテンツ + 規約
│  ├ sources/official/{cli,hooks}  │   - 縮退仕様 10 本 (A-2)
│  ├ sources/community/            │   - awesome-claude-code/ 5+ 本 (A-3)
│  ├ recipes/                      │   - 5+ 本 (A-4)
│  └ 90_meta/                      │   - auto-marker-spec.md (A-5)
│                                  │   - metrics.md (A-6)
│                                  │   - frontmatter-spec.md (recipe 追加)
│                                  │   - markdown-rules.md (3 部構成 → 縮退)
│                                  │   - sources.md (awesome-claude-code 追加)
│                                  │   - license-notes.md (awesome 追加)
└──────────────────────────────────┘
```

## コンポーネント設計

### 1. `agent/orchestration/llm.py`（A-1: 実 Anthropic SDK 統合）

**責務**:
- Anthropic SDK を介した Claude Sonnet 4.6 の呼び出し
- prompt caching の制御（system プロンプト / 規約 references を cache 化）
- バックエンド切替（`stub` / `anthropic`）の抽象化

**実装の要点**:
- インターフェイス: `class LLMBackend(Protocol)` を定義し、`StubBackend` / `AnthropicBackend` の 2 実装を切替
- 環境変数: `WIKI_LLM_BACKEND=stub|anthropic`（既定 `stub`、後半フェーズで `anthropic`）/ `WIKI_LLM_MODEL=claude-sonnet-4-6`（上書き可）/ `ANTHROPIC_API_KEY` 必須
- prompt caching: `system` メッセージで規約 references（schema / page-templates / three-part-rule 等）を `cache_control: ephemeral` 付与
- エラー処理:
  - API キー欠落 → `ConfigurationError` → exit code 3
  - API 呼び出し失敗（rate limit / network）→ 1 回リトライ後 `LLMInvocationError` → exit code 3
- ロギング: 入出力トークン数 / cache hit を `metrics.md` に追記する hook を呼ぶ

**依存**:
- `anthropic>=0.40` を `pyproject.toml` に追加
- 既存 `agent/errors.py` に `ConfigurationError`, `LLMInvocationError` を追加

### 2. `agent/writers/markdown_writer.py`（A-5: AUTO マーカー処理）

**責務**:
- AUTO マーカー領域（`<!-- AUTO:START --> ... <!-- AUTO:END -->`）の抽出と書き換え
- 領域外のバイト一致保持（人手編集を上書きしない構造的保証）
- frontmatter シリアライズ（既存実装を継承）

**実装の要点**:
- 構文パーサ: 正規表現ではなく行単位スキャナで START / END 行を検出（ネスト禁止 / 1 ファイル内に複数領域許容）
- 境界検証: START の数 ≠ END の数、または順序不正の場合 `MalformedAutoMarkerError`
- 書き換え API: `replace_auto_regions(path: Path, new_contents: list[str]) -> None` — 領域数と `new_contents` の長さ一致を強制
- 領域外バイト一致保持: 書き換え前後で「領域外行のバイト列」が完全一致することを assert（テストで担保）
- 既存の `regenerate` ユースケースから `markdown_writer.replace_auto_regions` を呼ぶ形に切替

**テスト**:
- unit: 領域抽出 / 領域数不一致エラー / ネストエラー / 領域外バイト一致
- integration: `regenerate` 後の領域外バイト一致 PASS

### 3. `agent/fetchers/awesome_claude_code.py`（A-3: コミュニティ source 取込み）

**責務**:
- awesome-claude-code リポジトリの README（または特定エントリ）から記事素材を取得
- 上流 URL + コミット SHA を返す（frontmatter `sources` 記録用）

**実装の要点**:
- 取得方式: GitHub raw content API（`https://raw.githubusercontent.com/<owner>/awesome-claude-code/<sha>/README.md`）
- レート制限: GitHub unauth は 60 req/h。Phase 2-A は手動起動のため十分
- 解析: README の構造化マークダウン（ヘッダ階層 + リンク列挙）から各エントリを `dataclass FetchedEntry(url, title, description, parent_section, commit_sha)` に変換
- ライセンス確認: README 末尾 / LICENSE ファイルを取得し、`license-notes.md` に転記
- ホワイトリスト連携: `vault/90_meta/sources.md` の `awesome-claude-code` エントリの `url_pattern` と一致しない URL は `WhitelistViolation` エラー

**テスト**:
- unit: 構造化リスト解析 / コミット SHA 抽出
- integration: モック GitHub レスポンスでの ingest E2E

### 4. `agent/validators/frontmatter_validator.py` + `citation_validator.py`（A-4: recipe 種別対応）

**責務**:
- `type: recipe` の必須キー検証（`use_case`, `sources` ≥ 2 件）
- `citation_validator` で `sources` 内の wikilink が `vault/sources/` 配下を指すことを検証

**実装の要点**:
- JSON Schema 拡張: `vault/90_meta/_schemas/frontmatter.schema.json` の `oneOf` に `recipe` 分岐を追加
  ```json
  {
    "if": { "properties": { "type": { "const": "recipe" } } },
    "then": {
      "required": ["use_case", "sources"],
      "properties": {
        "use_case": { "type": "string", "minLength": 1 },
        "sources": { "type": "array", "minItems": 2 }
      }
    }
  }
  ```
- `frontmatter_validator.validate()` の dispatch テーブルに `recipe` を追加（既存 `source` / `concept` / `entity` パターンを踏襲）
- `citation_validator`: `recipe` の `sources` 各要素が `[[vault/sources/...]]` 形式の wikilink であることを正規表現で検証
- 既存 source 規約改訂: `markdown-rules.md` の 3 部構成強制を縮退仕様に書き換え（A-2 と同期）

**テスト**:
- unit: recipe 必須キー欠落 / sources < 2 件 / wikilink 不正形式
- integration: `agent validate --all` で recipe 5 本 PASS

### 5. Skill `references/page-templates.md`（A-4: recipe テンプレート追加）

**責務**:
- recipe 種別の標準構造（frontmatter 雛形 + 本文骨格）を提供
- Wiki 編集時に context-aware にロードされる

**実装の要点**:
- 既存 `page-templates.md` の `source` テンプレ末尾に `recipe` セクションを追記
- recipe テンプレ骨格:
  ```markdown
  ---
  title: "<ユースケース名>"
  type: recipe
  use_case: "<具体的なユースケース 1 文>"
  sources: ["[[vault/sources/...]]", "[[vault/sources/...]]"]  # 最低 2 件
  confidence: 0.7
  ...
  ---

  ## TL;DR
  <!-- AUTO:START -->
  （ユースケースの結論を 1-3 文で）
  <!-- AUTO:END -->

  ## 手順
  <!-- AUTO:START -->
  ...
  <!-- AUTO:END -->

  ## 引用元の補足
  （引用元のどの部分を再構成したか / 派生した独自視点）
  ```

### 6. `vault/90_meta/auto-marker-spec.md`（A-5 新規）

**責務**:
- AUTO マーカー構文と境界制御規約の SSoT

**記載内容**:
- 構文: `<!-- AUTO:START --> ... <!-- AUTO:END -->`（HTML コメント）
- ネスト禁止（START 後に END より先に START が現れた場合エラー）
- 1 ファイル内複数領域許容（順序付きで管理）
- 領域外バイト一致保持の規範（Writer 実装とテストで担保）
- `auto_section_managed: true` の frontmatter キーとの関係（Phase 2-B で全展開予定）

**ADR-015 起票**: 上記仕様を `docs/core/decisions.md` に ADR-015 として追記。

### 7. `vault/90_meta/metrics.md`（A-6 新規）

**責務**:
- Phase 2-A の生成・レビュー実績を集計

**スキーマ**:
| 列 | 型 | 説明 |
|---|---|---|
| `path` | string | 記事の vault 相対パス |
| `generated_at` | ISO8601 | 生成日時 |
| `reviewer` | string | レビュアー（`tak` 等） |
| `review_minutes` | int | レビュー所要分 |
| `auto_fix_count` | int | 自動修正件数 |
| `manual_fix_count` | int | 人手修正件数 |
| `llm_input_tokens` | int | 入力トークン数（cache 込み） |
| `llm_output_tokens` | int | 出力トークン数 |
| `cache_hit_rate` | float | prompt cache hit 率 |

集計ビュー（Phase 2-A 完了時）:
- 修正率 = sum(`manual_fix_count`) / count(*)
- 平均レビュー時間 = avg(`review_minutes`)
- LLM コスト推計 = sum(tokens) × 単価

## データフロー

### A-1: regenerate（実 SDK 経由）

```
1. ユーザー: /wiki-regenerate vault/recipes/<sample>.md
2. Slash Command → uv run agent regenerate --target <path>
3. orchestration/regenerate.py:
   a. 既存記事の frontmatter + AUTO 領域を読み出し
   b. orchestration/llm.py.invoke(system=規約 references with cache, prompt=領域別生成指示)
   c. AnthropicBackend が Sonnet 4.6 を呼び、AUTO 領域の新内容を返す
4. writers/markdown_writer.replace_auto_regions(path, new_contents)
5. 領域外バイト一致を assert
6. metrics に input/output tokens, cache_hit_rate を追記
```

### A-3: ingest（awesome-claude-code）

```
1. ユーザー: /wiki-ingest <awesome-claude-code-entry-url> --category awesome-claude-code
2. orchestration/ingest.py:
   a. ホワイトリスト確認（sources.md と URL pattern マッチ）
   b. fetchers/awesome_claude_code.py.fetch(url) → FetchedEntry
   c. orchestration/llm.py.invoke で 1 段落要約 + AUTO 構造生成
3. writers/markdown_writer.create(path=vault/sources/community/awesome-claude-code/<slug>.md, ...)
4. validators/frontmatter_validator + citation_validator で PASS 確認
5. log.md に追記、index.md 更新
```

### A-4: recipe ingest（手動 + LLM 補助）

```
1. ユーザーがテンプレ（page-templates.md の recipe）から雛形をコピー
2. sources を最低 2 件設定（既存の vault/sources/ 配下）
3. /wiki-regenerate vault/recipes/<sample>.md で AUTO 領域を生成
4. validators/frontmatter_validator (recipe 分岐) PASS
5. validators/citation_validator (sources ≥ 2, wikilink 形式) PASS
6. /wiki-lint で confidence ≥ 0.7 確認 → status: published 昇格
```

## エラーハンドリング戦略

### カスタムエラークラス（`agent/errors.py` 拡張）

```python
class ConfigurationError(AgentError): ...           # API キー欠落 / 環境変数不正
class LLMInvocationError(AgentError): ...           # SDK 呼び出し失敗
class MalformedAutoMarkerError(AgentError): ...     # AUTO 構文不正
class WhitelistViolation(AgentError): ...           # 既存（Phase 1）
class CitationError(AgentError): ...                # 既存（recipe で sources<2 等）
```

### エラーハンドリングパターン

| エラー | 対応 | exit code |
|-------|------|----------|
| `ConfigurationError` | エラーメッセージで欠落キーを明示、終了 | 3 |
| `LLMInvocationError` | 1 回リトライ後、ログに stack trace 残して終了 | 3 |
| `MalformedAutoMarkerError` | ファイルパスと領域番号を出力、書き込み中止 | 4 |
| `WhitelistViolation` | URL を出力、ホワイトリスト追加手順を案内 | 5 |
| `CitationError` | 不足/不正な sources を出力、テンプレ参照を促す | 6 |

## テスト戦略

### ユニットテスト（追加）

- `tests/unit/orchestration/test_llm_anthropic.py` — AnthropicBackend モック呼び出し
- `tests/unit/writers/test_auto_markers.py` — AUTO 抽出 / 境界エラー / バイト一致
- `tests/unit/fetchers/test_awesome_claude_code.py` — README 解析 / SHA 抽出
- `tests/unit/validators/test_frontmatter_recipe.py` — recipe 必須キー / JSON Schema
- `tests/unit/validators/test_citation_recipe.py` — sources ≥ 2 / wikilink 形式

### 統合テスト（追加）

- `tests/integration/test_regenerate_with_auto.py` — regenerate 後に領域外バイト一致 PASS
- `tests/integration/test_ingest_awesome.py` — モック GitHub での E2E ingest
- `tests/integration/test_recipe_validate.py` — recipe 5 本サンプルで `agent validate` PASS

### E2E テスト（追加）

- `tests/e2e/test_phase2a_smoke.py` — `WIKI_LLM_BACKEND=stub` で全コマンド一通り動作

### 目標件数

- Phase 1: 107 件 → Phase 2-A 完了時: **130 件以上**

## 依存ライブラリ

```toml
# pyproject.toml に追加
[project]
dependencies = [
    "anthropic>=0.40",        # A-1
    # 既存依存はそのまま継承
]
```

実装後の検証:
- `uv lock` で `anthropic` の transitive 依存が問題ないことを確認
- `uv run mypy agent/orchestration/llm.py` で型エラーなし

## ディレクトリ構造（Phase 2-A 追加・変更分）

```
wiki-for-claude-code/
├── .steering/20260506-llm-wiki-for-claude-code-phase-2a/
│   ├── requirements.md          # 本フェーズ要件
│   ├── design.md                # 本書
│   └── tasklist.md              # タスク分解
├── agent/
│   ├── orchestration/llm.py     # ★ Anthropic SDK 実装に置換 (A-1)
│   ├── writers/markdown_writer.py # ★ AUTO 領域処理追加 (A-5)
│   ├── fetchers/
│   │   └── awesome_claude_code.py # ★ 新規 (A-3)
│   ├── validators/
│   │   ├── frontmatter_validator.py # ★ recipe 分岐追加 (A-4)
│   │   └── citation_validator.py    # ★ recipe 引用検証 (A-4)
│   └── errors.py                # ★ 新規エラー型追加
├── vault/
│   ├── sources/official/{cli,hooks}/*.md # ★ 縮退仕様に書き換え (A-2)
│   ├── sources/community/awesome-claude-code/*.md # ★ 新規 5+ 本 (A-3)
│   ├── recipes/                 # ★ 新規ディレクトリ (A-4)
│   │   ├── claude-code-setup.md
│   │   ├── hooks-introduction.md
│   │   ├── mcp-integration-tips.md
│   │   ├── permission-control-practice.md
│   │   └── multi-model-switching.md
│   └── 90_meta/
│       ├── auto-marker-spec.md  # ★ 新規 (A-5)
│       ├── metrics.md           # ★ 新規 (A-6)
│       ├── frontmatter-spec.md  # ★ recipe 種別追加 (A-4)
│       ├── _schemas/frontmatter.schema.json # ★ recipe 分岐追加 (A-4)
│       ├── markdown-rules.md    # ★ 3 部構成 → 縮退に改訂 (A-2)
│       ├── sources.md           # ★ awesome-claude-code 追加 (A-3)
│       └── license-notes.md     # ★ awesome ライセンス追加 (A-3)
├── .claude/skills/llm-wiki-for-claude-code/references/
│   ├── page-templates.md        # ★ recipe テンプレ追加 (A-4)
│   └── three-part-rule.md       # ★ 縮退仕様に改訂 or 削除 (A-2)
├── docs/core/decisions.md       # ★ ADR-015/016/017 追記
├── CLAUDE.md                    # ★ Phase 2-A 着手宣言・ガード解除
└── tests/
    ├── unit/    # ★ 追加テスト多数
    ├── integration/
    └── e2e/
```

## 実装の順序

Phase 2-A 内のタスクを依存順で配置（詳細は `tasklist.md`）:

1. **規約・ADR 先行**（A-5 / A-2 の前提）
   - ADR-015（AUTO マーカー）/ ADR-016（pivot 決定）/ ADR-017（縮退仕様）起票
   - `auto-marker-spec.md` 作成
   - `markdown-rules.md` の 3 部構成 → 縮退仕様改訂
   - `frontmatter-spec.md` に recipe 追加 + JSON Schema 拡張

2. **agent 層実装**
   - `errors.py` 新規エラー型
   - `writers/markdown_writer.py` AUTO 領域処理
   - `validators/{frontmatter,citation}_validator.py` recipe 分岐
   - `orchestration/llm.py` Anthropic SDK 実装
   - `fetchers/awesome_claude_code.py` 新規

3. **テスト整備**
   - 各機能のユニット → 統合 → E2E
   - 既存テスト 107 件 PASS 維持を確認

4. **コンテンツ生成**
   - 公式 source 10 本縮退（A-2）+ AUTO 領域導入
   - recipe 5 本作成（A-4）+ AUTO 領域導入
   - awesome-claude-code 5 本 ingest（A-3）

5. **Skill / Slash Command 動作確認**
   - `page-templates.md` に recipe 追加
   - `/wiki-ingest`, `/wiki-regenerate`, `/wiki-lint` をローカル Claude Code から実行

6. **metrics 集計と判定**
   - `metrics.md` に全件記録
   - 修正率 / コストを算出、A-7 中止条件に該当しないか確認

7. **CLAUDE.md 改訂**
   - `agent regenerate` ガード解除
   - Phase 2-A 進行中ステータスへ更新

## セキュリティ考慮事項

- `ANTHROPIC_API_KEY` は環境変数のみ。コミット禁止（`.gitignore` に `.env` 既存）
- LLM 出力をそのまま記事化しないため、人手レビューゲートで XSS / リンクインジェクション混入を防止
- awesome-claude-code から取得した URL は、レンダラに渡す前に `https?://` のみ許可（既存 `transclusion_validator` の延長）

## パフォーマンス考慮事項

- prompt caching: 規約 references（schema / page-templates / three-part-rule）を `cache_control: ephemeral` で送信し、連続 regenerate のコスト削減
- 差分検知: 既存記事の `fetched_at` と上流 commit SHA の比較で更新対象を絞る（既存 fetcher 仕様を継承）
- バッチ処理は Phase 2-A では不要（記事数 20 本程度）

## 将来の拡張性

- Phase 2-B で `concept` / `entity` / `synthesis` 種別を追加する際、本フェーズで確立した `recipe` の dispatch パターン（JSON Schema oneOf + validator dispatch + Skill template）をそのまま流用
- AUTO マーカー実装は Phase 2-B で全 source 記事に展開する際もインターフェイス不変（`replace_auto_regions` API の引数追加なし）
- LLM バックエンドは `LLMBackend` Protocol に揃えるため、将来 OpenAI / Gemini / ローカルモデル追加時も `*Backend` クラス追加で対応可能（Phase 3 以降の検討事項）
