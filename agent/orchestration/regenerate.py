"""regenerate_source ユースケース。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

from agent.errors import FrontmatterValidationError, LLMGenerationError
from agent.fetchers.http_fetcher import HttpFetcher, load_whitelist
from agent.orchestration.llm import LLMClient, StubLLMClient
from agent.prompts.loader import load_prompt, render_prompt
from agent.writers.frontmatter import FrontmatterDocument, parse
from agent.writers.markdown_writer import WriteResult, write
from agent.writers.nav_files import append_log


@dataclass
class RegenerateResult:
    article_path: Path
    write_result: WriteResult


def _extract_section(body: str, heading: str) -> str:
    """指定見出しから次の `## ` までを返す（含む）。"""
    idx = body.find(heading)
    if idx == -1:
        return ""
    next_idx = body.find("\n## ", idx + 1)
    if next_idx == -1:
        return body[idx:]
    return body[idx:next_idx]


def regenerate_source(
    target_path: Path,
    vault_root: Path,
    fetcher: HttpFetcher | None = None,
    llm: LLMClient | None = None,
    claude_code_version: str | None = None,
) -> RegenerateResult:
    if not target_path.exists():
        raise FileNotFoundError(f"target not found: {target_path}")
    target_path = target_path.resolve()
    vault_root = vault_root.resolve()

    existing_doc = parse(target_path.read_text(encoding="utf-8"))
    if existing_doc.metadata.get("type") != "source":
        raise FrontmatterValidationError(
            f"regenerate は type=source のみ対象: {target_path}"
        )
    source_url = existing_doc.metadata.get("source_url")
    if not isinstance(source_url, str):
        raise FrontmatterValidationError(
            f"source_url が無い、または不正: {target_path}"
        )

    if fetcher is None:
        whitelist = load_whitelist(vault_root / "90_meta" / "sources.md")
        fetcher = HttpFetcher(whitelist)

    if llm is None:
        llm = StubLLMClient()

    fetch_result = fetcher.fetch(source_url)

    # content_hash 比較で更新要否を判定
    existing_hash = existing_doc.metadata.get("source_version")  # ETag を使い回し
    if existing_hash and existing_hash == fetch_result.source_version:
        # 取込み元に変化なし。frontmatter の last_updated だけ更新するかは方針次第。
        # 冪等性のため、何も書き込まない。監査証跡として log.md には追記する。
        rel = target_path.relative_to(vault_root)
        append_log(vault_root, "regenerate", f"{rel} (no changes)")
        return RegenerateResult(
            article_path=target_path,
            write_result=WriteResult(
                file_path=target_path, changed=False, diff_summary="source unchanged"
            ),
        )

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    cc_version = claude_code_version or existing_doc.metadata.get(
        "claude_code_version", "1.5.0"
    )
    template = load_prompt("source-regenerate")
    existing_supplement = _extract_section(existing_doc.body, "## 補足解説 (日本語)")
    prompt = render_prompt(
        template,
        {
            "existing_frontmatter": yaml.safe_dump(
                existing_doc.metadata, allow_unicode=True, sort_keys=False
            ),
            "existing_supplement": existing_supplement,
            "raw_content": fetch_result.raw_content,
            "source_url": source_url,
            "today": today,
            "claude_code_version": str(cc_version),
        },
    )
    generated = llm.generate(prompt)
    if not generated.strip():
        raise LLMGenerationError("LLM が空応答を返しました")
    try:
        new_doc = parse(generated)
    except ValueError as e:
        raise LLMGenerationError(f"LLM 応答のパースに失敗: {e}") from e

    # frontmatter の保持・更新ルール
    preserved_keys = {
        "title",
        "tags",
        "reviewer",
        "human_edited",
        "status",
        "auto_section_managed",
        "sources",
        "source_url",
    }
    merged_meta = dict(new_doc.metadata)
    for k in preserved_keys:
        if k in existing_doc.metadata:
            merged_meta[k] = existing_doc.metadata[k]
    merged_meta["fetched_at"] = fetch_result.fetched_at
    merged_meta["last_updated"] = today
    merged_meta["stale"] = False
    if fetch_result.source_version is not None:
        merged_meta["source_version"] = fetch_result.source_version

    # 補足解説セクションを既存のもので置換
    new_supplement = _extract_section(new_doc.body, "## 補足解説 (日本語)")
    if existing_supplement and new_supplement:
        new_body = new_doc.body.replace(new_supplement, existing_supplement)
    else:
        new_body = new_doc.body

    final_doc = FrontmatterDocument(metadata=merged_meta, body=new_body)
    write_result = write(target_path, final_doc)
    rel = target_path.relative_to(vault_root)
    status = "updated" if write_result.changed else "no changes"
    append_log(vault_root, "regenerate", f"{rel} ({status})")
    return RegenerateResult(article_path=target_path, write_result=write_result)
