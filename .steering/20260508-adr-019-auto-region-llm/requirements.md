# 要求内容: ADR-019 AUTO 領域経路で LLM を実呼び出しする

> 関連 ADR: ADR-019（proposed, 2026-05-08）
> 前提となる ADR: ADR-006 / ADR-015 / ADR-017 / ADR-018
> 起票元: ADR-018 empirical 検証時に判明した noop stub の実装ギャップ

## 概要

`agent regenerate` の `auto_section_managed=true` 経路を noop stub から実 LLM 呼び出しに切り替え、AUTO マーカーに `purpose` メタデータを導入する。これにより ADR-018 の `ClaudeCodeBackend` empirical 検証が成立し、Phase 2-A の真の完了条件を満たせるようにする。

## 背景

ADR-015（AUTO マーカー）/ ADR-017（source 縮退仕様）の設計意図は「AUTO 領域は取込み元の最新内容に基づき LLM が再生成する」だった。しかし `agent/orchestration/regenerate.py:94-115` の `auto_section_managed=true` 経路は次の noop stub に留まっている:

```python
# Phase 2-A 時点では「再生成」プロンプトは AUTO 領域単位の生成に未対応のため、
# スタブ動作のみサポート（実 LLM 統合での AUTO 領域差分生成は Phase 2-B）。
new_inner_contents = ["\n".join(r.inner_lines) for r in regions]
replace_auto_regions(target_path, new_inner_contents)
```

結果として、Phase 2-A 縮退仕様（公式 source 11 + recipe 5 = 16 本すべて `auto_section_managed: true`）に対して `agent regenerate` は **どの LLM バックエンドが選ばれていても LLM を一度も呼ばない**。2026-05-08 の ADR-018 empirical 検証で `ClaudeCodeBackend.invoke` が実走しないことが発覚し、本作業の必要性が確定した。

## 実装対象の機能

### 1. AUTO マーカー `purpose` メタデータ

- `<!-- AUTO:START purpose=summary-1-paragraph -->` 形式の構文サポート
- `purpose` 省略時は種別（source/recipe）+ 領域配置順から既定値を推論
- `agent/writers/markdown_writer.py` の `extract_auto_regions` を拡張し、`AutoRegion` dataclass に `purpose: str | None` を追加
- 構文不正時は既存の `MalformedAutoMarkerError` で送出

### 2. per-region プロンプトテンプレート

- `agent/prompts/auto-region/<purpose>.md` ディレクトリを新設
- 最低限以下 3 種類を配置:
  - `summary-1-paragraph.md`: source 種別の 1 段落要約（3-5 文）
  - `recipe-tldr.md`: recipe 種別の TL;DR（1-3 文）
  - `recipe-steps.md`: recipe 種別の手順（番号付きリスト）
- プロンプト変数: `source_url`, `raw_content`, `existing_inner`, `claude_code_version`, `today`

### 3. `agent regenerate` の AUTO 領域経路で LLM 実呼び出し

- AUTO 領域ごとに `purpose` から prompt テンプレを選択し `llm.generate` を呼ぶ
- 各領域の生成結果を `replace_auto_regions` で書き戻し、領域外バイト一致を維持
- content_hash 一致での冪等 early-return は維持（`existing.source_version == fetch.source_version` なら no-op）

### 4. `--force` フラグ

- `agent regenerate --target <path> --force` で content_hash 一致時も LLM を呼び強制再生成
- empirical 検証 / trouble-shooting / 手動再生成で使う

### 5. 旧 `source-regenerate` フルファイル経路の削除

- `regenerate.py:117` 以降のフルファイル再生成経路を削除
- `agent/prompts/source-regenerate.md`（あれば）を削除
- AUTO マーカー必須化（Phase 2-A 縮退仕様）と整合させ、デッドコードを排除

### 6. 既存 16 本の AUTO マーカーへの `purpose` 後付け

- 公式 source 11 本: 全領域に `purpose=summary-1-paragraph`
- recipe 5 本: 各領域に `purpose=recipe-tldr` または `purpose=recipe-steps` を付与
- 既存 AUTO マーカーの構文と互換（属性追加のみ）

### 7. ADR-018 empirical 検証の再実施

- 本実装完了後、`empirical-checklist.md` の手順を `WIKI_LLM_BACKEND=claude-code agent regenerate --target vault/sources/official/cli/basic-usage.md --force` で再実施
- `ClaudeCodeBackend.invoke` が実走することを所要時間（数秒〜十数秒）と AUTO 領域 diff で確認
- `acceptance-test-report.md §2` を `[x]` で確定

## 受け入れ条件

### AUTO マーカー仕様拡張

- [ ] `vault/90_meta/auto-marker-spec.md` に `purpose` 構文・既定値推論ルール・purpose 一覧表が追加されている
- [ ] `<!-- AUTO:START purpose=summary-1-paragraph -->` 形式の構文を `extract_auto_regions` がパース可能
- [ ] `AutoRegion` dataclass に `purpose: str | None` フィールドが追加されている
- [ ] `purpose` 省略時の既定値推論ロジック（種別 + 配置順）が実装されている
- [ ] `tests/unit/test_auto_markers.py` に `purpose` 構文テスト最低 5 件追加

