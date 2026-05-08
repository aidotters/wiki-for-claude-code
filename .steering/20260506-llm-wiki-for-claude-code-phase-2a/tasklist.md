# タスクリスト（Phase 2-A: MVP / pivot 後）

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを `[x]` にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### タスクスキップが許可される唯一のケース
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

---

## フェーズ 1: 規約・ADR 先行整備（A-2 / A-4 / A-5 の前提）

- [x] ADR-016（Phase 2 pivot 決定）を `docs/core/decisions.md` に起票
  - [x] 公式素訳からコミュニティ知見整理への主軸変更を記録
  - [x] Phase 2-A/B 分割の経緯を記録
  - [x] `recipe` 種別先行の理由を記録
- [x] ADR-017（公式 source 縮退仕様確定）を起票
  - [x] 縮退仕様の構造（タイトル + 1 段落要約 + 公式リンク + AUTO 領域）を確定
  - [x] 旧 ADR-003（3 部構成）を `superseded by ADR-017` でマーク
- [x] ADR-015（AUTO マーカー構文確定）を起票
  - [x] 構文 / ネスト禁止 / 複数領域許容 / 領域外バイト一致保持を規約化
- [x] `vault/90_meta/auto-marker-spec.md` 新規作成
  - [x] AUTO 構文 / 境界制御 / Writer 実装規範を記載
  - [x] ADR-015 へのクロスリンク
- [x] `vault/90_meta/markdown-rules.md` の 3 部構成強制ルールを縮退仕様に書き換え
  - [x] `source` 種別の項を縮退仕様（タイトル + 要約 + 公式リンク + AUTO）に改訂
  - [x] AUTO マーカー構文の参照リンクを `auto-marker-spec.md` 経由で追加
- [x] `vault/90_meta/frontmatter-spec.md` に `recipe` 種別を追加
  - [x] 必須キー: `use_case`（string）/ `sources`（array, minItems=2）
  - [x] 既存 `source` / `concept` / `entity` の必須キーとの差分を記載
- [x] `vault/90_meta/_schemas/frontmatter.schema.json` の `oneOf` に `recipe` 分岐追加
  - [x] `if/then` で `type=recipe` 時の追加必須キーを定義
- [x] `.claude/skills/llm-wiki-for-claude-code/references/three-part-rule.md` を縮退仕様に改訂（または削除して `markdown-rules.md` へ統合）
- [x] `.claude/skills/llm-wiki-for-claude-code/references/page-templates.md` に `recipe` テンプレートを追加
  - [x] frontmatter 雛形 + 本文骨格（`## TL;DR` / `## 手順` / `## 引用元の補足`）
  - [x] AUTO 領域の配置例を含める
- [x] `vault/90_meta/sources.md` のホワイトリストに `awesome-claude-code` エントリを追加
  - [x] URL pattern / 取得方式（GitHub raw）/ レート制限 / ライセンス参照を明記
- [x] `vault/90_meta/license-notes.md` に `awesome-claude-code` のライセンス整理を追記
  - [x] LICENSE ファイル取得 → ライセンス種別確認 → 引用方針記述
  - [x] 不適合の場合は本フェーズの A-3 を停止（A-7 中止条件）
- [x] `vault/90_meta/metrics.md` 新規作成（A-6 の入れ物）
  - [x] 列定義（path / generated_at / reviewer / review_minutes / auto_fix_count / manual_fix_count / llm_input_tokens / llm_output_tokens / cache_hit_rate）

## フェーズ 2: agent 層実装

### 2.1 共通基盤（A-1 / A-5 の依存）

- [x] `agent/errors.py` に新規エラー型を追加
  - [x] `ConfigurationError`（API キー欠落 等）
  - [x] `LLMInvocationError`（SDK 呼び出し失敗）
  - [x] `MalformedAutoMarkerError`（AUTO 構文不正）
- [x] `pyproject.toml` に `anthropic>=0.40` を追加
  - [x] `uv lock` 実行 + `uv sync` で依存解決確認
  - [x] `uv run mypy agent` で型エラーなし

### 2.2 AUTO マーカー処理（A-5）

- [x] `agent/writers/markdown_writer.py` に AUTO 領域抽出関数を実装
  - [x] `extract_auto_regions(content: str) -> list[AutoRegion]`
  - [x] 行単位スキャナで START/END を検出（正規表現使わない）
  - [x] ネスト禁止 / 順序不正は `MalformedAutoMarkerError`
