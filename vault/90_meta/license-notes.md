# 著作権・利用規約 (license-notes)

> 取込み元の著作権・利用規約に関する整理。`vault/90_meta/sources.md` の各ソースから参照される。

## 大原則

1. **全文転載禁止**: 取込み元の文章を連続100文字以上そのまま転載しない（`transclusion_validator` で機械検出）
2. **縮退仕様で許可**: `type: source` ページは「## 概要 (要約)」（AUTO 領域）+「## 公式ドキュメント」の 2 セクション構造（ADR-017 / 旧 ADR-003 を superseded）
3. **ホワイトリスト外の取込み禁止**: `vault/90_meta/sources.md` に登録されていないソースは取込み拒否
4. **robots.txt 遵守**: 取込み元の robots.txt で disallow されているパスは取込まない
5. **レート制限遵守**: 各ソースの `rate_limit` フィールドに従い、`agent/fetchers` が sleep を挿入する

## ソース別の整理

### anthropic-claude-code-docs-ja / anthropic-claude-code-docs-en（https://code.claude.com/docs/）

#### 関連規約
- **Anthropic Usage Policy**: https://www.anthropic.com/legal/aup
- **Commercial Terms of Service**: https://www.anthropic.com/legal/commercial-terms
- **Privacy Policy**: https://www.anthropic.com/legal/privacy

#### 整理ポイント

- 公式ドキュメントの全文翻訳は商用利用とみなされ得るため、**禁止**とする
- 公式日本語版（`/docs/ja/*`）が存在する場合は `source_url` の原典をそちらに向け、本プロジェクトでは「要約 + 公式日本語版へのリンク + 日本語補足」の3部構成で扱う
- 要約 + 公式リンク + 日本語補足は「個別の表現」を含む二次創作として許容範囲とする方針（最終的な判断は法務確認の上）
- 公式日本語版の文章をそのまま要約セクションに転載することも全文転載禁止の対象（連続100文字一致を `transclusion_validator` で検出）
- 図表・コードサンプルの引用は「最小限・出典明記」の原則で限定的に許可
- LLM による生成過程で raw コンテンツを学習データとして再配布しない（プロンプトの一時利用のみ）

#### エージェント実装が遵守すべきルール

- 取込み時のプロンプトに「全文転載禁止」「日本語要約のみ」を明記する（`agent/prompts/source-ingest.md`）
- `transclusion_validator` で連続100文字一致を CI で必須チェック
- `User-Agent` を識別可能な値（例: `llm-wiki-for-claude-code/0.1 (https://github.com/...)`）に設定
- リクエスト間に最低 100ms（rate_limit に応じて延長）の sleep を入れる

### awesome-claude-code（https://github.com/hesreallyhim/awesome-claude-code）

#### ライセンス検証結果（2026-05-06、Phase 2-A）

> **A-7 中止条件発動**: ライセンスが **CC BY-NC-ND 4.0**（NonCommercial-NoDerivatives）と判明。A-3 タスクは停止し、`vault/sources/community/awesome-claude-code/` への記事生成は **実施しない**。`vault/90_meta/sources.md` の該当エントリは `enabled: false` に設定（コード資産は残すが ingest は禁止）。

検出詳細:

- **取得元**: `https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/2d32d46e5e946799bff436210d641eca1153ff63/LICENSE`
- **ライセンス**: `Awesome Claude Code © 2025 by hesreallyhim is licensed under Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International`
- **発見日**: 2026-05-06（Phase 2-A の A-3 着手時点）

#### 不適合の根拠

- **ND (NoDerivatives)**: リスト本体の構造化情報を再構成して要約記事を作る行為は、たとえ翻訳・原文書換でも derivative と見なされうる
- **NC (NonCommercial)**: 本プロジェクトは公開 Wiki を志向しており、将来的に広告・有料機能・組織用途に展開する可能性を排除しない（NC はそれを禁ずる）
- **ADR-016 の中止条件**: 「ライセンスが商用利用不可（NC 系）と判明した場合、A-3 を停止し別系統に切替」に直接該当

#### 残存する技術資産

- `agent/fetchers/awesome_claude_code.py`: 実装済み + ユニットテスト 11 件 PASS。Phase 2-B / B-3 で別系統（permissive license のリスト）の取込みに流用可能
- `agent/orchestration/ingest.py` の `awesome-claude-code` カテゴリパス: 残存。再有効化時はホワイトリストの `enabled` を `true` に戻すのみで動作する想定
- 本プロジェクトのフロー検証としては fetcher / ホワイトリスト / カテゴリ分岐の各レイヤーが動作することを ユニットテストで担保した

#### Phase 2-B での再計画方針

- 別系統候補（B-3 で検討）:
  - `github.com/anthropics/anthropic-cookbook`（MIT）
  - Anthropic 公式エンジニアリング blog（既存ホワイトリスト `anthropic-claude-code-docs-*` の延長）
  - Karpathy / Rezvani 個人発信（個別ライセンス確認の上）
- 別系統採用時は本ファイルに新セクションを起こし、ライセンス整理を経てからホワイトリスト追加を行う

### 将来追加候補ソース（旧位置）

### 将来追加候補ソース

#### Anthropic ブログ（Phase 2 候補）
- 公式ブログの著作権は同社に帰属。同様の3部構成適用を予定。

#### GitHub Releases（Phase 3 候補）
- `anthropics/claude-code` の Release Notes は公開情報だが、引用は最小限とし、要約 + リンク + 補足の3部構成を適用。

#### awesome-claude-code 系（Phase 3 候補）
- 各リスト項目の「ソース」自体は二次情報のため、原典への辿り着きを保証する Wikilinks 構造を採用。

## レート制限・robots.txt 遵守原則

- 各リクエスト前に該当ホスト直下の `robots.txt` を取得・キャッシュし、対象パスが disallow されていないか検証する
- 連続失敗時は exponential backoff（最大リトライ3回、間隔 1秒 → 2秒 → 4秒）
- 4xx 応答時はリトライしない（即時 `FetchFailedError`）
- 5xx 応答時は1度のみリトライ

## 全文転載検出の実装方針（Phase 1）

- `transclusion_validator` が公式ページとの連続100文字一致を検出
- 文字列スライディングウィンドウ（100文字幅、1文字ずつスライド）で実装
- 改行・空白の正規化のみ実施（句読点・全角半角は正規化しない）
- false positive を許容する設計（人間レビューで最終判断）
