# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを `[x]` にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### 実装可能なタスクのみを計画
- 計画段階で「実装可能なタスク」のみをリストアップ
- 「将来やるかもしれないタスク」は含めない
- 「検討中のタスク」は含めない

### タスクスキップが許可される唯一のケース
以下の技術的理由に該当する場合のみスキップ可能:
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

### タスクが大きすぎる場合
- タスクを小さなサブタスクに分割
- 分割したサブタスクをこのファイルに追加
- サブタスクを 1 つずつ完了させる

---

## フェーズ 1: 規約・スキーマ拡充（AUTO マーカー + 派生 4 種別）

- [ ] ADR-015（AUTO マーカー構文）を `docs/core/decisions.md` に追加
  - [ ] コンテキスト・決定・理由・不採用案・影響を記述
  - [ ] ADR-006 を参照（Phase 2 で実装する旨が既に明記されている）
- [ ] `vault/90_meta/auto-marker-spec.md` を新規作成
  - [ ] 構文: `<!-- AUTO:START -->` 〜 `<!-- AUTO:END -->`、ネスト禁止
  - [ ] 配置位置: `source` 種別の「## 補足解説 (日本語)」配下のみ
  - [ ] 1 記事最大 1 領域
  - [ ] `auto_section_managed: true` での Writer 動作仕様
- [ ] ADR-016（派生種別 concept/entity/synthesis 規約）を `docs/core/decisions.md` に追加
  - [ ] 引用必須（最低件数）と `entity_kind` enum、`query` キーの規定
- [ ] `vault/90_meta/frontmatter-spec.md` を更新
  - [ ] `concept` / `entity` / `synthesis` / `comparison` の必須キーを追記
  - [ ] `entity_kind`（enum: tool/command/person/model）の定義
  - [ ] `compared_targets`（comparison 用、最低 2 件配列）の定義
  - [ ] `query` / `query_executed_at`（synthesis 用）の定義
- [ ] `vault/90_meta/_schemas/frontmatter.schema.json` を更新
  - [ ] `oneOf` で 5 種別の分岐を追加
  - [ ] 各種別の `required` / `properties` を整備
- [ ] `vault/90_meta/markdown-rules.md` を更新
  - [ ] AUTO マーカーの構文・配置ルールを追記
- [ ] `.claude/skills/llm-wiki-for-claude-code/references/page-templates.md` を更新
  - [ ] `concept` / `entity` / `synthesis` / `comparison` の実体テンプレートを追加
  - [ ] 各テンプレートに引用必須のガイダンス
- [ ] `.claude/skills/llm-wiki-for-claude-code/references/auto-marker-spec.md` シンボリックリンクを作成（→ `vault/90_meta/auto-marker-spec.md`）

## フェーズ 2: validator 拡張

- [ ] `agent/validators/frontmatter_validator.py` を 5 種別対応に拡張
  - [ ] JSON Schema の `oneOf` 分岐を読み込み `type` 別に検証
  - [ ] `entity_kind` enum 違反検出
  - [ ] `synthesis` の `query` / `query_executed_at` 欠損検出
  - [ ] `comparison` の `compared_targets` 最低 2 件検証
- [ ] `agent/validators/citation_validator.py` を本実装（Phase 1 のスタブから昇格）
  - [ ] `sources` 配列の最低件数チェック（concept/entity/synthesis: 1 件、comparison: 2 件）
  - [ ] wikilink ターゲット実在チェック
  - [ ] `CitationTargetMissingError` を `agent/errors.py` に追加
- [ ] `agent/validators/markdown_rules_validator.py` に AUTO マーカー検証を追加
  - [ ] START/END ペア整合性
  - [ ] ネスト禁止
  - [ ] `source` 種別以外での使用エラー
  - [ ] 「## 補足解説 (日本語)」以外への配置エラー
  - [ ] 1 記事最大 1 領域
  - [ ] `AutoMarkerInvalidError` を `agent/errors.py` に追加
- [ ] ユニットテスト追加
  - [ ] 5 種別 × 必須キー欠損 / 型不一致 / enum 違反パターン
  - [ ] citation_validator: 引用先存在 / 不在、最低件数違反
  - [ ] markdown_rules_validator: AUTO マーカー孤立・ネスト・配置不正

## フェーズ 3: writer 拡張（AUTO 領域分離書き換え）

