"""awesome-claude-code リポジトリの README からエントリを抽出する fetcher。

Phase 2-A / A-3: コミュニティ source の取込み。

設計方針:
- GitHub raw content API（`https://raw.githubusercontent.com/<owner>/<repo>/<ref>/README.md`）経由で取得
- README は構造化マークダウン（ヘッダ階層 + リンク列挙）として解釈
- 各エントリは `(parent_section, title, url, description)` の 4 要素として抽出
- コミット SHA は API レスポンスから取得し、`FetchedEntry.commit_sha` に格納する想定
  （Phase 2-A は手動指定モードを許容、自動解決は Phase 2-B 検討）
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

from agent.errors import FetchFailedError, SourceNotWhitelistedError
from agent.fetchers.http_fetcher import DEFAULT_USER_AGENT

# README 内のリンク列挙行を抽出する正規表現
# 例: `- [Title](https://example.com) - description`
LINK_LINE_PATTERN = re.compile(r"^\s*[-*]\s*\[([^\]]+)\]\(([^)]+)\)\s*[-—:]?\s*(.*)$")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class FetchedEntry:
    """awesome-claude-code リスト内の 1 エントリ。"""

    title: str
    url: str
    description: str
    parent_section: str
    commit_sha: str
    raw_line: str


@dataclass
class AwesomeClaudeCodeFetcher:
    """awesome-claude-code リスト fetcher。

    `whitelist` には `vault/90_meta/sources.md` から読み込まれた YAML を渡す。
    ホワイトリスト中の `awesome-claude-code` エントリの `base_url` で URL を検証する。
    """

    whitelist: list[dict[str, Any]]
    user_agent: str = DEFAULT_USER_AGENT
    timeout: float = 30.0
    client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self.client is None:
            self.client = httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            )
        return self.client

    def _verify_whitelist(self, url: str) -> dict[str, Any]:
        """`awesome-claude-code` エントリにマッチするか検証し、エントリを返す。"""
        for source in self.whitelist:
            if source.get("id") != "awesome-claude-code":
                continue
            if not source.get("enabled", False):
                continue
            base = source.get("base_url", "")
            raw_base = source.get("raw_base_url", "")
            if (base and url.startswith(base)) or (raw_base and url.startswith(raw_base)):
                return source
        raise SourceNotWhitelistedError(
            f"URL がホワイトリスト `awesome-claude-code` に該当しません: {url}"
        )

    def fetch_readme(
        self,
        readme_url: str,
        commit_sha: str,
    ) -> str:
        """README 全文を GitHub raw 経由で取得する。

        `commit_sha` はピン留めのために必須（mutable な `main` ブランチを避ける）。
        """
        self._verify_whitelist(readme_url)
        try:
            response = self._get_client().get(readme_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise FetchFailedError(f"awesome-claude-code README 取得失敗: {e}") from e
        return response.text

    def parse_entries(self, readme_text: str, commit_sha: str) -> list[FetchedEntry]:
        """README 文字列から構造化エントリを抽出する。

        - 行頭ヘッダ（`# ... ###### `）を `parent_section` として保持
        - リスト項目（`- [Title](URL) - description`）を `FetchedEntry` 化
        - 適切に解釈できない行はスキップ（コードブロック内 / 段落内テキストなど）
        """
        entries: list[FetchedEntry] = []
        current_section_stack: list[tuple[int, str]] = []  # (level, title)
        in_code_block = False

        for raw_line in readme_text.splitlines():
            if raw_line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            heading_match = HEADING_PATTERN.match(raw_line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                # スタックから level 以上を削除
                while current_section_stack and current_section_stack[-1][0] >= level:
                    current_section_stack.pop()
                current_section_stack.append((level, title))
                continue

            link_match = LINK_LINE_PATTERN.match(raw_line)
            if not link_match:
                continue

            title = link_match.group(1).strip()
            url = link_match.group(2).strip()
            description = link_match.group(3).strip()
            parent = (
                " > ".join(s for _, s in current_section_stack)
                if current_section_stack
                else ""
            )
            entries.append(
                FetchedEntry(
                    title=title,
                    url=url,
                    description=description,
                    parent_section=parent,
                    commit_sha=commit_sha,
                    raw_line=raw_line,
                )
            )

        return entries

    def fetch_entries(
        self,
        readme_url: str,
        commit_sha: str,
    ) -> list[FetchedEntry]:
        """README を取得 + パース。"""
        readme_text = self.fetch_readme(readme_url, commit_sha)
        return self.parse_entries(readme_text, commit_sha)
