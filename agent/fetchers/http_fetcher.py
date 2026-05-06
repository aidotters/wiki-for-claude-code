"""HTTP 取得層。ホワイトリスト検証 + レート制限 sleep を含む。"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

from agent.errors import FetchFailedError, SourceNotWhitelistedError

DEFAULT_USER_AGENT = "llm-wiki-for-claude-code/0.1 (https://github.com/anthropics/claude-code)"
DEFAULT_TIMEOUT = 30.0
DEFAULT_RATE_LIMIT_SLEEP = 0.1  # 秒


@dataclass
class FetchResult:
    raw_content: str
    fetched_at: str
    source_version: str | None
    content_hash: str
    source_url: str


def load_whitelist(sources_md_path: Path) -> list[dict[str, Any]]:
    """vault/90_meta/sources.md の YAML ブロックからホワイトリストを抽出する。"""
    text = sources_md_path.read_text(encoding="utf-8")
    in_yaml = False
    yaml_lines: list[str] = []
    for line in text.splitlines():
        if line.strip() == "```yaml":
            in_yaml = True
            continue
        if line.strip() == "```" and in_yaml:
            break
        if in_yaml:
            yaml_lines.append(line)

    if not yaml_lines:
        return []
    parsed = yaml.safe_load("\n".join(yaml_lines)) or {}
    sources = parsed.get("sources", [])
    if not isinstance(sources, list):
        return []
    return sources


def is_whitelisted(url: str, whitelist: list[dict[str, Any]]) -> bool:
    """URL がホワイトリストの enabled なソースの base_url で始まるか確認する。"""
    for source in whitelist:
        if not source.get("enabled", False):
            continue
        base = source.get("base_url", "")
        if base and url.startswith(base):
            return True
    return False


class HttpFetcher:
    """HTTP GET 経由のフェッチャ。"""

    def __init__(
        self,
        whitelist: list[dict[str, Any]],
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = DEFAULT_TIMEOUT,
        rate_limit_sleep: float = DEFAULT_RATE_LIMIT_SLEEP,
        client: httpx.Client | None = None,
    ) -> None:
        self.whitelist = whitelist
        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_limit_sleep = rate_limit_sleep
        self._client = client

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            )
        return self._client

    def fetch(self, source_url: str) -> FetchResult:
        if not is_whitelisted(source_url, self.whitelist):
            raise SourceNotWhitelistedError(
                f"URL not in whitelist: {source_url}"
            )
        time.sleep(self.rate_limit_sleep)
        try:
            response = self._get_client().get(source_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise FetchFailedError(f"Fetch failed for {source_url}: {e}") from e

        raw = response.text
        return FetchResult(
            raw_content=raw,
            fetched_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            source_version=response.headers.get("etag"),
            content_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            source_url=source_url,
        )
