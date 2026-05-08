# empirical 検証チェックリスト: `ClaudeCodeBackend`

> **実施結果**: 2026-05-08 に CLI 経由 PASS（73.33s で `ClaudeCodeBackend.invoke` 実走を確認）。Slash Command 経由はユーザー手動実施（CLI と同コードパスのため実装上 PASS 判断）。
> **前提条件の修正**: 当初想定の対象 `vault/recipes/claude-code-setup.md` は `agent regenerate` 非対応（`type=source` 限定）のため、`vault/sources/official/cli/basic-usage.md` に変更。
> **ADR-019 対応**: 1 回目の実行（0.30s）で AUTO 領域経路が noop stub のため LLM 未呼び出しと判明し、ADR-019 で AUTO 経路を実 LLM 化 + `--force` フラグ追加 + `make_backend()` 配線修正を実施したうえで再実行（73.33s で PASS）。

## 前提条件

- [x] `claude` バイナリが PATH に存在する（`/Users/tak/.local/bin/claude` v2.1.133 確認）
- [x] Claude Code が Max プランで認証済み
- [x] 本リポジトリのワーキングコピーで `uv sync` 済み
- [x] `vault/sources/official/cli/basic-usage.md` が `type: source` / `auto_section_managed: true` で AUTO 領域を含む（ADR-019 マイグレーション後）

> **対象を `type=source` に限定する理由**: 現行 `agent regenerate`（`agent/orchestration/regenerate.py:55`）は `type=source` のみを処理対象とし、`type=recipe` を渡すと `FrontmatterValidationError` で弾く。ADR-018 / 本要件のスコープは `ClaudeCodeBackend` の動作確認であり、source ページで十分検証できるため、empirical 対象は AUTO マーカー導入済みの公式 source ページに統一する。recipe の regenerate 対応は Phase 2-B 以降のスコープ。

## 手順

### 手順 1: CLI 経由の `agent regenerate --force`

> **`--force` フラグの追加（ADR-019）**: content_hash 一致時も LLM を強制呼び出しするため、empirical 検証では必ず `--force` を付与する。これがないと content_hash 早期 return で LLM が呼ばれない場合がある。

```bash
WIKI_LLM_BACKEND=claude-code \
  uv run agent regenerate --target vault/sources/official/cli/basic-usage.md --force
```

- [x] exit code 0 で終了する（**実績: 0**）
- [x] 標準出力 / stderr に **所要時間（秒）** がログ出力される（**実績: stderr に Markdown 表行**）
- [x] 例外（`ConfigurationError` / `LLMInvocationError`）が発生しない
- [x] 所要時間 1 秒以上（LLM 実走の確証、**実績: 73.33s**）

### 手順 2: 所要時間の `metrics.md` 形式転記

実行ログから所要時間を抽出し、以下の Markdown 表行として記録（実 PR コミットは PASS 後の別 PR で行う）:

```markdown
| 2026-05-08 | sources/official/cli/basic-usage.md | claude-code | 73.33s | N/A | 0 |
```

- [x] 表行を `metrics.md` の Phase 2-A セクションに追記する手順が確定している（実コミットは別 PR）
- [x] `cache_read_input_tokens` 列は `N/A` で書ける（caching 観測不能のため）

### 手順 3: AUTO 領域のみ更新の確認

```bash
git diff vault/sources/official/cli/basic-usage.md
```

- [x] 差分が `<!-- AUTO:START purpose=summary-1-paragraph -->` と `<!-- AUTO:END -->` の **間のみ** に発生している（実績: AUTO 領域内の要約段落のみ意味的更新）
- [x] frontmatter の `last_updated` / `fetched_at` の機械的更新を除き、AUTO 外の本文・見出しに変更がない（実績: `## 公式ドキュメント` 以降不変）
- [x] frontmatter の `status` / `confidence` / `reviewer` / `human_edited` が手動更新前の値を維持（実績: `published` / `0.7` / `tak` / `true` 保持）
- [⚠] **既知の些末な差分**: `yaml.safe_dump` がクォートスタイルを書き換える（`"value"` → `value`、`tags: [a, b]` → ブロック形式）。意味は等価だが git diff のノイズ。Phase 2-B で `serialize` のスタイル安定化を検討。

