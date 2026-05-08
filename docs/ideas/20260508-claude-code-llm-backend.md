# Claude Code バックエンド化（`ClaudeCodeBackend` 追加）

> 作成日: 2026-05-08
> ステータス: draft
> 優先度: P1
> 起点: `.steering/20260506-llm-wiki-for-claude-code-phase-2a/acceptance-test-report.md` §6（2026-05-07 追記）
> 関連 ADR: ADR-018（Proposed、本アイデア確定後に起票）

## 概要

`agent/orchestration/llm.py` の `LLMBackend` Protocol に **3 つ目の実装** として `ClaudeCodeBackend` を追加し、Anthropic API 直接呼び出しの代わりに **Claude Code (Max プラン) 経由** で LLM を呼び出せるようにする。Max プランの定額枠を活用した日次自動化（ローカル cron / launchd）が主たるユースケース。

## 背景

### 現状の課題

- Phase 2-A で実装した `AnthropicBackend` は `ANTHROPIC_API_KEY` 必須・従量課金前提。**ユーザーは Max プランを契約しており、定額枠を活用したい**
- 想定運用は「日々新しい話題が出てくる Claude Code 関連情報を **ローカル cron / launchd** で定期取り込み → Obsidian で閲覧 → 将来は Web 公開へ同期」というローカル運用主軸
- 従量課金の `AnthropicBackend` を主経路にすると、記事数増加に伴い運用コストが線形に増加する。Max プランがある以上、副次経路として残すのが妥当
- `acceptance-test-report.md §6.1` で方針転換が起票済み、検討事項 5 点（§6.2）が別セッション課題として残っている

### 解決したいこと

- **Max プラン定額枠** を主たる LLM 呼び出し経路として活用する
- `AnthropicBackend` は **CI / API 利用者向けの選択肢** として残置し、`WIKI_LLM_BACKEND` で切替可能にする
- Phase 2-A の規約・実装・テスト 159 件 PASS は **影響を受けない**（既存 Protocol 拡張のみ）
- empirical 検証経路を再設計し、Phase 2-A クローズ判定を `ClaudeCodeBackend` 側で通せるようにする（acceptance-test-report.md §6.1 案 Y 採用）

## 解決策

### アプローチ

`claude-agent-sdk`（Anthropic 公式 Python パッケージ、内部で `claude` CLI を subprocess 起動）を採用し、`LLMBackend` Protocol の 3 つ目の実装として `ClaudeCodeBackend` を追加する。既存の `StubBackend` / `AnthropicBackend` と並列構造を保ち、`WIKI_LLM_BACKEND=claude-code` で選択する。

```python
# agent/orchestration/llm.py（追加イメージ）
class ClaudeCodeBackend:
    """Claude Code (Max プラン) 経由で LLM を呼び出すバックエンド。

    認証情報は claude CLI が ~/.claude/ で管理するものを再利用。
    起動時に claude バイナリの存在のみ検証、認証エラーは API 呼び出し時に拾う。
    """
    model: str = DEFAULT_MODEL  # claude-sonnet-4-6

    def invoke(self, system: str, user: str) -> LLMResponse:
        # claude-agent-sdk 経由で呼び出し
        ...
```

### 設計方針

1. **既存 Protocol 拡張のみ**: `LLMBackend` Protocol（`agent/orchestration/llm.py:61-71`）のシグネチャは変更せず、3 つ目の実装を追加するだけ。`AnthropicBackend` / `StubBackend` には一切手を加えない
2. **認証は claude CLI に委譲**: `~/.claude/` の認証情報を `claude-agent-sdk` 経由で再利用。本プロジェクトでは追加 env var を導入しない
3. **起動時チェックは最小化**: `claude` バイナリが PATH に存在するかのみ確認。認証エラーは API 呼び出し時の例外で拾い、`LLMInvocationError` にラップ（既存階層に乗せる）
4. **caching 効果計測の主軸を切替**: Claude Code 経由では `cache_read_input_tokens` の取得可否が不確定。**主指標を「修正率（人手修正件数 / 全件数）」に降格**し、caching 効果検証は `AnthropicBackend` 側に残置
5. **既定切替は段階展開**: empirical 検証 PASS まで `WIKI_LLM_BACKEND` 既定は `stub` 維持。PASS 後 `claude-code` に昇格（β 案、ADR-018 で明文化）
6. **`StubBackend` は残置**: テスト DI / オフライン開発 / CI フォールバック用途のため、実装と env var 選択肢を維持

### 代替案と比較

#### 実装方式

