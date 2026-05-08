# AUTO セクションマーカー仕様 (auto-marker-spec)

> Wiki ページ内の自動生成領域と人手編集領域を分離するための AUTO マーカー構文と境界制御規約。
> 設計判断の経緯は [ADR-015](../../docs/core/decisions.md#adr-015) を参照。

## 構文

AUTO 領域は **HTML コメント** で行頭に置く:

```markdown
<!-- AUTO:START purpose=summary-1-paragraph -->
（自動生成領域。エージェントが書き換える）
<!-- AUTO:END -->
```

`purpose` 属性は省略可能（後方互換、ADR-019 以前の記法）。省略時は orchestrator 側で「種別 × 配置順」から既定値を推論する（[既定値推論ルール](#purpose-既定値推論ルール) 参照）。

### 構文ルール

- `<!-- AUTO:START -->` と `<!-- AUTO:END -->` は **行頭** から始まること（前にスペース・タブ等を置かない）
- マーカー行はそれ単体で 1 行を占めること（同行に他のテキストや Markdown を混在させない）
- マーカー間の空行は許容（生成された本文の冒頭・末尾に空行が含まれてよい）
- 1 ファイル内に **複数領域許容**（順序付きで管理）
- **ネスト禁止**（`START` 後に `END` より先に新たな `START` が出現した場合エラー）
- **`purpose` 属性**（任意）: `<!-- AUTO:START purpose=<value> -->` の形式で 1 つだけ指定可能。値は `[a-z0-9-]+` の正規表現に一致すること（小文字英数 + ハイフンのみ）。属性無しは後方互換で許容
- `<!-- AUTO:END -->` には属性を付けない（START 側のみが領域メタを保持）

### 構文不正の扱い

以下のいずれかを Writer が検出した場合、`MalformedAutoMarkerError` を送出して書き込みを中止する:

| 違反 | 例 |
|------|----|
| `START` のみで対応する `END` がない | `<!-- AUTO:START -->` で終わるファイル |
| `END` のみで対応する `START` がない | `<!-- AUTO:END -->` が先に出現 |
| ネスト | `<!-- AUTO:START -->` の後に `END` より先に再び `<!-- AUTO:START -->` |
| 行頭以外への配置 | 行内 inline、リスト項目内、引用ブロック内 |
| `purpose` 属性の値が不正 | `<!-- AUTO:START purpose=Foo_Bar -->`（大文字・アンダースコア不許可）、`<!-- AUTO:START purpose= -->`（空値）、`<!-- AUTO:START purpose=a purpose=b -->`（重複指定） |
| `END` 側に属性を付与 | `<!-- AUTO:END purpose=foo -->` |

## 境界制御と領域外バイト一致保持

### Writer の責務

`agent/writers/markdown_writer.py` の `replace_auto_regions(path, new_contents)` は以下を厳守する:

1. **領域抽出**: 既存ファイルから AUTO 領域の `(start_line, end_line)` リストを順序付きで取得
2. **領域数一致**: `new_contents` の長さと領域数が一致しない場合 `MalformedAutoMarkerError`
3. **領域内置換**: 領域 i の内容を `new_contents[i]` で置換（マーカー行 `<!-- AUTO:START/END -->` 自体は保持）
4. **領域外バイト一致 assert**: 書き換え前後で AUTO 領域外行のバイト列が完全一致することを Writer 内部で assert（不一致は実装バグとして即座に例外送出）

### 領域外バイト一致の意味

「領域外バイト一致」とは、AUTO 領域外（マーカー行を含む）の **バイト列レベルでの完全一致** を指す:

- 改行コード（LF / CRLF）、末尾空白、空行の数、すべて完全一致
- frontmatter ブロック（`---` で囲まれた YAML 部分）も領域外として保持
- 人手編集の見出し・リスト・コードブロックは Writer が一切触らない

これにより ADR-006（自動 / 人手領域分離）の主張を **構造的に保証** する。

## `purpose` 属性

`purpose` は AUTO 領域に「何を生成する場所か」を宣言するメタデータで、`agent regenerate` の per-region プロンプトディスパッチに使われる（ADR-019）。

### purpose 一覧

| purpose | 用途 | 想定種別 | 出力形式 | プロンプトテンプレ |
|---------|------|----------|----------|--------------------|
| `summary-1-paragraph` | 取込み元の 1 段落要約 | source | 3-5 文の段落（日本語） | `agent/prompts/auto-region/summary-1-paragraph.md` |
| `recipe-tldr` | レシピの結論 | recipe | 1-3 文（日本語） | `agent/prompts/auto-region/recipe-tldr.md` |
| `recipe-steps` | レシピの手順 | recipe | 番号付きリスト（日本語） | `agent/prompts/auto-region/recipe-steps.md` |

Phase 2-B で派生種別（concept / entity / synthesis）の追加に伴い purpose も拡張予定。

### purpose 既定値推論ルール

`purpose` 省略時、orchestrator は次のルールで既定値を解決する:

| ページ種別 | 配置順（0-origin） | 既定 purpose |
|-----------|-----------------|--------------|
| `source` | 任意 | `summary-1-paragraph` |
| `recipe` | 0 | `recipe-tldr` |
| `recipe` | 1 | `recipe-steps` |
| `recipe` | 2 以降 | エラー（明示的に `purpose` を指定すること） |
| その他種別 | 任意 | エラー（明示的に `purpose` を指定すること） |

新規ページ作成時は **purpose を明示する** ことを推奨。既定値推論はマイグレーション時の後方互換のための仕組み。

## frontmatter キーとの連携

| キー | 値 | 意味 |
|------|----|------|
| `auto_section_managed` | `true` | このファイルに AUTO マーカーが導入済み。Writer は AUTO 領域のみ書き換え可 |
| `auto_section_managed` | `false` | AUTO マーカー未導入。Writer は従来どおりフルファイル書き換え |

Phase 2-A 時点では対象 15 本（公式 source 10 + recipe 5）のみ `auto_section_managed: true`。
Phase 2-B で残り全 source / 派生種別へ展開する予定。

## 配置パターン例

### `source` 種別（縮退仕様、ADR-017）

```markdown
## 概要 (要約)
<!-- AUTO:START purpose=summary-1-paragraph -->
（1 段落要約。3-5 文）
<!-- AUTO:END -->

## 公式ドキュメント
→ {URL}
（最終確認: YYYY-MM-DD / 対象バージョン: X.Y.Z）
```

`## 概要 (要約)` 配下のみ AUTO 領域化。`## 公式ドキュメント` は人手で更新（URL / 最終確認日 / 対象バージョン）。

### `recipe` 種別

```markdown
## TL;DR
<!-- AUTO:START purpose=recipe-tldr -->
（ユースケースの結論を 1-3 文で）
<!-- AUTO:END -->

## 手順
<!-- AUTO:START purpose=recipe-steps -->
1. ...
2. ...
<!-- AUTO:END -->

## 引用元の補足
（人手記述。引用元のどの部分を再構成したか / 派生した独自視点）
```

複数 AUTO 領域を順序付きで配置。`## 引用元の補足` は人手領域。

## 検証

`agent/validators/markdown_rules_validator.py` で構文の検出・検証を行う:

- 構文不正（START/END 不対応・ネスト・行頭以外配置）→ `MarkdownRuleViolationError`
- `auto_section_managed: true` なのに AUTO マーカー 0 件 → 警告（lint 違反、エラーではない）

## 関連 ADR

- [ADR-006](../../docs/core/decisions.md#adr-006): AUTO セクションマーカー導入方針（2026-05-05、Phase 2 で実装）
- [ADR-015](../../docs/core/decisions.md#adr-015): AUTO 構文確定（2026-05-06）
- [ADR-017](../../docs/core/decisions.md#adr-017): 公式 source 縮退仕様（2026-05-06、AUTO 領域を活用）
- [ADR-019](../../docs/core/decisions.md#adr-019): AUTO 領域経路で LLM を実呼び出し / `purpose` 属性導入（2026-05-08）

## 関連実装

- `agent/writers/markdown_writer.py`: `extract_auto_regions` / `replace_auto_regions`
- `tests/unit/test_auto_markers.py`: 構文検証 + バイト一致保持
