---
title: "キーバインドのカスタマイズ（生産性チューニング）"
type: recipe
use_case: "Claude Code のキーバインドを `~/.claude/keybindings.json` でカスタマイズし、自分の操作習慣に合わせる"
confidence: 0.7
sources:
  - "[[sources/official/cli/keybindings]]"
  - "[[sources/official/cli/basic-usage]]"
last_updated: 2026-05-06
stale: false
tags: [recipe, keybindings, productivity, ux]
reviewer: "tak"
human_edited: true
status: published
auto_section_managed: true
---

## TL;DR
<!-- AUTO:START purpose=recipe-tldr -->
`~/.claude/keybindings.json` に変更したいバインドだけを書き、デフォルトに対する差分上書きで運用するのが基本。複数行入力は `Shift+Enter` または末尾の `\` を覚えると入力体験が安定する。OS / 端末アプリで衝突しがちなショートカット（macOS の Option キー、WSL の `Ctrl+L`）は事前に切り分けて検証する。
<!-- AUTO:END -->

## 手順
<!-- AUTO:START purpose=recipe-steps -->
1. **デフォルトを覚える**: `Esc`（中断）、`Ctrl+C`（クリア / 強制終了）、`↑↓`（履歴）、`Tab`（補完）、`Shift+Enter`（改行）を体に染み込ませる
2. **不満点を洗い出す**: 「履歴遷移が `Ctrl+P` の方が好み」「画面クリアを `Cmd+K` に当てたい」など、自分の他ツールとの一貫性で違和感がある場所を列挙
3. **`~/.claude/keybindings.json` を作成**: 既存ファイルがなければ新規作成。差分形式なので、変えたいバインドだけ列挙すれば良い
4. **OS / 端末側の衝突を確認**: macOS Terminal / iTerm2 / WezTerm 等で同キーが既にバインドされていないか調査。WSL は Windows ターミナル側のキーバインドも考慮
5. **IME との相互作用**: 日本語 IME 入力中の `Esc` は IME 解除に消費されるため、Claude へのキャンセル送出には別キー（`Ctrl+C`）を意識する
6. **段階導入**: いきなり全部変えず、1〜2 個の変更で 1 週間運用し、慣れたら追加。ロールバックは `keybindings.json` の該当行を削除するだけで戻せる
<!-- AUTO:END -->

## 引用元の補足
公式 keybindings ページは記法と既定キー一覧の提供にとどまるが、「他ツールとの一貫性」「OS / 端末との衝突回避」「IME との相互作用」といった実利用観点の知見は人手でしかまとめられない領域。本レシピは basic-usage の対話セッション操作と組み合わせ、生産性チューニングの段階導入手順として再構成した。