- [ ] `agent/writers/markdown_writer.py` に AUTO 領域分離書き換えを追加
  - [ ] AUTO 領域抽出（正規表現 + DOTALL）
  - [ ] `WriteRequest.auto_section_body` パラメータ追加
  - [ ] 領域外バイト一致保持の実装
  - [ ] `AutoMarkerMissingError` を `agent/errors.py` に追加
- [ ] ユニットテスト追加
  - [ ] AUTO 領域抽出
  - [ ] 領域内のみ書き換え、領域外バイト一致保持
  - [ ] AUTO マーカー不在時のエラー
  - [ ] 連続 2 回書き換えで意味のある差分なし（冪等性）
- [ ] 統合テスト追加: `tests/integration/regenerate-auto/`
  - [ ] AUTO 領域のみ書き換え、外側を意図的に編集したテストケースが PASS

## フェーズ 4: Anthropic SDK 統合

- [ ] `pyproject.toml` の `dependencies` に `anthropic>=0.40` を追加
- [ ] `pyproject.toml` の `dependency-groups.dev` に `pytest-httpx>=0.30` を追加
- [ ] `uv sync` で依存解決を確認
- [ ] `agent/orchestration/llm.py` を Anthropic SDK 実装に置換
  - [ ] `AnthropicLLM` クラスを実装
  - [ ] `client.messages.create()` で system に `cache_control: ephemeral` 付きブロック配列を渡す
  - [ ] 既定モデル: `claude-sonnet-4-6`
  - [ ] `--model` フラグでモデル切替（`claude-opus-4-7` 等）
  - [ ] `WIKI_LLM_BACKEND=stub|anthropic` 切替の Factory `make_llm()` 実装
  - [ ] エラー時に `LLMGenerationError` / `LLMQuotaExceededError` を raise
- [ ] `agent/runners/local.py` で `ANTHROPIC_API_KEY` 未設定時のエラー処理（exit 3）
- [ ] ユニットテスト追加（`pytest-httpx` で SDK 呼び出しをモック）
  - [ ] `cache_control: ephemeral` が付与されている
  - [ ] `WIKI_LLM_BACKEND` 切替が動作する
  - [ ] API エラー時の終了コード 3
- [ ] 統合テスト: stub バックエンドで連続 2 回 regenerate の冪等性を確認

## フェーズ 5: drift 記事 2 本の全面書き直し

- [ ] `vault/sources/official/cli/installation.md` を書き直し
  - [ ] 新ドキュメント `code.claude.com/docs/ja/setup` を fetch して raw コンテンツ取得
  - [ ] `agent regenerate --target` 実行（実 Anthropic SDK 経由）
  - [ ] 人手レビュー: 推奨インストール手段（`curl install.sh`）反映を確認
  - [ ] frontmatter 更新: `status: published`, `confidence ≥ 0.7`, `stale: false`
  - [ ] drift コメント削除
- [ ] `vault/sources/official/hooks/overview.md` を書き直し
  - [ ] 新ドキュメント `code.claude.com/docs/ja/hooks` を fetch
  - [ ] `agent regenerate --target` 実行
  - [ ] 人手レビュー: 現行 hook イベント一覧（~20 種）反映を確認
  - [ ] frontmatter 更新: `status: published`, `confidence ≥ 0.7`, `stale: false`
  - [ ] drift コメント削除
- [ ] 両記事の `agent verify-links` PASS 確認

## フェーズ 6: 既存 8 本の `published` 昇格

- [ ] `vault/sources/official/cli/` 配下の `status: reviewed` 4-5 本を精査
  - [ ] 各記事を新ドキュメント基準で個別仕様精査
  - [ ] 補足解説を加筆（必要に応じて）
  - [ ] `status: published`, `confidence ≥ 0.7` に更新
- [ ] `vault/sources/official/hooks/` 配下の `status: reviewed` 4 本を精査
  - [ ] 同上の手順で `published` 化
- [ ] 全 10 本の `agent validate` PASS 確認
- [ ] `vault/log.md` に各昇格の操作履歴を追記

## フェーズ 7: 公式 4 カテゴリ × 5 本以上 = 20 本以上の新規 source 記事生成

- [ ] `vault/90_meta/sources.md` のホワイトリストに 4 カテゴリの URL を追加
- [ ] `vault/sources/official/slash-commands/` に 5 本以上を `agent ingest` で生成
  - [ ] 候補（公式ページに対応）: `overview`, `built-in-commands`, `custom-commands`, `arguments`, `examples` 等から 5 本以上
  - [ ] 各記事を人手レビューし `status: published`, `confidence ≥ 0.7`
