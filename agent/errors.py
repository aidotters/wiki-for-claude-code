"""エラー型階層。終了コードと対応関係を持つ。

| エラー | 終了コード | 用途 |
|-------|-----------|------|
| FrontmatterValidationError | 1 | frontmatter 規約違反 |
| MarkdownRuleViolationError | 1 | Markdown 制約違反 |
| ThreePartViolationError | 1 | source 種別の縮退仕様違反（ADR-017） |
| TransclusionViolationError | 1 | 連続100文字一致違反 |
| CitationViolationError | 1 | 派生種別の引用必須違反 |
| SourceNotWhitelistedError | 2 | ホワイトリスト外取込み |
| FetchFailedError | 2 | HTTP 取得失敗 |
| LLMGenerationError | 3 | LLM 生成失敗 |
| ConfigurationError | 3 | 環境変数・API キー設定不正（Phase 2-A） |
| LLMInvocationError | 3 | Anthropic SDK 呼び出し失敗（Phase 2-A） |
| MalformedAutoMarkerError | 4 | AUTO マーカー構文不正（Phase 2-A） |
| LintViolationError | 4 | lint 違反 |
"""

from __future__ import annotations


class WikiError(Exception):
    exit_code: int = 1


class FrontmatterValidationError(WikiError):
    exit_code = 1


class MarkdownRuleViolationError(WikiError):
    exit_code = 1


class ThreePartViolationError(WikiError):
    exit_code = 1


class TransclusionViolationError(WikiError):
    exit_code = 1


class CitationViolationError(WikiError):
    exit_code = 1


class SourceNotWhitelistedError(WikiError):
    exit_code = 2


class FetchFailedError(WikiError):
    exit_code = 2


class LLMGenerationError(WikiError):
    exit_code = 3


class ConfigurationError(WikiError):
    """環境変数・設定不正（API キー欠落等）。Phase 2-A で追加。"""

    exit_code = 3


class LLMInvocationError(WikiError):
    """Anthropic SDK 呼び出し失敗（rate limit / network 等）。Phase 2-A で追加。"""

    exit_code = 3


class MalformedAutoMarkerError(WikiError):
    """AUTO マーカー構文不正。Phase 2-A で追加。"""

    exit_code = 4


EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_FETCH = 2
EXIT_LLM = 3
EXIT_LINT = 4
EXIT_AUTO_MARKER = 4
