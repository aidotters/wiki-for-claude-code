# コード検証レポート

> 生成日時: 2026-05-08
> 対象: `.steering/20260506-llm-wiki-for-claude-code-phase-2a/`
> 検証範囲: agent/ 層（orchestration / writers / validators / fetchers / errors）+ vault/ コンテンツ + tests/

## エグゼクティブサマリー

| 検証項目 | 結果 | 詳細 |
|----------|------|------|
| スペック整合性 | CONDITIONAL_PASS | 41 受入れ条件中 28 PASS、1 FAIL（A-1-6: 運用判断で保留）、6 中止条件発動（A-7 で正当化）、6 empirical 検証は別セッション |
| コード品質 | PASS | ruff: All checks passed / mypy: 29 source files OK |
| テストカバレッジ | PASS | **159 件 PASS**（目標 130 件超、Phase 1: 107 件 → +52） |
| セキュリティ | PASS | 機密のハードコードなし、危険パターン（eval/exec/shell=True 等）検出なし |
| パフォーマンス | PASS | prompt caching 実装済み、httpx クライアント再利用、AUTO 領域差分 update |
| **総合判定** | **CONDITIONAL_PASS** | empirical 検証（A-1-2 / A-1-3）と CLAUDE.md ガード削除（A-1-6）が別セッション持ち越し |

---

## 1. スペックとの整合性

### 主要受入れ条件のトレーサビリティ

| 機能 | 条件 | 結果 | 根拠 |
|------|------|------|------|
| A-1 | `LLMBackend` Protocol + Stub/Anthropic 並列 | PASS | `agent/orchestration/llm.py:61-71`（Protocol 定義）、`:73-98` Stub、`:101-169` Anthropic |
| A-1 | 既定モデル `claude-sonnet-4-6`、`WIKI_LLM_MODEL` 上書き可 | PASS | `agent/orchestration/llm.py:21,117` |
| A-1 | `ANTHROPIC_API_KEY` 未設定時 `ConfigurationError` (exit 3) | PASS | `agent/orchestration/llm.py:124-128`、`agent/errors.py:58-61` |
| A-1 | 1 回リトライ後 `LLMInvocationError` | PASS | `agent/orchestration/llm.py:145-161` |
| A-1 | system プロンプトに `cache_control: ephemeral` 付与 | PASS | `agent/orchestration/llm.py:141-143` |
| A-1 | 実 API empirical PASS（A-1-2/A-1-3） | **手動** | API キー必須、別セッション |
| A-1 | `CLAUDE.md` ガード注記削除（A-1-6） | **FAIL** | `CLAUDE.md` にガード残存（運用判断で empirical PASS まで保留） |
| A-2 | 公式 source 11 本（cli 6 + hooks 5）縮退仕様 | PASS | 全件 AUTO 領域あり、`status: published`、`confidence: 0.7` |
| A-2 | drift 記事 2 本 `stale: false` | PASS | `installation.md` / `overview.md` 両方解除 |
| A-3 | awesome-claude-code 取込み 5 本 | A-7 中止 | CC BY-NC-ND 4.0 検出 → `enabled: false`、Phase 2-B B-3 持ち越し |
| A-4 | recipe 種別必須キー（`use_case`, `sources≥2`） | PASS | `agent/validators/citation_validator.py:44-52`、JSON Schema oneOf |
| A-4 | `vault/recipes/` 5 本配置 | PASS | claude-code-setup / hooks-introduction / permission-control-practice / post-tool-use-formatter / keybindings-customization |
| A-4 | recipe `sources` wikilink 形式強制 | PASS | `citation_validator.py:55-85` で wikilink 形式 + `sources/` 配下チェック |
| A-5 | AUTO マーカー抽出 + バイト一致保持 | PASS | `agent/writers/markdown_writer.py:82-219`（行単位スキャナ + `_assert_outside_bytes_match`） |
| A-5 | 構文不正で `MalformedAutoMarkerError` | PASS | ネスト/順序不正/行頭以外/対応不一致を 5 種類で検出 |
| A-5 | 公式 11 + recipe 5 = 16 本に AUTO 領域 | PASS | grep で全 16 本に START/END マーカー確認 |
| A-6 | `metrics.md` 列定義（9 列）記載 | PASS | `vault/90_meta/metrics.md:8-18` |
| A-6 | 個別記事行の追記（A-6-2/A-6-3） | **手動** | empirical 計測待ち、表ヘッダのみ存在 |
| A-7 | 中止条件発動時の記録運用 | PASS | `metrics.md:68-86` で CC BY-NC-ND 検出と判定を記録 |
| 共通 | テスト 130 件以上 | PASS | **159 件**（目標 +29 件達成） |
| 共通 | ADR-015 / ADR-016 / ADR-017 起票 | PASS | `docs/core/decisions.md` で 3 件確認 |