- [ ] `vault/sources/official/mcp/` に 5 本以上を生成
  - [ ] 候補: `overview`, `configuration`, `transport`, `auth`, `examples` 等
- [ ] `vault/sources/official/settings/` に 5 本以上を生成
  - [ ] 候補: `overview`, `permissions`, `env`, `hooks-config`, `model-config` 等
- [ ] `vault/sources/official/sdk/` に 5 本以上を生成
  - [ ] 候補: `overview`, `python-sdk`, `typescript-sdk`, `agent-sdk`, `examples` 等
- [ ] 全記事が `agent verify-links` PASS（source_url 200 + 連続 100 文字一致なし）
- [ ] 6 カテゴリ合計で 30 本以上の `source` 種別記事が `published` を満たす

## フェーズ 8: 既存記事への AUTO 領域導入

- [ ] `source` 種別記事 30 本以上の「## 補足解説 (日本語)」配下に AUTO マーカーを配置
  - [ ] 既存補足解説の中で「自動更新したい部分」と「人手で書きたい部分」を区分
  - [ ] AUTO 領域を 1 記事 1 つ配置
- [ ] 各記事の frontmatter `auto_section_managed: true` に切替
- [ ] `agent validate --all` で全記事の AUTO 構文 PASS 確認

## フェーズ 9: 派生種別記事の生成（concept / entity / synthesis 各 5 本以上）

- [ ] `vault/concepts/` に 5 本以上を作成
  - [ ] 候補: `permission-mode`, `hook-lifecycle`, `tool-use-flow`, `mcp-transport`, `slash-command-vs-skill` 等
  - [ ] 各記事の `sources` に最低 1 件の wikilink、引用先実在
  - [ ] `confidence ≥ 0.7`, `status: published`
- [ ] `vault/entities/` に 5 本以上を作成
  - [ ] 候補（entity_kind 別）: `bash-tool` (tool), `read-tool` (tool), `wiki-ingest` (command), `andrej-karpathy` (person), `claude-sonnet-4-6` (model)
  - [ ] 各記事の `entity_kind` を正しく設定
- [ ] `vault/syntheses/` に 5 本以上を蓄積（フェーズ 11 の `/wiki-query` 実運用で生成）

## フェーズ 10: `/wiki-query` 実装

- [ ] `agent/orchestration/query.py` を新規実装
  - [ ] 候補ページ抽出（tags + 全文スコアリング）
  - [ ] 既存 synthesis 検出（`query` フィールド一致）
  - [ ] LLM で集約生成
  - [ ] Writer で `vault/syntheses/<slug>.md` 生成
  - [ ] slug 生成（クエリのハッシュ + slugify）
  - [ ] `--force` フラグで上書き
  - [ ] `QueryDuplicateError` を `agent/errors.py` に追加
- [ ] `agent/runners/local.py` に `query` サブコマンド追加（`agent query --question "..." [--force]`）
- [ ] `.claude/commands/wiki-query.md` を新規配置
  - [ ] 自然言語の指示書として記述、内部で `agent query` を呼ぶ
  - [ ] 規約参照は `@.claude/skills/llm-wiki-for-claude-code/references/...` 経由
- [ ] ユニットテスト追加
  - [ ] 候補抽出スコアリング
  - [ ] 既存 synthesis 検出 + `--force` 動作
  - [ ] slug 衝突時の挙動
- [ ] 統合テスト: `tests/integration/query/`
  - [ ] 自然言語クエリ → synthesis 生成の E2E（stub LLM）
  - [ ] 連続 2 回実行で `--force` なしなら既存検出

## フェーズ 11: `/wiki-query` 実運用 + synthesis 5 本以上蓄積

- [ ] `/wiki-query` で 5 件以上の代表的なクエリを実行
  - [ ] 例: 「hooks と Skills の使い分けは？」「permission mode の挙動は？」「MCP server を localhost で動かすには？」「Claude Agent SDK と Claude Code の違いは？」「hook の終了コードによる挙動の違い」等
- [ ] 生成された `synthesis` 記事を人手レビューし `confidence ≥ 0.7`, `status: published` に昇格
- [ ] `vault/syntheses/` に 5 本以上の `published` 記事が存在することを確認