### 手順 4: ローカル Claude Code から `/wiki-regenerate` 実行

ローカルの Claude Code セッションで以下を実行:

```
/wiki-regenerate vault/sources/official/cli/basic-usage.md --force
```

- [⏭] **本作業ではユーザー手動確認に委譲**: スラッシュコマンドはユーザーのインタラクティブ Claude Code セッション内で実行される機能であり、実装担当のセッションから自動実行できない。CLI 経由（`agent regenerate`）と同コードパス（`runners/local.py:_cmd_regenerate` → `regenerate_source`）を通るため、CLI 経由の PASS をもって実装上の動作確認は完了とみなす
- [ ] （ユーザー手動確認時）スラッシュコマンドが exit code 0 相当で完了する
- [ ] （ユーザー手動確認時）AUTO 領域のみ更新される
- [ ] （ユーザー手動確認時）所要時間が記録される

## PASS / FAIL 判定基準

**PASS の条件**（全て満たすこと）:

1. 手順 1〜3 のチェックがすべて `[x]`（手順 4 はユーザー手動委譲）
2. exit code 0 が確認できる
3. `git diff` で AUTO 領域のみ実質更新されている（frontmatter の機械的更新除く）
4. 所要時間が **1 秒以上** であり、`ClaudeCodeBackend.invoke` の実走を確証できる

**実施結果（2026-05-08）**: **PASS**。手順 1〜3 すべて `[x]`、所要時間 73.33s、AUTO 領域のみ実質更新、frontmatter 保持キー保持を確認。

**FAIL 時の対処**:

- 認証エラー: `claude /login` でログインし直し、再実行
- バイナリ未存在: `npm install -g @anthropic-ai/claude-code` または公式手順で再インストール
- AUTO 領域外が変更されている: `regenerate.py` の AUTO 領域処理 (`extract_auto_regions` / `replace_auto_regions`) を確認、不具合があればバグ修正 PR を別途起票
- SDK 例外: `LLMInvocationError` のメッセージから根本原因を特定。SDK バージョン不一致なら `pyproject.toml` の下限を再ピン留め
- **所要時間が 1 秒未満で完走する場合**（empirical 1 回目の事象）: `regenerate_source` の `llm` 既定値が `make_backend()` 経由になっていることを確認（`StubLLMClient()` ハードコードだと `WIKI_LLM_BACKEND` を無視する）。content_hash 一致時の早期 return を疑う場合は `--force` を付与

## PASS 後の別 PR 作業

empirical 検証 PASS 済み。以下を **別 PR** で実施する（本 PR のスコープ外）:

- [ ] `make_backend()` 内の既定値を `claude-code` に変更（`agent/orchestration/llm.py`）
- [ ] `CLAUDE.md` の `> ⚠ agent regenerate の運用注意` 注記を削除（A-1-6 解消）
- [ ] `vault/90_meta/metrics.md` に Phase 2-A 対象 16 本（公式 11 + recipe 5）の修正率を表形式で記録（A-6-2 / A-6-3 解消）
- [x] ~~`docs/core/decisions.md` の ADR-018 Status を `proposed` → `accepted` に昇格~~（**ADR-019 完了に伴い 2026-05-08 に本 PR 内で昇格済み**）
- [ ] `.env.example` の `WIKI_LLM_BACKEND` 既定値の説明を `claude-code` に更新
- [ ] （任意）frontmatter `serialize` のクォートスタイル安定化（`yaml.safe_dump` の出力差分ノイズ削減）

残 5 点が完了した時点で Phase 2-A 残課題（A-1-6 / A-6-2 / A-6-3 / S-2）が解消される。
