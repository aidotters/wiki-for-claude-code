# 設計書: ADR-019 AUTO 領域経路で LLM を実呼び出しする

> 関連 ADR: ADR-019（proposed, 2026-05-08）

## アーキテクチャ概要

既存 `agent regenerate` のパイプラインを「AUTO 領域単位の per-region LLM 呼び出し」に再設計する。AUTO マーカーに `purpose` 属性を導入し、それをディスパッチキーとして per-region prompt テンプレートを選ぶ。

```
agent regenerate --target <path> [--force]
  ↓
parse frontmatter
  ↓
type=source か？ → No: FrontmatterValidationError
  ↓ Yes
HttpFetcher.fetch(source_url)
  ↓
content_hash 比較:
  ├─ 一致 && --force なし → no-op return（冪等性）
  └─ 不一致 or --force → 続行
  ↓
auto_section_managed=true か？
  ├─ Yes（Phase 2-A 縮退仕様）→ AUTO 領域経路（本作業の主対象）
  └─ No → ❌ 旧フルファイル経路（削除）
  ↓
extract_auto_regions(content) → list[AutoRegion(purpose=...)]
  ↓
各領域について:
  prompt = render_prompt(load_prompt(f"auto-region/{purpose}"), {...})
  generated = llm.generate(prompt)
  if not generated.strip(): raise LLMGenerationError
  new_inner_contents.append(generated)
  ↓
replace_auto_regions(path, new_inner_contents)
  ↓
frontmatter 更新（last_updated / source_version / fetched_at）
  ↓
append_log(vault_root, "regenerate", ...)
```

## コンポーネント設計

### 1. `agent/writers/markdown_writer.py` 拡張

**責務**:
- AUTO マーカーから `purpose` 属性を抽出
- `AutoRegion` dataclass に `purpose` フィールドを追加

**実装の要点**:

- 構文: `<!-- AUTO:START purpose=summary-1-paragraph -->` を許容（属性は `key=value` 形式、属性無しの `<!-- AUTO:START -->` も後方互換で許容）
- 属性パースは正規表現で実装（`^<!-- AUTO:START(?:\s+purpose=([a-z0-9-]+))?\s*-->$`）
- `AutoRegion.purpose: str | None` を追加（`None` は属性未指定、orchestrator 側で既定値推論）
- `replace_auto_regions` は不変（マーカー行を変更しないため `purpose` 属性も保持される）
- 既存テストの後方互換性を維持（属性無しマーカーは引き続き有効）

### 2. `agent/orchestration/regenerate.py` 改修

**責務**:
- AUTO 領域経路で per-region LLM 呼び出し
- `purpose` から prompt テンプレを選択
- `--force` フラグの解釈
- 旧フルファイル経路の削除

**実装の要点**:

- 関数シグネチャ拡張: `regenerate_source(..., force: bool = False)`
- content_hash 比較に `force` 条件を追加: `if existing_hash == fetch_result.source_version and not force:`
- `purpose` 既定値推論ヘルパー関数 `_default_purpose(doc_type: str, region_index: int) -> str` を新設:
  - `source` 種別: 全領域 `summary-1-paragraph`
  - `recipe` 種別: 配置順 0 → `recipe-tldr`, 1 → `recipe-steps`, それ以降 → `recipe-additional`（未定義時はエラー）
- 各領域に対して prompt 構築 → `llm.generate` → 結果蓄積 → `replace_auto_regions` で一括書き戻し
- `regenerate.py:117-` の `load_prompt("source-regenerate")` 以降のフルファイル経路を削除
- `_extract_section` ヘルパーが旧経路でしか使われていない場合は削除

### 3. `agent/prompts/auto-region/` ディレクトリ

**責務**:
- per-region prompt テンプレートを集中管理

**実装の要点**:

- `summary-1-paragraph.md`: source 種別の 1 段落要約（3-5 文、日本語）
- `recipe-tldr.md`: recipe TL;DR（1-3 文、日本語）
- `recipe-steps.md`: recipe 手順（番号付きリスト、日本語）
- 各テンプレに次のプレースホルダーを使う:
  - `{source_url}`: 取込み元 URL
  - `{raw_content}`: fetcher で取得した生コンテンツ
  - `{existing_inner}`: 既存の AUTO 領域内テキスト（差分参考用）
  - `{claude_code_version}`: 対象 CC バージョン
  - `{today}`: 実行日
- `agent/orchestration/prompts.py` 既存 `load_prompt` / `render_prompt` を使う（変更不要）

### 4. CLI（`agent/runners/local.py` または `agent/cli.py`）

