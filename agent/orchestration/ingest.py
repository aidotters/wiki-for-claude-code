"""ingest_source ユースケース。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from agent.errors import LLMGenerationError, SourceNotWhitelistedError
from agent.fetchers.http_fetcher import HttpFetcher, load_whitelist
from agent.orchestration.llm import LLMClient, StubLLMClient
from agent.prompts.loader import load_prompt, render_prompt
from agent.writers.frontmatter import parse
from agent.writers.markdown_writer import WriteResult, write
from agent.writers.nav_files import append_log

VALID_CATEGORIES = {"hooks", "cli", "slash-commands", "mcp", "settings", "sdk"}


@dataclass
class IngestResult:
    article_path: Path
    write_result: WriteResult


def slug_from_url(url: str) -> str:
    """URL の末尾から記事 slug を作る。"""
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", tail).strip("-")
    return slug or "untitled"


def has_existing_source(vault_root: Path, source_url: str) -> Path | None:
    """同一 source_url を持つ既存ページを検索する。"""
    for path in (vault_root / "sources").rglob("*.md"):
        try:
            doc = parse(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        if doc.metadata.get("source_url") == source_url:
            return path
    return None


def ingest_source(
    source_url: str,
    category: str,
    vault_root: Path,
    fetcher: HttpFetcher | None = None,
    llm: LLMClient | None = None,
    claude_code_version: str = "1.5.0",
) -> IngestResult:
    """新ソース取込みユースケース。"""
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")

    if fetcher is None:
        whitelist = load_whitelist(vault_root / "90_meta" / "sources.md")
        fetcher = HttpFetcher(whitelist)

    if llm is None:
        llm = StubLLMClient()

    existing = has_existing_source(vault_root, source_url)
    if existing is not None:
        raise FileExistsError(
            f"既に同一 source_url のページが存在します: {existing}（regenerate を使用してください）"
        )

    fetch_result = fetcher.fetch(source_url)
    template = load_prompt("source-ingest")
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    prompt = render_prompt(
        template,
        {
            "source_url": source_url,
            "category": category,
            "claude_code_version": claude_code_version,
            "today": today,
            "raw_content": fetch_result.raw_content,
        },
    )
    generated = llm.generate(prompt)
    if not generated.strip():
        raise LLMGenerationError("LLM が空の応答を返しました")
    try:
        new_doc = parse(generated)
    except ValueError as e:
        raise LLMGenerationError(f"LLM 応答のパースに失敗: {e}") from e

    if new_doc.metadata.get("type") != "source":
        raise LLMGenerationError("LLM 応答が type=source ではありません")

    new_doc.metadata["source_url"] = source_url
    new_doc.metadata["fetched_at"] = fetch_result.fetched_at
    new_doc.metadata["last_updated"] = today
    if fetch_result.source_version is not None:
        new_doc.metadata["source_version"] = fetch_result.source_version

    slug = slug_from_url(source_url)
    article_path = vault_root / "sources" / "official" / category / f"{slug}.md"
    write_result = write(article_path, new_doc)
    rel = article_path.relative_to(vault_root)
    append_log(vault_root, "ingest", f"{rel} from {source_url}")
    return IngestResult(article_path=article_path, write_result=write_result)


__all__ = [
    "IngestResult",
    "SourceNotWhitelistedError",
    "ingest_source",
    "slug_from_url",
]