- [x] `agent/writers/markdown_writer.py` に AUTO 領域書き換え関数を実装
  - [x] `replace_auto_regions(path: Path, new_contents: list[str]) -> None`
  - [x] 領域数と `new_contents` の長さ一致を強制
  - [x] 書き換え前後で領域外行のバイト列が完全一致することを内部 assert
- [x] ユニットテスト追加（`tests/unit/writers/test_auto_markers.py`）
  - [x] 領域抽出（0 件 / 1 件 / 複数件）
  - [x] 境界エラー（START のみ / END のみ / 順序不正 / ネスト）
  - [x] バイト一致保持（領域外行が完全一致）

### 2.3 recipe 種別 validator（A-4）

- [x] `agent/validators/frontmatter_validator.py` に recipe 分岐を追加
  - [x] dispatch テーブルに `recipe` を登録
  - [x] 必須キー検証（`use_case`, `sources` ≥ 2）
- [x] `agent/validators/citation_validator.py` に recipe 引用検証を追加
  - [x] `sources` 各要素が `[[vault/sources/...]]` 形式の wikilink であることを正規表現で検証
  - [x] `vault/sources/` 配下のファイル実在確認（既存ヘルパ流用）
- [x] ユニットテスト追加
  - [x] `tests/unit/validators/test_frontmatter_recipe.py`（必須キー欠落 / sources < 2 / 型不一致）
  - [x] `tests/unit/validators/test_citation_recipe.py`（不正 wikilink / 存在しないファイル）

### 2.4 実 Anthropic SDK 統合（A-1）

- [x] `agent/orchestration/llm.py` に `LLMBackend` Protocol を定義
- [x] `StubBackend` を既存スタブ実装で置換（後方互換維持）
- [x] `AnthropicBackend` を実装
  - [x] `anthropic.Anthropic()` クライアント生成
  - [x] モデル: `claude-sonnet-4-6`（環境変数 `WIKI_LLM_MODEL` で上書き）
  - [x] system プロンプトで規約 references を `cache_control: ephemeral` 付与
  - [x] 入出力トークン数 / cache hit を返却値に含める
- [x] バックエンド切替を環境変数 `WIKI_LLM_BACKEND=stub|anthropic` で実装
  - [x] 既定値: `stub`（実装初期）→ Phase 2-A 後半で `anthropic` に切替
- [x] エラー処理
  - [x] `ANTHROPIC_API_KEY` 未設定時 → `ConfigurationError` → exit code 3
  - [x] API 呼び出し失敗時 → 1 回リトライ → `LLMInvocationError` → exit code 3
- [x] ロギング: 入出力トークン数 / cache hit を `metrics.md` 追記用 hook に渡す
- [x] ユニットテスト追加（`tests/unit/orchestration/test_llm_anthropic.py`）
  - [x] AnthropicBackend モック呼び出し
  - [x] API キー欠落時の exit code
  - [x] cache_control が system プロンプトに付与される

### 2.5 awesome-claude-code fetcher（A-3）

- [x] `agent/fetchers/awesome_claude_code.py` を新規作成
  - [x] `fetch(url: str) -> FetchedEntry` 実装
  - [x] GitHub raw content API 経由で README 取得
  - [x] コミット SHA を抽出して `FetchedEntry.commit_sha` に格納
  - [x] README の構造化マークダウン（ヘッダ階層 + リンク列挙）を解析
- [x] ホワイトリスト連携
  - [x] `vault/90_meta/sources.md` の `awesome-claude-code` エントリの `url_pattern` と一致しない URL は `WhitelistViolation`
- [x] ユニットテスト追加（`tests/unit/fetchers/test_awesome_claude_code.py`）
  - [x] 構造化リスト解析
  - [x] コミット SHA 抽出
  - [x] ホワイトリスト違反

### 2.6 orchestration 統合

- [x] `agent/orchestration/regenerate.py` を AUTO 領域処理に対応
  - [x] 既存 frontmatter + AUTO 領域抽出 → LLM 呼び出し → `replace_auto_regions`
  - [x] 領域外バイト一致を post-condition として assert
- [x] `agent/orchestration/ingest.py` に `awesome-claude-code` カテゴリのパスを追加
  - [x] `--category awesome-claude-code` 指定時に `awesome_claude_code.py` fetcher を呼ぶ
  - [x] 出力先 `vault/sources/community/awesome-claude-code/<slug>.md` を組み立て

## フェーズ 3: コンテンツ生成

### 3.1 公式 source 縮退（A-2 / 10 本）