| 案 | メリット | デメリット | 採否 |
|----|---------|-----------|------|
| **A. `claude-agent-sdk`（Python パッケージ）** | Python ネイティブで `LLMBackend` Protocol に素直にはまる、メッセージ構造が型付き、usage 情報にアクセス可能、エラー・リトライが SDK で抽象化 | 新規依存追加、SDK API 安定性が `anthropic` SDK ほど枯れていない | **採用** |
| B. `claude -p <prompt> --output-format=json` を subprocess で直接起動 | 依存追加なし、挙動が完全に把握可能 | プロンプト長・エスケープを自前実装、metrics 用 usage 情報が取れない可能性、CLI フラグ非互換変更を直接被る | 不採用 |
| C. MCP サーバ経由 | Claude Code 内文脈と統合しやすい | 過剰、本ユースケースに対し複雑度が高すぎる | 不採用 |

#### 既定値ポリシー

| 案 | 既定 | 採否 |
|---|------|------|
| α. `stub` 既定維持 | `stub` | 中間状態として維持 |
| **β. `claude-code` を既定に昇格** | `claude-code` | **empirical PASS 後に採用** |
| γ. 設定ファイル経由 | `.env` 任意 | 不採用（複雑度増） |

→ empirical 検証 PASS 前は α 維持、PASS 後 β に昇格する **段階展開** で確定。

## 実装する機能

### ロードマップ

| Phase | 機能 | 概要 |
|-------|------|------|
| 1 | `ClaudeCodeBackend` 実装 + env var 拡張 + 起動時バイナリチェック | 本アイデアの中核（今回スコープ） |
| 2 | empirical 検証（Phase 2-A 案 Y 経路） | Phase 2-A クローズ判定の最終条件 |
| 3 | 既定値を `claude-code` に昇格、`CLAUDE.md` ガード削除 | Phase 2-A クローズと同時 |
| 4 | metrics.md への修正率計測開始（A-6-2/A-6-3） | Phase 2-A 残課題の解消 |

### 機能1: `ClaudeCodeBackend` 実装

`agent/orchestration/llm.py` に `ClaudeCodeBackend` クラスを追加し、`LLMBackend` Protocol を実装する。

**インターフェース:**
- 既存 `LLMBackend.invoke(system, user) -> LLMResponse` をそのまま実装
- モデル既定 `claude-sonnet-4-6`、`WIKI_LLM_MODEL` で上書き可能
- レスポンス変換: `claude-agent-sdk` のメッセージ構造を `LLMResponse` データクラスに正規化
- `LLMUsage` フィールドのうち `cache_read_input_tokens` が取得できない場合は `None` を入れる

**バックエンド選択ロジック（既存）:**
- `WIKI_LLM_BACKEND` 環境変数で `stub|anthropic|claude-code` を選択
- 不明な値は `ConfigurationError`（exit code 3）

### 機能2: 環境変数拡張

| env var | 値 | 既定（empirical PASS 前 / 後） | 備考 |
|---------|-----|--------------------------------|------|
| `WIKI_LLM_BACKEND` | `stub` / `anthropic` / `claude-code` | `stub` / `claude-code` | 段階展開、ADR-018 に明記 |
| `WIKI_LLM_MODEL` | モデル ID | `claude-sonnet-4-6`（共通） | 既存維持、`claude-code` でも有効 |
| `ANTHROPIC_API_KEY` | API キー | 未設定可 | `anthropic` 選択時のみ必須、`claude-code` 選択時は **読まない** |

### 機能3: 起動時バイナリチェック

`claude-code` 選択時、`ClaudeCodeBackend` の初期化で以下を実施:

1. `claude` バイナリが PATH に存在するか（`shutil.which("claude")` 等）
2. 不在なら `ConfigurationError`（exit code 3）、メッセージで `claude /login` 等への誘導を含める
3. 認証エラーは API 呼び出し時の例外で拾い、`LLMInvocationError` にラップ（既存階層）

### 機能4: ADR-018 起票

`docs/core/decisions.md` に ADR-018 を追加。

**記録内容:**
- 決定事項: `claude-agent-sdk` 採用、`AnthropicBackend` / `StubBackend` 残置、env var 拡張、既定値段階展開
- 影響: Phase 2-A クローズ条件は変更しない（acceptance-test-report.md §6.3 と整合）
- 関連 ADR: ADR-015 / ADR-016 / ADR-017 を踏襲

## 受け入れ条件

### バックエンド実装

- [ ] `agent/orchestration/llm.py` に `ClaudeCodeBackend` が `LLMBackend` Protocol 実装として追加されている
- [ ] `WIKI_LLM_BACKEND=claude-code` で `ClaudeCodeBackend` が選択される
- [ ] `claude-agent-sdk` が `pyproject.toml` の依存に追加されている
- [ ] `AnthropicBackend` / `StubBackend` の既存実装に変更がない（diff で確認可能）

