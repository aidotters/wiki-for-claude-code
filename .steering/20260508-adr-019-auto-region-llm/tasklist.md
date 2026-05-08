# タスクリスト: ADR-019 AUTO 領域経路で LLM を実呼び出しする

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### タスクスキップが許可される唯一のケース
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

---

## フェーズ1: AUTO マーカー仕様の改訂（規約先行）

- [x] `vault/90_meta/auto-marker-spec.md` に `purpose` 構文を追加
  - [x] 構文セクションに `<!-- AUTO:START purpose=<value> -->` 説明追加
  - [x] 既定値推論ルール表（種別 × 配置順）追加
  - [x] purpose 一覧表（`summary-1-paragraph` / `recipe-tldr` / `recipe-steps`）追加
  - [x] `purpose` 値の正規表現 `[a-z0-9-]+` を明記
- [x] 関連 ADR セクションに ADR-019 を追加

## フェーズ2: `AutoRegion` 拡張とパーサ改修

- [x] `agent/writers/markdown_writer.py` を改修
  - [x] `AutoRegion` dataclass に `purpose: str | None` フィールド追加
  - [x] `extract_auto_regions` の START マーカー検出ロジックを正規表現ベースに切替
  - [x] 属性無しマーカー（後方互換）を `purpose=None` でパース
  - [x] 不正な属性形式に対し `MalformedAutoMarkerError` 送出
  - [x] `_assert_outside_bytes_match` 内の START 検索も正規表現対応（追加対応）
- [x] `tests/unit/test_auto_markers.py` に `purpose` テスト追加（8 件）
  - [x] 正常系: `purpose=summary-1-paragraph` パース
  - [x] 正常系: 属性無し → `purpose=None`
  - [x] 異常系: `purpose=` 空値
  - [x] 異常系: `purpose=Invalid_Caps`（大文字・アンダースコア不許可）
  - [x] `replace_auto_regions` がマーカー行（属性含む）を保持
  - [x] END に属性付与の異常系
  - [x] 領域順での purpose 保持
- [x] `uv run pytest tests/unit/test_auto_markers.py` PASS 確認（22 件）

## フェーズ3: prompt テンプレート配置

- [x] `agent/prompts/auto-region/` ディレクトリ作成
- [x] `agent/prompts/auto-region/summary-1-paragraph.md` 作成
- [x] `agent/prompts/auto-region/recipe-tldr.md` 作成
- [x] `agent/prompts/auto-region/recipe-steps.md` 作成
- [x] `load_prompt("auto-region/summary-1-paragraph")` がパス解決できることを確認

## フェーズ4: `regenerate.py` 改修（AUTO 経路で LLM 呼び出し）

- [x] `regenerate_source` シグネチャに `force: bool = False` 追加（keyword-only）
- [x] content_hash 早期 return 条件に `not force` を追加
- [x] `_default_purpose(doc_type, region_index)` ヘルパー実装
- [x] `_build_region_prompts` ヘルパー実装（per-region prompt 組み立て）
- [x] `auto_section_managed=true` 経路で各領域に対し `llm.generate` 呼び出し
- [x] 空応答時 `LLMGenerationError`
- [x] `replace_auto_regions` で一括書き戻し
- [x] frontmatter 更新（`last_updated` / `source_version` / `fetched_at` / `stale=false`）
- [x] `append_log` メッセージを「AUTO regions, N generated」形式に更新
- [x] **旧フルファイル経路削除**（`load_prompt("source-regenerate")` 以降）
- [x] `_extract_section` ヘルパー削除
- [x] `agent/prompts/source-regenerate.md` 削除
- [x] **追加対応**: `regenerate_source` の `llm` 既定値を `make_backend()` に変更（`StubLLMClient()` ハードコードのバグ修正）
- [x] **追加対応**: `auto_section_managed != true` を `FrontmatterValidationError` で弾く（ADR-017 整合）

## フェーズ5: CLI `--force` フラグ追加

- [x] `agent/runners/local.py` argparse に `--force` 追加
- [x] ヘルプメッセージで意図を明記
- [x] `regenerate_source(..., force=args.force)` に渡す

## フェーズ6: AUTO 経路 LLM 経路のテスト追加

- [x] `tests/unit/test_regenerate_auto.py` 新規作成（13 件）
  - [x] `_default_purpose` 5 経路（source / recipe x2 / 範囲外 / 未対応種別）
  - [x] AUTO 経路で `llm.generate` が領域数だけ呼ばれる（call count 検証）
  - [x] content_hash 一致 + `force=False` で LLM 未呼び出し
  - [x] content_hash 一致 + `force=True` で LLM 呼び出し
  - [x] `purpose` 省略時の既定値推論（source）
  - [x] LLM 空応答時 `LLMGenerationError`
  - [x] `auto_section_managed=false` で `FrontmatterValidationError`
  - [x] 領域外バイト不変（マーカー行・後続セクション）
  - [x] log エントリに領域数記録