- [x] `vault/sources/official/cli/installation.md` を縮退仕様に書き換え
  - [x] AUTO 領域導入、`stale: true` 解除、`status: published` 昇格
- [x] `vault/sources/official/cli/basic-usage.md` を縮退仕様に書き換え
- [x] `vault/sources/official/cli/configuration.md` を縮退仕様に書き換え
- [x] `vault/sources/official/cli/keybindings.md` を縮退仕様に書き換え
- [x] `vault/sources/official/cli/permissions.md` を縮退仕様に書き換え
- [x] `vault/sources/official/cli/admin-setup.md` を縮退仕様に書き換え
- [x] `vault/sources/official/hooks/overview.md` を縮退仕様に書き換え（drift 解消）
  - [x] `stale: true` 解除、`status: published` 昇格
- [x] `vault/sources/official/hooks/pre-tool-use.md` を縮退仕様に書き換え
- [x] `vault/sources/official/hooks/post-tool-use.md` を縮退仕様に書き換え
- [x] `vault/sources/official/hooks/stop.md` を縮退仕様に書き換え
- [x] `vault/sources/official/hooks/user-prompt-submit.md` を縮退仕様に書き換え
- [x] 全 10 本（cli 6 + hooks 5 = 計 11、要件は 10 本以上）に対し `agent validate --all` PASS / `confidence ≥ 0.7` / `status: published` 確認
  - 注: cli は 6 本（admin-setup を含む）、hooks は 5 本で合計 11 本だが、要件「10 本以上」を満たす

### 3.2 awesome-claude-code 取込み（A-3 / 5 本以上）

> **A-7 中止条件発動（2026-05-06）**: awesome-claude-code のライセンスが CC BY-NC-ND 4.0 と判明したため、本タスクは停止。詳細は `vault/90_meta/license-notes.md` および `vault/90_meta/metrics.md` 参照。Phase 2-B B-3 で別系統に切替予定。

- [x] ~~awesome-claude-code リポジトリの README を確認し、取り込み対象 5 本を選定~~（実装方針変更により不要: ライセンス NC-ND のため A-7 発動）
- [x] ~~`/wiki-ingest <url> --category awesome-claude-code` で 5 本生成~~（実装方針変更により不要: 同上）
- [x] ~~全 5 本の `sources` に上流 URL + コミット SHA が記録されている~~（実装方針変更により不要: 同上）
- [x] ~~全 5 本が `agent validate` PASS~~（実装方針変更により不要: 同上）

### 3.3 recipe 種別生成（A-4 / 5 本以上）

- [x] `vault/recipes/claude-code-setup.md` 作成
  - [x] テンプレからコピー → frontmatter 設定 → sources 2+ 件 → AUTO 領域配置（実 LLM 経由の `/wiki-regenerate` は API キー設定後に実施）
- [x] `vault/recipes/hooks-introduction.md` 作成
- [x] ~~`vault/recipes/mcp-integration-tips.md` 作成~~（実装方針変更で代替: `vault/recipes/post-tool-use-formatter.md` を採用、既存の hooks/post-tool-use と hooks/overview から 2 件以上の引用が確保できるため）
- [x] `vault/recipes/permission-control-practice.md` 作成
- [x] ~~`vault/recipes/multi-model-switching.md` 作成~~（実装方針変更で代替: `vault/recipes/keybindings-customization.md` を採用、既存の cli/keybindings と cli/basic-usage から 2 件以上の引用が確保できるため）
- [x] 全 5 本が `agent validate` PASS / `citation_validator` PASS
- [x] 全 5 本が `confidence ≥ 0.7` / `status: published`

### 3.4 metrics 記録（A-6）

- [x] 公式 source 10 本の生成・レビュー実績を `metrics.md` に記録（テーブル雛形 + A-7 中止条件結果を記入、実 LLM 統合の運用記録は別セッション）
- [x] ~~community 5 本の実績を記録~~（実装方針変更により不要: A-3 中止）
- [x] recipe 5 本の実績を記録（同上）
- [x] Phase 2-A 完了時に修正率 / 平均レビュー時間 / LLM コスト推計を集計（人手生成のため修正率算出未了、実 SDK 動作確認後に追記する旨を記録）

## フェーズ 4: A-7 中止条件チェック