### 設計との整合性

| 設計項目（design.md） | 実装 | 結果 |
|----------------------|------|------|
| `LLMBackend` Protocol → `StubBackend` / `AnthropicBackend` 2 実装 | `agent/orchestration/llm.py` | PASS |
| AUTO 抽出は正規表現を使わず行単位スキャナ | `markdown_writer.py:88-124`（`for i, line in enumerate(lines)`） | PASS |
| 領域外バイト一致を post-condition で assert | `markdown_writer.py:166`（`_assert_outside_bytes_match`） | PASS |
| `awesome-claude-code` fetcher は GitHub raw + ホワイトリスト連携 | `agent/fetchers/awesome_claude_code.py:64-77` | PASS |
| recipe 種別の dispatch（既存 source/concept/entity パターン踏襲） | `citation_validator.py:16` で `DERIVED_TYPES` に追加 | PASS |
| カスタムエラー階層と exit code（3=Config/LLM、4=AutoMarker） | `agent/errors.py` | PASS |

## 2. コード品質

### ruff check
```
All checks passed!
```

### mypy
```
Success: no issues found in 29 source files
```

### ベストプラクティス

| 項目 | 状態 | コメント |
|------|------|----------|
| エラーハンドリング | OK | 全例外型に exit code を割当、`agent/errors.py:1-17` で対応表をドキュメント化 |
| ログ出力 | OK | `nav_files.append_log` で操作ログを log.md に追記、各 orchestration から呼び出し |
| 単一責任 | OK | fetchers / writers / validators / orchestration が層分離されている |
| DRY 原則 | OK | `LLMBackend` Protocol で stub/anthropic 共通化、`StubLLMClient.invoke` で後方互換 |
| 型安全 | OK | `from __future__ import annotations` 統一、`Protocol` 活用、Optional の明示 |
| TODO/FIXME 残存 | OK | agent/ 配下に TODO/FIXME 残存なし |

### 微細な改善余地（優先度: 低）

- `agent/orchestration/llm.py:155` の `except Exception as e:  # noqa: BLE001` は意図的な広域捕捉だが、テスト用 mock（`Exception` を投げる）では問題なし。実 SDK 例外型（`anthropic.APIError` 等）への絞り込みは Phase 2-B で検討可能
- `agent/fetchers/awesome_claude_code.py:53` の `client: httpx.Client | None` は `_get_client` で遅延生成。`__post_init__` で生成してもよいが、テスト容易性のため現行で許容

## 3. テストカバレッジ

### テスト件数（159 件 PASS）

| ファイル | 件数 | カバレッジ対象 |
|----------|------|----------------|
| `tests/unit/test_auto_markers.py` | 14 | `markdown_writer.extract_auto_regions` / `replace_auto_regions` |
| `tests/unit/test_awesome_claude_code.py` | 11 | `awesome_claude_code.AwesomeClaudeCodeFetcher` |
| `tests/unit/test_citation_recipe.py` | 5 | recipe 種別の citation 検証 |
| `tests/unit/test_frontmatter_recipe.py` | 4 | recipe 必須キー / Schema 検証 |
| `tests/unit/test_llm_anthropic.py` | 15 | AnthropicBackend mock / API キー欠落 / cache_control 付与 |
| `tests/unit/test_markdown_writer.py` | 6 | 既存 + AUTO 統合 |
| その他既存 | 104 | Phase 1 継承テスト |
| **合計** | **159** | |

### テスト品質

| 種類 | 件数 | 状態 |
|------|------|------|
| 正常系 | 多数 | OK（各機能の標準フロー） |
| 異常系 | 多数 | OK（API キー欠落、構文不正、ホワイトリスト違反、wikilink 不正等を網羅） |
| エッジケース | 多数 | OK（AUTO 領域 0 件 / 1 件 / 複数件、ネスト、順序不正、行頭以外配置） |
| 境界値 | OK | recipe `sources < 2` で 1 件、空文字列、空リスト |

### カバレッジ計測

- pytest-cov 未導入のため数値カバレッジは未取得（pyproject.toml の addopts と未整合）
- 実装ファイルの行数とテスト件数の比から、主要パスは十分にカバーされていると判断
- 推奨対応（優先度: 低）: 必要に応じて Phase 2-B で `pytest-cov` 導入とカバレッジ閾値設定

## 4. セキュリティ

### 検出された問題

| 重大度 | カテゴリ | ファイル | 行 | 内容 |
|--------|----------|----------|-----|------|
| - | - | - | - | 検出された問題なし |

### セキュリティチェックリスト

