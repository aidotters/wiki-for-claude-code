---
title: "Claude Code キーバインド"
type: source
confidence: 0.6
sources: []
last_updated: 2026-05-06
stale: false
tags: [cli, keybindings, ux]
source_url: "https://code.claude.com/docs/ja/interactive-mode#keyboard-shortcuts"
fetched_at: "2026-05-06T01:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: true
status: reviewed
auto_section_managed: false
---

<!--
Last verified: 2026-05-06 against code.claude.com/docs/ja/interactive-mode.
高レベルのキー操作（Esc / Ctrl+C / 矢印キー / Tab / Shift+Enter 等）は現行ドキュメントと整合。
キーボードショートカット情報は cli-reference から interactive-mode ページへ移動済み（公式構成変更）。
~/.claude/keybindings.json のフォーマットや差分適用挙動は Phase 2 で再確認後に published 化する。
日本語版見出しが「## キーボードショートカット」のためアンカー `#keyboard-shortcuts` の解決可否は
`agent verify-links` で確認すること。
-->

## 概要 (要約)
Claude Code はターミナル UI を持ち、キーバインドで効率的に対話できます。Esc で実行中アクションの中断、Ctrl+C で強制終了、上下キーで履歴遷移、Tab で候補補完が基本です。`~/.claude/keybindings.json` で一部のショートカットをカスタマイズ可能で、コードブロック貼り付け時の改行扱いなど環境依存の挙動も調整できます。複数行入力は Shift+Enter または `\` で行を継続します。

## 公式ドキュメント
→ https://code.claude.com/docs/ja/interactive-mode#keyboard-shortcuts
（最終確認: 2026-05-06 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)

### よく使うキー

| キー | 動作 |
|------|------|
| `Esc` | 実行中の中断 |
| `Ctrl+C` | 入力クリア / 強制終了 |
| `↑` / `↓` | 入力履歴 |
| `Tab` | 補完 |
| `Shift+Enter` | 複数行入力（改行） |
| `Ctrl+L` | 画面クリア（一部端末） |

### カスタマイズ

`~/.claude/keybindings.json` に変更したいバインドを記述。デフォルトを完全置換ではなく差分適用するため、書きすぎに注意。

### ハマりどころ

- macOS の Option + キーは端末アプリの設定次第で送出キーコードが異なる
- WSL では Windows ターミナル側のキーバインドと衝突しがち
- IME 入力中の Esc は IME 解除に消費されることがある

### 関連ページ

- インストール: [[installation]]
- 起動: [[basic-usage]]
- 設定: [[configuration]]
