# 情報源ホワイトリスト (sources)

> 取込み可能な情報源を機械可読形式で管理する。`agent/fetchers` および `agent/orchestration/ingest` が本ファイルを参照してホワイトリスト検証を行う。

## ホワイトリスト本体（YAML）

```yaml
sources:
  - id: anthropic-claude-code-docs-ja
    name: "Anthropic Claude Code 公式ドキュメント (日本語版)"
    base_url: "https://code.claude.com/docs/ja/"
    fetch_method: http
    rate_limit: "1 req/sec"
    license_notes: "Anthropic Usage Policy 準拠。全文転載禁止。要約 + リンク + 補足の3部構成のみ許可（ADR-003）。読者が日本人想定のため日本語版を原典として採用"
    enabled: true
  - id: anthropic-claude-code-docs-en
    name: "Anthropic Claude Code 公式ドキュメント (英語版、補完用)"
    base_url: "https://code.claude.com/docs/en/"
    fetch_method: http
    rate_limit: "1 req/sec"
    license_notes: "日本語版に未翻訳箇所がある場合の補完参照のみ許可。新規記事の `source_url` は `-ja` を優先する"
    enabled: true
  - id: anthropic-claude-docs-legacy
    name: "Anthropic Claude Code 公式ドキュメント (旧ドメイン、リダイレクト追跡用)"
    base_url: "https://docs.claude.com/"
    fetch_method: http
    rate_limit: "1 req/sec"
    license_notes: "2026-05 時点で 301 redirect → code.claude.com/docs/。互換のため維持（ADR 別途）"
    enabled: true
  - id: awesome-claude-code
    name: "awesome-claude-code (GitHub コミュニティリスト)"
    base_url: "https://github.com/hesreallyhim/awesome-claude-code"
    raw_base_url: "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/"
    fetch_method: http
    rate_limit: "1 req/sec (GitHub unauth: 60 req/h)"
    license_notes: "CC BY-NC-ND 4.0 と判明（2026-05-06）。NC-ND のため A-7 中止条件発動、Phase 2-A の A-3 を停止。詳細は [[license-notes]]。Phase 2-B B-3 で別系統に切替予定"
    enabled: false
```

> 2026-05-06 更新: 公式ドキュメントの正式 URL が `https://docs.claude.com/claude-code/*` から
> `https://code.claude.com/docs/{en,ja}/*` に移行（旧 URL は 301 リダイレクト）。
> 同時に公式日本語版（`/docs/ja/*`）の存在を確認したため、本プロジェクトの読者は日本人想定であることから
> 日本語版を `source_url` の原典として採用する方針に切替。英語版は日本語版に未翻訳箇所がある場合の
> 補完参照に位置付ける。

## フィールド仕様

| フィールド | 型 | 必須 | 説明 |
|-----------|----|------|------|
| `id` | string | ✓ | ソース識別子（小文字・ハイフン、`anthropic-claude-docs` 等） |
| `name` | string | ✓ | 人間可読の名称 |
| `base_url` | string (URL) | ✓ | 取得対象ベース URL。`source_url` がこの prefix で始まる場合のみ取込み許可 |
| `fetch_method` | enum | ✓ | `http` / `rss` / `github_api`（Phase 1 では `http` のみ） |
| `rate_limit` | string | ✓ | レート制限の表現。`agent/fetchers` が sleep 計算に使用（Phase 1 は1秒固定で可） |
| `license_notes` | string | ✓ | 取込み時に従う著作権・規約上の制約 |
| `enabled` | bool | ✓ | `false` にすると取込み対象外 |

## ホワイトリスト追加プロセス

1. 取込み候補のソースの利用規約・robots.txt を確認
2. `vault/90_meta/license-notes.md` に該当ソースの整理を追記
3. 本ファイルの `sources:` 配下に YAML エントリを追加
4. PR を立て、人間レビューを経てマージ

## Phase 別のソース展開

- **Phase 1**: `anthropic-claude-code-docs-ja`（主）+ `anthropic-claude-code-docs-en`（補完）+ `anthropic-claude-docs-legacy`（リダイレクト追跡）
- **Phase 2-A**: 上記 + `awesome-claude-code`（コミュニティリスト 1 系統先行、ADR-016 pivot）
- **Phase 2-B**: 公式 Anthropic ブログ、Anthropic Releases（必要に応じて）
- **Phase 3**: GitHub Releases（`anthropics/claude-code`）、Karpathy/Rezvani 等の個人発信、X/Reddit（要規約再検討）

## ホワイトリスト外の取込み禁止

- `source_url` が任意のソースの `base_url` で始まらない場合、`agent/orchestration/ingest` は `SourceNotWhitelistedError` を送出（終了コード `2`）
- `enabled: false` のソースも同様に拒否

## 関連ドキュメント

- [[license-notes]] — 各ソースの著作権・利用規約整理
- [[frontmatter-spec]] — 取込みページの frontmatter 規約