**責務**:
- `--force` フラグの追加

**実装の要点**:

- 既存 `agent regenerate --target <path>` に `--force` を追加（argparse の `action="store_true"`）
- `regenerate_source(..., force=args.force)` に渡す
- ヘルプメッセージに「content_hash 一致時も LLM を強制呼び出し」と明記

### 5. AUTO マーカー仕様（`vault/90_meta/auto-marker-spec.md`）

**責務**:
- `purpose` 構文・既定値推論ルール・purpose 一覧を文書化

**実装の要点**:

- 構文セクションに `purpose=<value>` の説明を追加
- 既定値推論ルール表を追加（種別 × 配置順）
- purpose 一覧表（現状 `summary-1-paragraph` / `recipe-tldr` / `recipe-steps` の 3 種、Phase 2-B で拡張予定）

### 6. 既存 16 本の AUTO マーカー一括マイグレーション

**責務**:
- 公式 source 11 本 → 全領域 `purpose=summary-1-paragraph`
- recipe 5 本 → 領域順に `recipe-tldr` / `recipe-steps`

**実装の要点**:

- スクリプト `scripts/migrate_auto_purpose.py`（または `sed` 一括）で属性後付け
- 各ページで `extract_auto_regions` を実行し、領域数と既定値推論ロジックの結果と一致することを検証
- 後方互換のため `purpose` 省略でも動作するが、明示する方が運用上明確

## データフロー

### ユースケース 1: 通常の regenerate（content 変化あり）

```
1. user: WIKI_LLM_BACKEND=claude-code agent regenerate --target vault/sources/.../X.md
2. parse frontmatter → type=source, auto_section_managed=true, source_version=H_old
3. fetch source → raw_content, source_version=H_new (≠ H_old)
4. extract_auto_regions → [Region(purpose="summary-1-paragraph")]
5. prompt = render_prompt(template["summary-1-paragraph"], {raw_content, ...})
6. generated = ClaudeCodeBackend.invoke(prompt)  ← 実 LLM 呼び出し
7. replace_auto_regions(path, [generated])
8. frontmatter 更新 → last_updated=today, source_version=H_new, fetched_at=now
9. append_log: "regenerate {rel} (AUTO regions, 1 generated)"
```

### ユースケース 2: --force 指定（content 不変）

```
1. user: agent regenerate --target X.md --force
2. parse frontmatter → source_version=H_old
3. fetch source → source_version=H_old（一致）
4. force=True なので early-return せず続行
5. （以降ユースケース 1 の 4-9 と同じ）
```

### ユースケース 3: content 不変 + --force なし（冪等）

```
1. user: agent regenerate --target X.md
2. fetch source → source_version 一致 && force=False
3. early-return（LLM 呼び出しなし）
4. append_log: "{rel} (no changes)"
```

## エラーハンドリング戦略

### 既存例外を流用

- `FrontmatterValidationError`: `type != source`、`auto_section_managed=true` だが AUTO 領域 0 件
- `MalformedAutoMarkerError`: AUTO マーカー構文不正（`purpose` 属性が不正な形式 `[a-z0-9-]+` 以外）
- `LLMGenerationError`: LLM 応答が空、または応答パース失敗
- `LLMInvocationError`: ClaudeCodeBackend / AnthropicBackend からの SDK 例外（既存）
- `ConfigurationError`: バイナリ未存在、API キー欠如（既存）

### 新規例外なし

- `purpose` 不明（未登録）の場合は `FrontmatterValidationError` を流用（メッセージで「未知の purpose: X」と明示）

## テスト戦略

### ユニットテスト

**`tests/unit/test_auto_markers.py` 拡張**:
- `purpose` 属性パース（正常系: `purpose=summary-1-paragraph` / 属性無し / 不正属性）
- `AutoRegion.purpose` フィールドへの代入検証
- `replace_auto_regions` が `purpose` 属性を保持する（マーカー行不変）

**`tests/unit/test_runner.py` または新規 `test_regenerate_auto.py`**:
- AUTO 経路で `llm.generate` が領域数だけ呼ばれる（mock の call count）
- content_hash 一致 + `--force=False` で LLM 未呼び出し（call count = 0）
- content_hash 一致 + `--force=True` で LLM 呼び出される（call count > 0）
- `purpose` 省略時の既定値推論（source/recipe で異なる）
- LLM 空応答時 `LLMGenerationError`
- 領域外バイト一致が保持される（既存 replace_auto_regions テスト流用）

### 統合テスト