### プロンプトテンプレート

- [ ] `agent/prompts/auto-region/summary-1-paragraph.md` が存在し、source 種別 1 段落要約用の指示を含む
- [ ] `agent/prompts/auto-region/recipe-tldr.md` が存在し、recipe TL;DR 用の指示を含む
- [ ] `agent/prompts/auto-region/recipe-steps.md` が存在し、recipe 手順用の指示を含む
- [ ] 各テンプレに `{source_url}` `{raw_content}` `{existing_inner}` `{claude_code_version}` `{today}` プレースホルダーが含まれる

### regenerate.py 改修

- [ ] `auto_section_managed=true` 経路で各 AUTO 領域に対し `llm.generate` を呼ぶ
- [ ] `purpose` から prompt テンプレを選択するディスパッチロジックが実装されている
- [ ] content_hash 一致時は LLM を呼ばず early-return する（`--force` 指定なし時）
- [ ] `--force` フラグが CLI に追加され、content_hash 一致時も LLM を呼ぶ
- [ ] LLM 応答が空の場合 `LLMGenerationError` を送出する
- [ ] 領域外バイト一致が `replace_auto_regions` により保持されている（既存テストで検証）

### 旧経路削除

- [ ] `regenerate.py:117` 以降のフルファイル再生成経路が削除されている
- [ ] `agent/prompts/source-regenerate.md` が削除されている（存在する場合）
- [ ] 旧経路を呼んでいたテストが削除または AUTO 経路用に書き換えられている

### マイグレーション

- [ ] 公式 source 11 本の AUTO マーカーに `purpose=summary-1-paragraph` が後付けされている
- [ ] recipe 5 本の AUTO マーカーに `purpose=recipe-tldr` または `purpose=recipe-steps` が後付けされている
- [ ] `agent validate --all` が全 16 本で PASS する
- [ ] `agent lint --all` が違反 0 で PASS する

### テスト

- [ ] `tests/unit/test_runner.py` または新規ファイルに AUTO 領域 LLM 経路の mock テスト最低 3 件追加
- [ ] content_hash 一致 / 不一致 / `--force` の 3 経路がそれぞれテストされている
- [ ] `uv run pytest tests/` 全 PASS（181 → 190+ 件想定）
- [ ] `uv run ruff check .` PASS
- [ ] `uv run mypy agent` PASS

### empirical 検証（ADR-018 再実施）

- [ ] `WIKI_LLM_BACKEND=claude-code uv run agent regenerate --target vault/sources/official/cli/basic-usage.md --force` が exit 0 で完了
- [ ] 実行ログに所要時間（秒）が出力され、**1 秒以上**である（LLM が実走している証拠）
- [ ] `git diff` で AUTO 領域内のみ変更され、AUTO 外は不変
- [ ] frontmatter の `last_updated` / `source_version` / `fetched_at` が更新される
- [ ] frontmatter の `status` / `confidence` / `reviewer` / `human_edited` が保持される
- [ ] `.steering/20260508-claude-code-llm-backend/acceptance-test-report.md §2` が `[x]` で埋まる

### ADR 更新

- [ ] ADR-019 の Status を `proposed` → `accepted` に昇格
- [ ] ADR-018 の empirical 検証 PASS を受けて Status を `proposed` → `accepted` に昇格

## 成功指標

- 定量: テスト件数 181 → 190+ 件 PASS、全 16 本の `agent regenerate` が LLM 実走で AUTO 領域更新可能
- 定量: ADR-018 empirical 検証 4 項目すべて `[x]`
- 定性: `regenerate.py` のデッドコード（`source-regenerate` フルファイル経路）が消え、AUTO 経路が唯一の生成経路になる
- 定性: Phase 2-A の CONDITIONAL_PASS が正式 PASS に昇格

## スコープ外

以下は本作業では実装しません:

- `purpose` 種別の追加（`concept-summary` / `entity-overview` 等）— Phase 2-B で派生種別実装時に追加
- AUTO 領域差分の最小化（生成結果が既存内容と同一なら書き込みしない最適化）— Phase 2-B
- `--dry-run` フラグ（生成結果を表示するだけで書き込まない）— 別作業
- `metrics.md` への 16 本修正率記録 — empirical PASS 後の別 PR で実施（ADR-018 の影響欄に記載）
- `make_backend()` 既定値の `claude-code` 昇格 — empirical PASS 後の別 PR

## 参照ドキュメント

- `docs/core/decisions.md` ADR-019（本作業の決定根拠）
- `docs/core/decisions.md` ADR-015 / ADR-017 / ADR-018（前提）
- `vault/90_meta/auto-marker-spec.md`（AUTO マーカー現行仕様）
- `agent/orchestration/regenerate.py`（改修対象）
- `agent/writers/markdown_writer.py`（`AutoRegion` 拡張対象）
- `.steering/20260508-claude-code-llm-backend/empirical-checklist.md`（再実施対象）
- `.steering/20260508-claude-code-llm-backend/acceptance-test-report.md`（§2 更新対象）