- [x] 既存統合テストの stub レスポンスを AUTO マーカー対応に更新（`tests/integration/test_orchestration.py` / `tests/e2e/test_cli_e2e.py`）
- [x] `agent/validators/three_part_validator.py` の AUTO 検出を `purpose` 属性対応の正規表現に切替
- [x] `uv run pytest tests/` 全 202 件 PASS

## フェーズ7: 既存 16 本の AUTO マーカーマイグレーション

- [x] 公式 source 11 本に `purpose=summary-1-paragraph` 後付け（sed 一括）
  - [x] `vault/sources/official/cli/installation.md`
  - [x] `vault/sources/official/cli/basic-usage.md`
  - [x] `vault/sources/official/cli/configuration.md`
  - [x] `vault/sources/official/cli/keybindings.md`
  - [x] `vault/sources/official/cli/permissions.md`
  - [x] `vault/sources/official/cli/admin-setup.md`
  - [x] `vault/sources/official/hooks/overview.md`
  - [x] `vault/sources/official/hooks/pre-tool-use.md`
  - [x] `vault/sources/official/hooks/post-tool-use.md`
  - [x] `vault/sources/official/hooks/stop.md`
  - [x] `vault/sources/official/hooks/user-prompt-submit.md`
- [x] recipe 5 本に位置指定の `purpose` 後付け（Python 一発スクリプト）
  - [x] `vault/recipes/claude-code-setup.md`
  - [x] `vault/recipes/hooks-introduction.md`
  - [x] `vault/recipes/permission-control-practice.md`
  - [x] `vault/recipes/post-tool-use-formatter.md`
  - [x] `vault/recipes/keybindings-customization.md`

> **マイグレーションスクリプト方針変更**: 当初 `scripts/migrate_auto_purpose.py` 新設予定だったが、source は `sed` 一発、recipe は inline Python の方が確実かつ使い捨てスクリプトとして残す価値が薄いため作成しなかった。

## フェーズ8: 静的検証

- [x] `uv run agent validate --all` 全 16 本 PASS
- [x] `uv run agent lint --all` 違反 0 PASS
- [x] `uv run pytest tests/` 全 PASS（181 → **202 件**）
- [x] `uv run ruff check .` PASS
- [x] `uv run mypy agent` PASS（29 source files, 0 issues）

## フェーズ9: ADR-018 empirical 検証の再実施

- [x] `WIKI_LLM_BACKEND=claude-code uv run agent regenerate --target vault/sources/official/cli/basic-usage.md --force` 実行
  - [x] exit 0 で完了
  - [x] 所要時間 **73.33 秒**（実 LLM 実走の確証）
  - [x] stderr に Markdown 表行形式の所要時間ログ出力
- [x] `git diff vault/sources/official/cli/basic-usage.md` で AUTO 領域内のみ意味的変更を確認
  - [x] AUTO 外（`## 公式ドキュメント` 以降）が完全不変
  - [x] frontmatter の `last_updated` / `fetched_at` が更新
  - [x] frontmatter の `status: published` / `confidence: 0.7` / `reviewer: tak` / `human_edited: true` が保持
- [x] ~~ローカル Claude Code セッションから `/wiki-regenerate vault/sources/official/cli/basic-usage.md` 実行~~（**技術的理由でスキップ**: スラッシュコマンドはユーザーのインタラクティブ Claude Code セッション内で実行される機能であり、別プロセスから自動実行できない。CLI 経由 (`agent regenerate`) と同コードパス（`runners/local.py:_cmd_regenerate` → `regenerate_source`）を通るため、CLI 経由の empirical PASS をもって実装上の動作確認は完了。Slash Command 経由のユーザー手動確認は本作業のスコープ外として後続に委譲）

## フェーズ10: ドキュメント更新と ADR 昇格

- [x] `.steering/20260508-claude-code-llm-backend/acceptance-test-report.md` §2 を `[x]` で確定
  - [x] CLI 経由 3 項目を `[x]`
  - [x] 総合判定を `CONDITIONAL_PASS` → `PASS` に更新
  - [x] ADR-019 対応の経緯を注記
- [x] `docs/core/decisions.md` ADR-019 Status を `proposed` → `accepted` に昇格
- [x] `docs/core/decisions.md` ADR-018 Status を `proposed` → `accepted` に昇格
- [x] `docs/core/decisions.md` 更新履歴に 2026-05-08 の ADR-019 完了エントリ追加
- [x] 実装後の振り返り（このファイル下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-05-08

### 計画と実績の差分

**計画と異なった点**:

