---
title: "Claude Code のインストール"
type: source
confidence: 0.5
sources: []
last_updated: 2026-05-06
stale: true
tags: [cli, installation, setup]
source_url: "https://code.claude.com/docs/ja/setup"
fetched_at: "2026-05-06T01:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: true
status: draft
auto_section_managed: false
---

<!--
Content drift detected vs. code.claude.com/docs/ja/setup on 2026-05-06: 公式は curl install.sh による
ネイティブインストールを推奨に変更、Homebrew/WinGet/apt/dnf/apk/npm の複数経路に拡大、
Node.js 要件は 18 以上（npm 経路のみ）。本記事の主軸である「npm install -g 推奨」は古い。
Phase 2 で内容を最新ドキュメントに対して全面書き直し予定。それまで status は draft 維持。
-->

## 概要 (要約)
Claude Code は npm パッケージ `@anthropic-ai/claude-code` として配布される CLI ツールで、`npm install -g` でグローバルインストールできます。Node.js 20 LTS 以上が必要で、初回起動時に Anthropic アカウントでの認証フローが走ります。サブスクリプションプランまたは API キーによる利用が可能で、macOS / Linux / Windows（WSL）に対応します。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/setup
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### 主要な手順（概略）

1. Node.js 20 LTS 以上を導入
2. `npm install -g @anthropic-ai/claude-code` でインストール
3. ターミナルで `claude` を起動
4. 初回認証（Anthropic アカウントでログイン or API キー設定）

### バージョン確認とアップデート

- バージョン確認: `claude --version`
- 最新化: `npm update -g @anthropic-ai/claude-code`

### ハマりどころ

- パスが通らない場合、`npm config get prefix` で確認し、`bin` ディレクトリを `$PATH` に追加
- 企業 Proxy 環境では `npm config set proxy <url>` が必要なことがある
- WSL 上で動かす場合、Windows 側のクリップボード連携や git 認証は別途設定が必要

### 関連ページ

- 起動後の使い方: [[basic-usage]]
- 設定: [[configuration]]
- ショートカット: [[keybindings]]
