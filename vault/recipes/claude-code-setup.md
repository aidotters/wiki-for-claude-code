---
title: "Claude Code セットアップ（新規プロジェクト導入）"
type: recipe
use_case: "新規プロジェクトに Claude Code を導入し、初回対話とパーミッション設定まで完了させる"
confidence: 0.7
sources:
  - "[[sources/official/cli/installation]]"
  - "[[sources/official/cli/configuration]]"
  - "[[sources/official/cli/permissions]]"
last_updated: 2026-05-06
stale: false
tags: [recipe, setup, cli, onboarding]
reviewer: "tak"
human_edited: true
status: published
auto_section_managed: true
---

## TL;DR
<!-- AUTO:START purpose=recipe-tldr -->
Claude Code を新しいプロジェクトに導入する最短経路は「インストール → `claude` 起動 → `/init` で `CLAUDE.md` 生成 → `.claude/settings.json` で permissions を最低限定義」の 4 ステップ。チームで共有する場合は `.claude/settings.json` を Git 管理し、機微情報は `.local.json` に分離する。
<!-- AUTO:END -->

## 手順
<!-- AUTO:START purpose=recipe-steps -->
1. **インストール**: ネイティブインストーラ（`curl install.sh`）または npm（`npm install -g @anthropic-ai/claude-code`、Node.js 18+ が必要）を選ぶ。詳細経路は [[sources/official/cli/installation]] を参照
2. **認証**: 初回 `claude` 起動で Anthropic アカウントの OAuth または API キー設定を行う（組織テナントの場合は SSO）
3. **プロジェクトルートで起動**: 対象リポジトリで `claude` を実行。初回は探索に少し時間がかかる
4. **`/init` で CLAUDE.md 生成**: プロジェクト概要・ディレクトリ構造・主要コマンドを記載した `CLAUDE.md` を作成すると、以降のセッションが大幅に効率化される
5. **`.claude/settings.json` で permissions 定義**: チーム共有用の許可・禁止コマンドを宣言（例: `Bash(git status)` を allow、`Bash(rm -rf:*)` を deny）。詳細は [[sources/official/cli/permissions]]
6. **`.claude/settings.local.json` に個別環境設定**: API キーや個人エイリアスは `.gitignore` 対象のローカル設定に置く
<!-- AUTO:END -->

## 引用元の補足
公式ドキュメントは「インストール」「設定」「permissions」がそれぞれ別ページに分散しているが、新規導入時は順番に踏むのが定石。本レシピは 3 つの一次資料を時系列で再構成し、`/init` の活用ポイントと `.local.json` の分離パターンを補足した。