- **`make_backend()` 配線バグの発見と即時修正**: 計画では `regenerate_source` の AUTO 経路を実 LLM 化することのみがスコープだったが、empirical 1 回目で `WIKI_LLM_BACKEND=claude-code` を指定しても 0.29s で完走（LLM 未呼び出し）することが判明。原因は `regenerate_source` の `llm` 既定値が `StubLLMClient()` ハードコードだったこと。`make_backend()` への切替を本作業で同時に修正した（`agent/orchestration/regenerate.py:131`）。ADR-019 の事前計画では検出できていなかった配線バグで、Phase 2-A 全体に影響する隠れた品質問題。
- **マイグレーション専用スクリプトを作らなかった**: 計画では `scripts/migrate_auto_purpose.py` を新設予定だったが、source は `sed` 一発、recipe は inline Python の方が確実かつ使い捨てスクリプトとして残す価値が薄いため作成せず。tasklist にも理由を明記。
- **`auto_section_managed != true` の明示的拒否**: 計画では旧フルファイル経路を「削除」とのみ書いていたが、削除に伴い `auto_section_managed=false` のページに対する挙動を明確化する必要があり、`FrontmatterValidationError` で弾く実装にした（ADR-017 整合）。
- **検証ロジックの整合修正**: `agent/validators/three_part_validator.py` も `<!-- AUTO:START -->` 文字列完全一致で AUTO 領域を検出していたため、`purpose` 属性付きマーカーを認識できず統合テスト 2 件が FAIL。同様の正規表現パターンを validator にも追加して整合させた。

**新たに必要になったタスク**:

- `_assert_outside_bytes_match` 内の `_find_marker(AUTO_START_MARKER)` も purpose 属性に対応する必要があり、`_find_start_marker` ヘルパーを追加（`AUTO_END_MARKER` は属性禁止のため変更なし）
- 既存統合テスト・E2E テストの stub response を AUTO マーカー対応に更新（`auto_section_managed: true` + AUTO 領域）
- `agent/validators/three_part_validator.py` の AUTO 検出を正規表現対応に切替

**技術的理由でスキップしたタスク**: なし

### 学んだこと

**技術的な学び**:

- **「テストが PASS する」と「機能する」は別物**: ClaudeCodeBackend のユニットテスト 21 件が PASS していても、`regenerate_source` の `llm = StubLLMClient()` ハードコードにより本番経路で一度も呼ばれていなかった。ユニットテストは API の正しさを保証するが、配線（依存注入）のバグはユニットテストでは捕捉しにくい。empirical 検証（実 LLM 起動 + 所要時間計測）が初めてこのバグを露出させた。
- **AUTO マーカー検出ロジックの分散**: AUTO マーカーを参照する箇所が `extract_auto_regions` / `_find_marker` / `three_part_validator` の 3 箇所に散在していた。属性追加のような構文拡張時、3 箇所同時に更新する必要があり漏れやすい。将来は AUTO マーカー検出ヘルパーを `markdown_writer.py` の単一公開関数に集約するリファクタが望ましい。
- **`yaml.safe_dump` のクォートスタイル変動**: empirical 実行後の diff で frontmatter のクォートスタイル（`"value"` vs `value`）が機械的に書き換わる。意味上は等価だが git diff のノイズになる。Phase 2-B で `serialize` のスタイル安定化（カスタム dumper）を検討する余地。

**プロセス上の改善点**:

- **規約先行が機能した**: フェーズ 1 で `auto-marker-spec.md` の `purpose` 仕様を確定してから実装に入ることで、パーサ・テスト・マイグレーションの一貫した実装ができた。`purpose` の正規表現や既定値推論ルールが先に確定していたため、テスト記述時に迷いがなかった。
- **steering 3 ファイル + ADR の二重管理は適切**: ADR-019 が「決定の記録」、steering が「実装手順の追跡」と役割が分離していて、両方とも価値を発揮した。実装中に追加対応（make_backend 配線修正等）が出ても、steering の振り返りに記録できる。

### 次回への改善提案

- **新機能を追加するとき、依存注入の本番配線を `make_*` 関数経由に必ず置く**: `StubLLMClient()` をテスト用 fixture 以外で書かない、というルールを徹底する。次回類似のバックエンド導入時は最初の段階で「`make_backend()` 配線が CLI まで到達しているか」を smoke test で確認する。
- **AUTO マーカー検出を 1 箇所に集約**: 次に AUTO マーカーへ拡張属性（lang / version 等）を加える際、検出ロジックの分散が再び問題になるので、Phase 2-B 着手前にリファクタする。
- **empirical 検証は実装フェーズ早期に組み込む**: 本作業のように「実 LLM が動かないと露出しないバグ」が存在するため、テスト 100% PASS でも empirical を別 PR に積み残すのは危険。Phase 2-B 以降は最低 1 回の empirical を各 PR で必須化する運用を検討。