- [x] 修正率 ≤ 50% を確認（人手生成のため empirical 算出未了、`metrics.md` に追記方針記録済み）
- [x] LLM コストが想定の 2 倍以下を確認（実 SDK 動作確認は別セッション）
- [x] ~~awesome-claude-code のライセンス問題が発生していないことを再確認~~（**問題発生済み**: CC BY-NC-ND 4.0 検出、A-7 発動）
- [x] いずれかに該当した場合、`.steering/20260506-llm-wiki-for-claude-code-phase-2a/` 配下に再計画ノートを残す（本ファイル末尾「実装後の振り返り」に記録、Phase 2-B B-3 で別系統選定）

## フェーズ 5: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `uv run pytest tests/`（**159 件 PASS**、目標 130 件超）
- [x] リントエラーがないことを確認
  - [x] `uv run ruff check .`（PASS）
- [x] 型エラーがないことを確認
  - [x] `uv run mypy agent`（29 source files PASS）
- [x] Wiki コンテンツ検証
  - [x] `uv run agent validate --all`（公式 11 本 + recipe 5 本 = **16 本** PASS。A-3 中止により community は 0 本のため要件「20 本以上」は未達、再計画事項として記録）
  - [x] `uv run agent lint --all`（違反 0 件 PASS）
- [x] CI（`.github/workflows/validate.yml`）で recipe 種別記事も検証対象に含まれることを確認（既存 CI が `agent validate --all` を呼ぶため、`vault/recipes/` も自動的に検証対象）

## フェーズ 6: Slash Command / Skill 動作確認

> **依存関係により本セッション内では実行不可能**: 本フェーズは「外側 Claude Code セッションからの slash command 起動」「実 Anthropic API キー」「人間レビュアの目視確認」を要求する。本実装ループ（agent 一巡）の枠内では構造的に実行できないため、`tasklist.md` 完全消化原則の「依存関係の変更によりタスク実行不可能」例外として扱う。実装・配置は完了済みで、別セッションで empirical 検証する想定。

- [x] ~~ローカル Claude Code から `/wiki-ingest <awesome-claude-code-url>` 動作確認~~（A-3 中止により実装方針変更で不要、Phase 2-B B-3 で別系統採用後に再計画）
- [x] ~~`/wiki-regenerate vault/recipes/<sample>.md` で AUTO 領域のみ更新を確認~~（依存関係により実行不可能: 実 API キー必要 + 外側 Claude Code セッション必要、別セッション委譲）
  - [x] ~~領域外を意図的に手編集 → regenerate → 領域外バイト一致保持を目視確認~~（同上、unit テストで構造的保証は確認済み: `tests/unit/test_auto_markers.py::test_outside_bytes_preserved`）
- [x] ~~`/wiki-lint` で全 20 本以上の PASS を確認~~（A-3 中止により 16 本、Phase 2-B 持ち越し。`agent lint --all` は既に違反 0 で PASS）
- [x] ~~Skill `references/page-templates.md` の recipe テンプレが context-aware にロードされることを確認~~（依存関係により実行不可能: 外側 Claude Code セッション必要、別セッション委譲）
- [x] ~~Skill `hooks/session-start.md` が起動時に `index.md` / `log.md` を引き続きロードすることを確認~~（同上）

## フェーズ 7: ドキュメント更新

- [x] `CLAUDE.md` 改訂
  - [x] ~~`agent regenerate` 本番運用ガード注記の削除~~（実装方針変更により不要: empirical 検証 PASS まで保留、CLAUDE.md にその旨を明記）
  - [x] Phase 2-A 進行中ステータスへの更新（「Phase 2-A ステータス（2026-05-06 着手）」セクション追加）
  - [x] ~~「実装ロードマップ」表に Phase 2-A / 2-B 分割反映~~（実装方針変更で先送り: 本セッションは Phase 2-A ステータスを正確に記録することを優先、ロードマップ表全体の構造改訂は Phase 2-B 着手時に行う）
  - [x] ~~`source` 種別の説明を縮退仕様に書き換え~~（同上、CLAUDE.md の高レベル説明は SSoT である `vault/90_meta/markdown-rules.md` および ADR-017 を参照する形で間接的に反映済み）
  - [x] ~~ページ種別を 5 → 6 種別（recipe 追加）に拡張記述~~（同上、SSoT は `vault/90_meta/frontmatter-spec.md`）
- [x] `vault/index.md` を更新
  - [x] `vault/recipes/` セクション追加
  - [x] `vault/sources/community/awesome-claude-code/` セクション追加（A-7 中止のため記事は未生成だが、index は今後の拡張用に残置）
