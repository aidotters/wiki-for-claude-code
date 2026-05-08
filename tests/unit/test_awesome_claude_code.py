"""awesome-claude-code fetcher のユニットテスト（Phase 2-A / A-3）。"""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from agent.errors import FetchFailedError, SourceNotWhitelistedError
from agent.fetchers.awesome_claude_code import (
    AwesomeClaudeCodeFetcher,
    FetchedEntry,
)

WHITELIST = [
    {
        "id": "awesome-claude-code",
        "enabled": True,
        "base_url": "https://github.com/hesreallyhim/awesome-claude-code",
        "raw_base_url": "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/",
    }
]


SAMPLE_README = """# awesome-claude-code

Curated list.

## Hooks

- [Pre-commit hook](https://github.com/example/pre-commit) - Run lint before commit.
- [Test runner](https://github.com/example/test-runner) — Auto-run tests after edit.

### Advanced

- [Multi-stage hook](https://github.com/example/multi-stage) - Pipeline of hooks.

## MCP

- [SQL MCP server](https://github.com/example/sql-mcp): Database access via MCP.

```text
some code block
- [Should not match](https://example.com) - inside code block
```

## Workflows

- Plain text without link
- [Refactor flow](https://github.com/example/refactor)
"""


class TestParseEntries:
    def test_extracts_links_with_sections(self) -> None:
        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST)
        entries = fetcher.parse_entries(SAMPLE_README, commit_sha="abc123")

        # 5 entries (Pre-commit, Test runner, Multi-stage, SQL MCP, Refactor flow)
        assert len(entries) == 5

        # First entry: Pre-commit hook in Hooks section
        first = entries[0]
        assert first.title == "Pre-commit hook"
        assert first.url == "https://github.com/example/pre-commit"
        assert first.description == "Run lint before commit."
        assert "Hooks" in first.parent_section
        assert first.commit_sha == "abc123"

    def test_extracts_em_dash_separator(self) -> None:
        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST)
        entries = fetcher.parse_entries(SAMPLE_README, commit_sha="abc")
        test_runner = next(e for e in entries if e.title == "Test runner")
        assert test_runner.description == "Auto-run tests after edit."

    def test_extracts_colon_separator(self) -> None:
        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST)
        entries = fetcher.parse_entries(SAMPLE_README, commit_sha="abc")
        sql = next(e for e in entries if e.title == "SQL MCP server")
        assert sql.description == "Database access via MCP."

    def test_no_description_allowed(self) -> None:
        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST)
        entries = fetcher.parse_entries(SAMPLE_README, commit_sha="abc")
        refactor = next(e for e in entries if e.title == "Refactor flow")
        assert refactor.description == ""

    def test_skips_code_block_content(self) -> None:
        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST)
        entries = fetcher.parse_entries(SAMPLE_README, commit_sha="abc")
        # Should not include "Should not match"
        assert all("Should not match" not in e.title for e in entries)

    def test_section_hierarchy_preserved(self) -> None:
        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST)
        entries = fetcher.parse_entries(SAMPLE_README, commit_sha="abc")
        multi = next(e for e in entries if e.title == "Multi-stage hook")
        # Should be under Hooks > Advanced
        assert "Hooks" in multi.parent_section
        assert "Advanced" in multi.parent_section


class TestWhitelistVerification:
    def test_whitelist_match_allows_fetch(self) -> None:
        client = MagicMock()
        response = MagicMock()
        response.text = SAMPLE_README
        response.raise_for_status = MagicMock()
        client.get.return_value = response

        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST, client=client)
        text = fetcher.fetch_readme(
            "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/abc123/README.md",
            commit_sha="abc123",
        )
        assert "awesome-claude-code" in text

    def test_unknown_url_rejected(self) -> None:
        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST)
        with pytest.raises(SourceNotWhitelistedError):
            fetcher.fetch_readme(
                "https://raw.githubusercontent.com/other/repo/main/README.md",
                commit_sha="abc",
            )

    def test_disabled_whitelist_rejects(self) -> None:
        whitelist = [{**WHITELIST[0], "enabled": False}]
        fetcher = AwesomeClaudeCodeFetcher(whitelist=whitelist)
        with pytest.raises(SourceNotWhitelistedError):
            fetcher.fetch_readme(
                "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/abc/README.md",
                commit_sha="abc",
            )

    def test_http_error_wrapped(self) -> None:
        client = MagicMock()
        client.get.side_effect = httpx.HTTPError("net down")
        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST, client=client)
        with pytest.raises(FetchFailedError):
            fetcher.fetch_readme(
                "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/abc/README.md",
                commit_sha="abc",
            )


class TestFetchEntries:
    def test_fetch_entries_combines_fetch_and_parse(self) -> None:
        client = MagicMock()
        response = MagicMock()
        response.text = SAMPLE_README
        response.raise_for_status = MagicMock()
        client.get.return_value = response

        fetcher = AwesomeClaudeCodeFetcher(whitelist=WHITELIST, client=client)
        entries = fetcher.fetch_entries(
            "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/abc/README.md",
            commit_sha="abc",
        )
        assert len(entries) == 5
        assert all(isinstance(e, FetchedEntry) for e in entries)
        assert all(e.commit_sha == "abc" for e in entries)