| 項目 | 状態 | 根拠 |
|------|------|------|
| 機密情報のハードコード | OK | `ANTHROPIC_API_KEY` は `os.environ.get` 経由のみ（`llm.py:124`）、`.env` 取り扱いは `.gitignore` 既存 |
| インジェクション対策 | OK | `eval`/`exec`/`os.system`/`subprocess(...shell=True)`/`pickle.load`/`yaml.load(` の使用なし |
| 入力検証 | OK | URL は whitelist（`sources.md`）でホワイトリスト検証、`http_fetcher` で HTTPS 制限、`citation_validator` で wikilink 形式強制 |
| ファイルパス | OK | `target_path.resolve()` / `relative_to(vault_root)` で path traversal を抑止 |
| 外部依存（httpx） | OK | `follow_redirects=True` だが whitelist 経由で起点 URL を制限済み |
| エラー漏洩 | OK | カスタム例外メッセージにキー値を含めない（`ConfigurationError` は欠落事実のみ） |

## 5. パフォーマンス

### パフォーマンスチェックリスト

| 項目 | 状態 | コメント |
|------|------|----------|
| prompt caching | OK | `system` ブロックに `cache_control: ephemeral` 付与（`llm.py:141-143`）、`LLMUsage.cache_hit_rate` で計測可能 |
| HTTP クライアント再利用 | OK | `AwesomeClaudeCodeFetcher._get_client` で httpx.Client を遅延生成・再利用 |
| AUTO 領域差分更新 | OK | regenerate.py:94-115 で `auto_section_managed=true` 時は AUTO 領域のみ更新（領域外バイト一致保持） |
| メモリ効率 | OK | README は一括 read（`response.text`）だが、Phase 2-A スコープでは記事数 ~20 本のため問題なし |
| N+1 問題 | OK | バルク処理は `agent validate --all` 等で一括 read のみ、API call ループはなし |
| リソース解放 | OK | `with open` 不使用（`Path.read_text/write_text` は内部で close）、httpx.Client は再利用前提 |

### 検出された問題

なし。

## 6. 推奨事項

### 優先度: 高（修正必須）

なし。FAIL の A-1-6（CLAUDE.md ガード削除）は acceptance-test-report.md `§3` で「empirical 検証 PASS 後」と運用順序が明確に決まっているため、本セッションで先行削除しない判断は妥当。

### 優先度: 中（empirical 検証セッションで実施）

- **A-1-2**: `WIKI_LLM_BACKEND=anthropic uv run agent regenerate --target vault/recipes/claude-code-setup.md` で実 API 動作確認（API キー必須）
- **A-1-3**: 連続 2 回 regenerate で `cache_read_input_tokens > 0` を確認
- **A-6-2 / A-6-3**: 上記実行ログから `metrics.md` に 16 本分の行を追加し、修正率を算出
- **A-1-6**: 上記 PASS 後に `CLAUDE.md` ガード注記削除
- **S-2 / S-3**: 別 Claude Code セッションから slash command 経由で動作確認

### 優先度: 低（Phase 2-B 検討）

- `pytest-cov` 導入とカバレッジ閾値設定（現状は件数ベースの担保のみ）
- `agent/orchestration/llm.py:155` の `except Exception` を `anthropic.APIError` 等に絞り込み
- `agent metrics` サブコマンド導入による metrics.md 自動追記化（現在は手動更新運用）
- LLM バックエンド方針の Claude Code 経由化検討（acceptance-test-report.md §6 で起票、ADR-018 予定）

## 7. 次のアクション

- [ ] empirical 検証セッションで A-1-2 / A-1-3 実行（API キー設定済み環境）
- [ ] `metrics.md` に 16 本分の計測値追記、修正率算出（A-6-2 / A-6-3）
- [ ] empirical PASS 後、`CLAUDE.md` の `agent regenerate` ガード注記削除（A-1-6）
- [ ] 別 Claude Code セッションから `/wiki-regenerate` / `/wiki-lint` の e2e 動作確認（S-2 / S-3）
- [ ] LLM バックエンドの Claude Code 経由化検討（暫定 ADR-018 起票）

---

## 補足: Phase 2-A 完了状態の評価

Phase 2-A の中核実装（A-1〜A-7 の規約・ADR・コード・テスト・コンテンツ）はすべて完了しており、`acceptance-test-report.md` の総合判定 **CONDITIONAL_PASS** と本検証結果は整合する。残課題は API キー必須の empirical 検証および別セッション起動が必要な slash command 動作確認のみで、これは要件側でも別セッション持ち越しが明記されている運用前提と一致する。

A-3（awesome-claude-code）の中止は **A-7 中止条件メカニズムが正常に作用した** ことの実証であり、tasklist.md / metrics.md / sources.md / license-notes.md で経緯が追跡可能な状態に整理されている。Phase 2-B B-3 で別系統に切替予定。