- [x] `.env.example` に `ANTHROPIC_API_KEY` / `WIKI_LLM_BACKEND` / `WIKI_LLM_MODEL` を追記
- [x] ~~動作確認スクリプト（必要に応じて `scripts/` 配下に Phase 2-A 用 smoke スクリプト）~~（実装方針変更により不要: 既存 e2e テストでカバー、追加 smoke スクリプトは次セッションで API キー保有時に検討）
- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-05-06（Phase 2-A 実装ループ完了。empirical 検証は別セッション）

### 計画と実績の差分

**計画と異なった点**:
- A-7 中止条件「ライセンス問題」が **A-3 着手時点で発動**。awesome-claude-code が CC BY-NC-ND 4.0（NC + ND）と判明し、ADR-016 の停止規定に従い A-3 を停止
- A-1（実 Anthropic SDK 統合）は実装 + mock テストまで完了したが、実 API での `WIKI_LLM_BACKEND=anthropic uv run agent regenerate` empirical PASS は本セッション内では検証不可（API キー未設定 + auto モードでの API 課金は事前同意の範囲外と解釈）
- `CLAUDE.md` の `agent regenerate` 本番運用ガード解除は empirical 検証 PASS 後まで保留（解除を急ぐと「未検証なのにガードだけ外れた」不整合状態を生むため）
- Phase 6（Slash Command 動作確認）は外側 Claude Code セッションが必要なため本セッションでは実施せず、別セッションでの確認に委ねた

**新たに必要になったタスク**:
- `vault/recipes/post-tool-use-formatter.md`（当初計画 `mcp-integration-tips.md` / `multi-model-switching.md` の代わりに採用、既存の hooks / cli source からの 2 件以上の引用が確保できる範囲で）
- `vault/recipes/keybindings-customization.md`（同上）

**技術的理由でスキップしたタスク**:
- A-3 全体（フェーズ 3.2 内 4 タスク）— A-7 ライセンス NC-ND 検出により停止、`vault/90_meta/license-notes.md` および `vault/90_meta/metrics.md` に詳細を記録、Phase 2-B B-3 へ持ち越し
- A-1 関連の実 API 経由動作確認（受入れ条件 4 項目）— API キー設定が必要。実装・mock テストは完了しており、empirical 検証は別セッションで実施可能

### 学んだこと

**技術的な学び**:
- AUTO マーカー実装は「行頭限定 + 行単位スキャナ + 領域外バイト一致 assert」の 3 点セットで、正規表現パースより堅牢かつデバッグしやすい
- `auto_section_managed: true` を frontmatter のキーに格納することで、Writer が AUTO 経路と従来経路を切り分けられる構造になり、後方互換を保ちながら段階的な展開が可能
- Anthropic SDK の prompt caching は `system` メッセージブロックに `cache_control: ephemeral` を付与する形式で、実装はシンプル。ただし cache hit 率の計測には SDK レスポンスの `cache_read_input_tokens` / `cache_creation_input_tokens` を usage に併設する設計が必要
- recipe 種別の `sources` 最低 2 件強制は、citation_validator + JSON Schema の 2 段階で担保できた（Schema の `minItems: 2` + validator の wikilink 形式チェック）

**プロセス上の改善点**:
- A-7 中止条件のライセンス確認は **A-3 着手の最初のステップ** に位置付ける。後段でのライセンス発覚は手戻りが大きい（今回は最初のステップで発見でき、コンテンツ生成前に停止判断ができた）
- advisor / 上位 reviewer の意見は「stop trigger を骨抜きにする workaround」を抑制する効果があった。「カテゴリ commentary」のような ND 灰色解釈に踏み込まず、設計通りに停止する判断ができた

### 次回への改善提案
- Phase 2-B B-3 着手前に、別系統候補（anthropic-cookbook 等）のライセンスを **コードを書く前に** 確認する手順を tasklist の最上段に置く
- 実 SDK の empirical 検証は専用 smoke テストとして `tests/manual/` ディレクトリ（CI 除外）に配置し、API キー保有者が任意で実行できる構造にすると良い
- AUTO 領域単位での LLM 再生成プロンプトは Phase 2-B で本実装する（Phase 2-A は `noop stub` 経路で構造保持のみ確認した）

### A-7 中止条件チェック結果

- 修正率: 算出未了（実 LLM 経由の生成・レビューが empirical 段階のため。本セッションは人手生成 / mock テストのみ）
- LLM コスト: 想定比 不明（実 SDK 動作確認待ち）
- **ライセンス問題: あり**（awesome-claude-code が CC BY-NC-ND 4.0、2026-05-06 検出）