## フェーズ 12: CI 拡張（verify-links 別ジョブ）

- [ ] `.github/workflows/verify-links.yml` を新規作成
  - [ ] `schedule: cron "0 0 * * 1"`（月曜 UTC 0 時）+ `workflow_dispatch`
  - [ ] `continue-on-error: true`
  - [ ] `uv run agent verify-links` 実行
  - [ ] 失敗時に `actions/github-script` で Issue 起票（タイトル `[verify-links] drift detected: YYYY-MM-DD`）
  - [ ] 権限: `issues: write`, `contents: read` のみ
- [ ] `validate.yml` 本体に `agent verify-links` を含めない（ネットワーク非依存維持を確認）
- [ ] 手動 `workflow_dispatch` で 1 回以上実行し、Issue 起票挙動を確認

## フェーズ 13: 人手レビュー工数の実測

- [ ] `vault/90_meta/metrics.md` を新規作成
  - [ ] カラム: `path`, `created_at`, `review_minutes`, `reviewer`, `auto_fixes`, `manual_fixes`, `notes`
  - [ ] フェーズ 5〜11 で生成・レビューした全記事を記録
- [ ] 集計値を算出し記載
  - [ ] 記事数（`source` / `concept` / `entity` / `synthesis` 別）
  - [ ] 平均レビュー時間（分）
  - [ ] 修正率（manual_fixes / 総変更行数）
  - [ ] PRD KPI（修正率 30% 以下、Phase 3 目標）への到達見込みを評価記載

## フェーズ 14: 運用ガード解除 + ドキュメント整備

- [ ] `CLAUDE.md` の `agent regenerate` 運用ガード文（「本番運用記事に対して呼ばない」）を削除
- [ ] `CLAUDE.md` の Phase 1 ステータスを Phase 2 ステータスに更新
  - [ ] 派生種別記事数、公式 6 カテゴリ展開状況、`/wiki-query` 動作確認、prompt caching 実装等
- [ ] `vault/index.md` の「ページ種別」セクションを Phase 2 で展開済みに更新
- [ ] `vault/overview.md` を Phase 2 完了内容で更新

## フェーズ 15: 品質チェックと修正

- [ ] すべてのテストが通ることを確認
  - [ ] `uv run pytest tests/` （目標: 150 件以上 PASS）
- [ ] リントエラーがないことを確認
  - [ ] `uv run ruff check .`
- [ ] 型エラーがないことを確認
  - [ ] `uv run mypy agent`
- [ ] `agent validate --all` で全記事 PASS
- [ ] `agent lint --all` で違反なしを確認
- [ ] `agent verify-links` を手動実行し、全 source 記事が PASS

## フェーズ 16: 受入れテスト

- [ ] requirements.md の全受け入れ条件チェックリストに対し PASS 判定を記録
- [ ] `.steering/20260506-llm-wiki-for-claude-code-phase-2/acceptance-test-report.md` を作成（Phase 1 と同様の形式）
- [ ] PASS の場合は本ファイルの「実装後の振り返り」を記載

---

## 実装後の振り返り

### 実装完了日
{YYYY-MM-DD}

### 計画と実績の差分

**計画と異なった点**:
- {計画時には想定していなかった技術的な変更点}
- {実装方針の変更とその理由}

**新たに必要になったタスク**:
- {実装中に追加したタスク}
- {なぜ追加が必要だったか}

**技術的理由でスキップしたタスク**（該当する場合のみ）:
- {タスク名}
  - スキップ理由: {具体的な技術的理由}
  - 代替実装: {何に置き換わったか}

**⚠️ 注意**: 「時間の都合」「難しい」などの理由でスキップしたタスクはここに記載しないこと。全タスク完了が原則。

### 学んだこと

**技術的な学び**:
- {実装を通じて学んだ技術的な知見}
- {prompt caching のヒット率実測値、トークンコスト削減効果}
- {AUTO マーカー実装で見つかった edge case}

**プロセス上の改善点**:
- {人手レビュー工数の実測結果、PRD KPI との乖離}
- {Phase 3 へ送るべき項目}

### 次回への改善提案
- {Phase 3（comparison 自動生成、コミュニティソース取り込み、GitHub Actions 週次 cron）に向けた改善}
- {ステアリングファイル / ADR の運用改善}
- {CI / verify-links の改善案}