### 環境変数・設定

- [ ] `WIKI_LLM_MODEL` の値が `claude-code` バックエンドでも反映される
- [ ] `claude-code` 選択時に `ANTHROPIC_API_KEY` が読まれない
- [ ] `.env.example` に `WIKI_LLM_BACKEND=claude-code` の例が追記されている

### 起動時チェック

- [ ] `claude` バイナリが PATH に存在しない環境で `WIKI_LLM_BACKEND=claude-code` 指定時、`ConfigurationError`（exit code 3）で停止する
- [ ] エラーメッセージに `claude /login` 等の誘導が含まれている

### empirical 検証（Phase 2-A 案 Y 経路）

- [ ] `WIKI_LLM_BACKEND=claude-code uv run agent regenerate --target vault/recipes/claude-code-setup.md` が成功する
- [ ] 実行ログから所要時間が記録され、`metrics.md` に追記可能な形式で出力される
- [ ] ローカル Claude Code から `/wiki-regenerate vault/recipes/claude-code-setup.md` で AUTO 領域のみ更新されることを確認（Phase 2-A S-2 と同じ手順）

### 既定値切替（empirical PASS 後）

- [ ] `WIKI_LLM_BACKEND` 既定が `claude-code` に昇格している
- [ ] `CLAUDE.md` の `agent regenerate` 本番運用ガード注記が削除されている（Phase 2-A A-1-6）
- [ ] `metrics.md` に Phase 2-A の対象 16 本（公式 11 + recipe 5）の修正率が記録されている（Phase 2-A A-6-2 / A-6-3）

### エラーハンドリング

- [ ] API 呼び出し時の認証エラーが `LLMInvocationError` にラップされる
- [ ] `claude-agent-sdk` 内部例外も `LLMInvocationError` にラップされる（実 SDK 例外型の絞り込みは Phase 2-B で再検討）
- [ ] `cache_read_input_tokens` が取得できない場合、`LLMUsage` で `None` または明示的な未取得マーカーを返し、metrics.md は `N/A` で記録できる

### テスト

- [ ] `ClaudeCodeBackend` のユニットテストが追加され、mock 経由で `invoke` の挙動が検証されている
- [ ] バイナリ未存在時の `ConfigurationError` がテストで再現される
- [ ] テスト総数が **159 → 165 件以上** に増加（目安）
- [ ] `uv run pytest tests/` 全 PASS
- [ ] `uv run ruff check .` PASS
- [ ] `uv run mypy agent` PASS

### ADR

- [ ] ADR-018（LLM バックエンドの Claude Code 経由化）が `docs/core/decisions.md` に起票されている
- [ ] ADR-018 で `AnthropicBackend` / `StubBackend` 残置の判断が明文化されている

## スコープ外

### 今回対象外

- **GitHub Actions / CI 環境での `claude-code` バックエンド対応**: Max プラン認証は個人サブスクで CI では一般に通らない。CI は `anthropic` または `stub` で対応する運用方針（ADR-018 に明記、追加実装なし）
- **caching 効果の積極的計測**: Claude Code 経由では `cache_read_input_tokens` の観測可否が不確定。Phase 2-A の caching 検証は `AnthropicBackend` 側に残置
- **`AnthropicBackend` の廃止・既定降格**: CI / API 利用者向けに残置、選択肢として保持
- **`agent metrics` サブコマンドによる metrics.md 自動追記**: Phase 2-B 検討事項（acceptance-test-report.md §優先度低）
- **モデル切替 UI / 設定ファイル化**: env var で十分、複雑度を上げない
- **Web 公開パイプライン本体**: 生成はローカル → Web push という分離想定、本アイデアは生成側のみ

### 将来対応予定

- **Phase 2-B**: `AnthropicBackend` の `except Exception` を `anthropic.APIError` 等に絞り込み（acceptance-test-report.md §優先度低）と並行して、`ClaudeCodeBackend` の SDK 例外型も絞り込む
- **Phase 3**: GitHub Actions 週次 cron 実装時、CI 経路は `AnthropicBackend` で確定。ローカル cron / launchd 経路は `ClaudeCodeBackend` で運用
- **将来 Web 公開時**: 生成パイプライン（`ClaudeCodeBackend` 主軸）と公開パイプライン（静的サイト生成 + push）を分離

## 技術的考慮事項

### ディレクトリ構成（変更箇所）