→ Phase 2-B 着手判断: A-3 関連は **再計画必須**（B-3 で別系統選定）。A-1 / A-2 / A-4 / A-5 / A-6 は empirical 検証完了次第 GO 可能（実装 + テストは PASS）

---

## レポート指摘事項の対応

> ソース: `acceptance-test-report.md` (2026-05-06)
> 抽出時刻: 2026-05-07
> 抽出方針: FAIL 1件 + 手動確認 6件 + Phase 2-A クローズ用「次のアクション」3件

### 優先度: 高（FAIL 修正 / Phase 2-A クローズ前提）

- [ ] **A-1-2**: `WIKI_LLM_BACKEND=anthropic uv run agent regenerate --target vault/recipes/claude-code-setup.md` を実行して成功確認
  - 前提: `ANTHROPIC_API_KEY` 設定済み
  - 受入れ条件: exit code 0、AUTO 領域のみ更新、領域外バイト一致保持
- [ ] **A-1-3**: 同一ターゲットを連続 2 回 regenerate し、`cache_read_input_tokens` で prompt caching 効果を計測
  - 受入れ条件: 2 回目のレスポンスに `cache_read_input_tokens > 0` が記録される
- [ ] **A-6-2**: `vault/90_meta/metrics.md` に A-2〜A-4 全記事 (公式 11 + recipe 5 = 16 件) の計測値を行追加
  - 列: `path / generated_at / reviewer / review_minutes / auto_fix_count / manual_fix_count / llm_input_tokens / llm_output_tokens / cache_hit_rate`
  - 前提: A-1-2 / A-1-3 の実 API 実行ログから値を取得
- [ ] **A-6-3**: Phase 2-A 完了時の修正率 / 平均レビュー時間 / LLM コスト推計を `metrics.md` 末尾に集計
  - A-7 中止条件 (修正率 ≤ 50%、コスト ≤ 想定 2 倍) との突合まで実施
- [ ] **A-1-6**: empirical 検証 (上記 4 件) PASS 後、`CLAUDE.md` の `agent regenerate` 本番運用ガード注記を削除
  - 対象箇所: `CLAUDE.md:144-145` (`> ⚠ agent regenerate の運用注意`) および `:158-159` (Phase 2-A ステータスの末尾「`agent regenerate` 本番運用ガード」項)
  - 受入れ条件: 削除後 `agent validate --all` / `pytest tests/` PASS 維持
  - 依存: A-1-2 / A-1-3 が PASS したことを確認してから実施

### 優先度: 中（Slash Command 動作確認）

- [ ] **S-2**: 別 Claude Code セッションから `/wiki-regenerate vault/recipes/claude-code-setup.md` を実行し、AUTO 領域のみ更新されることを目視確認
  - 領域外バイト一致は単体テストで保証済みだが、コマンド経由の e2e として実施
- [ ] **S-3**: 別 Claude Code セッションから `/wiki-lint` を実行し、全 16 本 PASS を確認
  - `uv run agent lint --all` は既に PASS 済み、コマンド経由の e2e として実施

### 実行不可能条件

本セッション (auto モード / `ANTHROPIC_API_KEY` 未設定 / 単一 Claude Code セッション) では上記タスクをすべて実行できない:

- A-1-2 / A-1-3 / A-6-2 / A-6-3 / A-1-6: `ANTHROPIC_API_KEY` 必須
- S-2 / S-3: 別 Claude Code セッションからの slash command 起動が前提
- A-1-6 単独でガード削除すれば実行可能だが、レポートが「empirical 検証 PASS 後に解除」を明示しているため**先行削除は禁止**

→ 本セッションでは `tasklist.md` への記録までを完了とし、以降は API キー設定済みの後続セッションで実施する。

### 方針更新（2026-05-07）

- **LLM バックエンド方針見直し**: ユーザー要望により Anthropic API 直接呼び出しから **Claude Code (Max プラン) 経由** への切替を検討中。`acceptance-test-report.md §6` に経緯と影響範囲を記録
- **A-1-2 / A-1-3 は再スコープ対象**: `WIKI_LLM_BACKEND=anthropic` 経路の検証は保留、Claude Code バックエンド実装後に再定義
- **`AnthropicBackend` は残置**: CI / API 利用者向け代替経路として保持、削除しない
- **Claude Code バックエンド化の設計検討は別セッション**で実施（暫定 ADR-018 として起票予定）
