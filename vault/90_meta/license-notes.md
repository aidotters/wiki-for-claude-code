# 著作権・利用規約 (license-notes)

> 取込み元の著作権・利用規約に関する整理。`vault/90_meta/sources.md` の各ソースから参照される。

## 大原則

1. **全文転載禁止**: 取込み元の文章を連続100文字以上そのまま転載しない（`transclusion_validator` で機械検出）
2. **要約 + リンク + 補足の3部構成のみ許可**: `type: source` ページは「## 概要 (要約)」「## 公式ドキュメント」「## 補足解説 (日本語)」の3セクション必須（ADR-003）
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