```
wiki-for-claude-code/
├── agent/
│   └── orchestration/
│       └── llm.py                # ClaudeCodeBackend を追加（既存に追記のみ）
├── tests/
│   └── unit/
│       └── test_llm_claude_code.py  # 新規追加
├── pyproject.toml                # claude-agent-sdk 依存追加
├── .env.example                  # WIKI_LLM_BACKEND=claude-code 例追記
├── docs/
│   └── core/
│       └── decisions.md          # ADR-018 追記
└── CLAUDE.md                     # empirical PASS 後にガード注記削除
```

### 既存コードとの関係

- **再利用**: `LLMBackend` Protocol（`agent/orchestration/llm.py:61-71`）、`LLMResponse` / `LLMUsage` データクラス、`agent/errors.py` の例外階層（`ConfigurationError` / `LLMInvocationError`）
- **影響なし**: `AnthropicBackend`（`llm.py:101-169`）、`StubBackend`（`llm.py:73-98`）、既存テスト 159 件
- **間接影響**: `agent/orchestration/regenerate.py` のバックエンド選択ロジック（既存の `WIKI_LLM_BACKEND` 分岐に `claude-code` を追加）、Phase 2-A の `metrics.md`（修正率記録形式の継続性のみ）

### 依存コンポーネント

| コンポーネント | 用途 |
|--------------|------|
| `claude-agent-sdk` (Python) | Claude Code 経由の LLM 呼び出し本体 |
| `claude` CLI（ユーザー環境） | 認証情報の保管・サブスクリプション認証 |
| 既存 `anthropic` SDK | `AnthropicBackend` 経路で継続使用 |
| 既存 `httpx` | fetcher で継続使用、本機能では不使用 |

### パフォーマンス考慮

- **subprocess 起動オーバヘッド**: `claude-agent-sdk` は内部で claude CLI を起動するため、ネイティブ API 呼び出しより遅い。記事数 ~20 本 × 週次 = 数十回/週なので許容範囲
- **caching 効果の不確定性**: Claude Code が独自にプロンプトキャッシュを管理するため、`AnthropicBackend` で明示付与した `cache_control: ephemeral` とは別レイヤー。定額プラン前提なので金銭的影響は無視可能
- **メモリ・並列性**: Phase 2-A と同様、シーケンシャル処理を維持。並列化は Phase 2-B 以降の検討

### リスクと対策

| リスク | 影響度 | 対策 |
|-------|--------|------|
| `claude-agent-sdk` API 仕様の変動 | 中 | 公式パッケージのため大幅変更時は SDK 更新で追従、ADR-018 に依存方針を明記。ピン留めは行うが、上限は緩めにして mypy / pytest で破壊検出 |
| `claude` CLI の非互換変更（`claude-agent-sdk` 経由でも影響） | 中 | empirical 検証で動作確認、CI で `AnthropicBackend` 経路の検証を継続することで二重化 |
| Max プラン認証情報の取り回し（複数マシン展開時） | 低 | 本アイデアスコープ外、ローカル個人マシン主軸で OK |
| caching 効果の不可視化 | 低 | 主指標を修正率に切替、metrics.md は `N/A` 許容、`AnthropicBackend` 側で caching 検証を継続 |
| 既定切替タイミングのミス | 中 | empirical PASS 後の段階展開を ADR-018 に明文化、PR 単位で `WIKI_LLM_BACKEND` 既定変更を分離 |
| Phase 2-A 残課題（A-1-6 / A-6-2 / A-6-3 / S-2）との依存 | 中 | acceptance-test-report.md §6.1 案 Y 経路で本機能完成後に一括解消、依存順序を tasklist で明記 |
| CI 環境で `claude-code` 選択時の事故 | 低 | 起動時バイナリチェックでフェイルファスト、CI 設定で `WIKI_LLM_BACKEND=anthropic` を明示する運用 |

## 参照ドキュメント

- `.steering/20260506-llm-wiki-for-claude-code-phase-2a/acceptance-test-report.md` §6（方針更新の起点）
- `.steering/20260506-llm-wiki-for-claude-code-phase-2a/requirements.md`（Phase 2-A 受入れ条件）
- `.steering/20260506-llm-wiki-for-claude-code-phase-2a/validation-report.md`（コード検証結果）
- `agent/orchestration/llm.py`（`LLMBackend` Protocol、`StubBackend` / `AnthropicBackend` 既存実装）
- `agent/errors.py`（例外階層と exit code 対応）
- `docs/core/decisions.md`（ADR-001〜017 を踏襲、ADR-018 を追加予定）
- `CLAUDE.md`（Phase 2-A ステータスとガード注記）

## 更新履歴

- 2026-05-08: 初版作成（ブレインストーミングセッション）。実装方式 A（`claude-agent-sdk`）採用、env var 拡張、既定値段階展開、`StubBackend` 残置を確定。