- 既存 `agent validate --all` / `agent lint --all` が全 16 本で PASS（マイグレーション後）
- `regenerate_source` を stub backend で呼び、AUTO 領域に stub 出力が入ることを確認

### empirical テスト（ADR-018 再実施）

- 実 `claude` バイナリ + Max プラン認証で `WIKI_LLM_BACKEND=claude-code agent regenerate --target ... --force` を実行
- 所要時間 1 秒以上（LLM 実走の証拠）
- AUTO 外 diff 0、frontmatter の保持キーが不変

## 依存ライブラリ

新規追加なし。既存の `claude-agent-sdk` / `anthropic` / `pyyaml` を流用。

## ディレクトリ構造

```
agent/
  prompts/
    auto-region/                          # 新規ディレクトリ
      summary-1-paragraph.md              # 新規
      recipe-tldr.md                      # 新規
      recipe-steps.md                     # 新規
    source-regenerate.md                  # 削除（旧フルファイル経路）
  orchestration/
    regenerate.py                         # 改修（AUTO 経路で LLM 呼び出し / --force）
  writers/
    markdown_writer.py                    # 改修（AutoRegion.purpose 追加）
  runners/
    local.py                              # --force フラグ追加
scripts/
  migrate_auto_purpose.py                 # 新規（一括マイグレーション、使い捨て）
tests/
  unit/
    test_auto_markers.py                  # purpose テスト追加
    test_regenerate_auto.py               # 新規（AUTO 経路 LLM 経路）
vault/
  90_meta/
    auto-marker-spec.md                   # 改訂（purpose 仕様追加）
  sources/official/cli/*.md               # 6 本マイグレーション
  sources/official/hooks/*.md             # 5 本マイグレーション
  recipes/*.md                            # 5 本マイグレーション
docs/
  core/
    decisions.md                          # ADR-019 を accepted に昇格、ADR-018 も同様
.steering/20260508-claude-code-llm-backend/
  acceptance-test-report.md               # §2 を [x] で確定
  empirical-checklist.md                  # 結果記録
```

## 実装の順序

1. **AUTO マーカー仕様改訂** — `vault/90_meta/auto-marker-spec.md` に `purpose` 仕様追加（規約先行）
2. **`AutoRegion` 拡張 + パーサ拡張** — `markdown_writer.py` の `extract_auto_regions` を改修、`AutoRegion.purpose` 追加、ユニットテスト追加
3. **prompt テンプレート配置** — `agent/prompts/auto-region/*.md` 3 本作成
4. **`regenerate.py` 改修** — AUTO 経路で LLM 呼び出し、`--force` 対応、旧経路削除
5. **CLI 改修** — `--force` フラグ追加
6. **AUTO 経路 LLM 経路のテスト追加** — mock backend で 3 経路（一致/不一致/force）検証
7. **既存 16 本のマイグレーション** — `purpose` 後付け
8. **`agent validate --all` / `agent lint --all` PASS 確認**
9. **静的検証** — `ruff` / `mypy` / `pytest` 全 PASS
10. **ADR-018 empirical 再実施** — `WIKI_LLM_BACKEND=claude-code agent regenerate --target ... --force` で実走、所要時間と AUTO 外 diff 0 を確認
11. **acceptance-test-report.md §2 を `[x]` で確定**、ADR-019 と ADR-018 を accepted に昇格

## セキュリティ考慮事項

- prompt テンプレートに `raw_content` をそのまま埋め込むため、取込み元 HTML/Markdown に prompt injection が含まれていた場合 LLM が誤誘導される可能性。Phase 2-A の whitelist（公式日本語ドキュメント）の範囲では実害想定低だが、`vault/90_meta/sources.md` のホワイトリスト遵守を継続維持する
- `--force` の悪用（不要な LLM 呼び出し → API コスト増）。Max プラン定額枠主体のため影響低、ただし運用ドキュメントで「empirical / trouble-shooting 用」と明示する

## パフォーマンス考慮事項

- 領域数だけ LLM 呼び出しが発生（recipe 種別は最大 2 領域 = 2 呼び出し）。並列化は Phase 2-B 検討
- content_hash 早期 return が冪等性を保証し、変化なし時の LLM コストを 0 に保つ
- ClaudeCodeBackend は内部キャッシュを持つが本作業のスコープ外

## 将来の拡張性

- `purpose` 種別を追加するだけで Phase 2-B の派生種別（concept / entity / synthesis）に対応可能
- per-region 並列実行（asyncio）への移行余地を残す（現状は逐次）
- `--dry-run` フラグ（生成結果を表示し書き込まない）を将来追加可能
