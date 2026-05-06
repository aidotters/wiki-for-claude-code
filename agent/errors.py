"""エラー型階層。終了コードと対応関係を持つ。

| エラー | 終了コード | 用途 |
|-------|-----------|------|
| FrontmatterValidationError | 1 | frontmatter 規約違反 |
| MarkdownRuleViolationError | 1 | Markdown 制約違反 |
| ThreePartViolationError | 1 | source 種別の3部構成違反 |
| TransclusionViolationError | 1 | 連続100文字一致違反 |
| CitationViolationError | 1 | 派生種別の引用必須違反 |
| SourceNotWhitelistedError | 2 | ホワイトリスト外取込み |
| FetchFailedError | 2 | HTTP 取得失敗 |
| LLMGenerationError | 3 | LLM 生成失敗 |
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


class LintViolationError(WikiError):
    exit_code = 4


EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_FETCH = 2
EXIT_LLM = 3
EXIT_LINT = 4
