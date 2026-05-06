"""agent/fetchers/http_fetcher のテスト。"""

from __future__ import annotations

import httpx
import pytest

from agent.errors import FetchFailedError, SourceNotWhitelistedError
from agent.fetchers.http_fetcher import (
    HttpFetcher,
    is_whitelisted,
    load_whitelist,
)
from tests.conftest import REPO_ROOT

WHITELIST_FIXTURE = [
    {
        "id": "anthropic-claude-docs",
        "name": "Anthropic",
        "base_url": "https://docs.claude.com/",
        "fetch_method": "http",
        "rate_limit": "1 req/sec",
        "license_notes": "...",
        "enabled": True,
    },
    {
        "id": "disabled-source",
        "name": "Disabled",
        "base_url": "https://example.com/",
        "fetch_method": "http",
        "rate_limit": "...",
        "license_notes": "...",
        "enabled": False,
    },
]


def _make_fetcher(transport: httpx.MockTransport) -> HttpFetcher:
    client = httpx.Client(transport=transport, follow_redirects=True)
    return HttpFetcher(WHITELIST_FIXTURE, rate_limit_sleep=0, client=client)


def test_is_whitelisted_allows_anthropic() -> None:
    assert is_whitelisted("https://docs.claude.com/claude-code/cli", WHITELIST_FIXTURE) is True


def test_is_whitelisted_rejects_disabled() -> None:
    assert is_whitelisted("https://example.com/page", WHITELIST_FIXTURE) is False


def test_is_whitelisted_rejects_unknown() -> None:
    assert is_whitelisted("https://other.example.org/", WHITELIST_FIXTURE) is False


def test_load_whitelist_from_real_sources_md() -> None:
    sources_md = REPO_ROOT / "vault" / "90_meta" / "sources.md"
    wl = load_whitelist(sources_md)
    ids = [s.get("id") for s in wl]
    assert "anthropic-claude-code-docs-ja" in ids
    assert "anthropic-claude-code-docs-en" in ids
    # 旧ドメインも redirect 追跡用に残置
    assert "anthropic-claude-docs-legacy" in ids


def test_fetch_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="hello world")

    fetcher = _make_fetcher(httpx.MockTransport(handler))
    result = fetcher.fetch("https://docs.claude.com/claude-code/page")
    assert result.raw_content == "hello world"
    assert result.content_hash
    assert result.fetched_at.endswith("Z")


def test_fetch_404_raises_fetch_failed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    fetcher = _make_fetcher(httpx.MockTransport(handler))
    with pytest.raises(FetchFailedError):
        fetcher.fetch("https://docs.claude.com/claude-code/missing")


def test_fetch_500_raises_fetch_failed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    fetcher = _make_fetcher(httpx.MockTransport(handler))
    with pytest.raises(FetchFailedError):
        fetcher.fetch("https://docs.claude.com/claude-code/error")


def test_fetch_non_whitelisted_raises() -> None:
    fetcher = HttpFetcher(WHITELIST_FIXTURE, rate_limit_sleep=0)
    with pytest.raises(SourceNotWhitelistedError):
        fetcher.fetch("https://other.example.org/")
