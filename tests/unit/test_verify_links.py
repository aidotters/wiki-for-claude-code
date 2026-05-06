"""agent/orchestration/verify_links のテスト（HTTP モック）。"""

from __future__ import annotations

import shutil
from pathlib import Path

import httpx

from agent.fetchers.http_fetcher import HttpFetcher
from agent.orchestration.verify_links import verify_links

WHITELIST = [
    {
        "id": "anthropic-claude-docs",
        "name": "Anthropic",
        "base_url": "https://docs.claude.com/",
        "fetch_method": "http",
        "rate_limit": "1 req/sec",
        "license_notes": "...",
        "enabled": True,
    }
]


def _make_vault(tmp_path: Path, repo_root: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "sources" / "official" / "hooks").mkdir(parents=True)
    (vault / "90_meta" / "_schemas").mkdir(parents=True)
    shutil.copy(
        repo_root / "vault" / "90_meta" / "_schemas" / "frontmatter.schema.json",
        vault / "90_meta" / "_schemas" / "frontmatter.schema.json",
    )
    shutil.copy(
        repo_root / "vault" / "90_meta" / "sources.md",
        vault / "90_meta" / "sources.md",
    )
    (vault / "index.md").write_text("# Index\n", encoding="utf-8")
    (vault / "log.md").write_text("# Log\n", encoding="utf-8")
    return vault


def _write_source(target: Path, url: str, body: str = "本文") -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"""---
title: x
type: source
confidence: 0.85
sources: []
last_updated: 2026-05-05
stale: false
tags: [hooks]
source_url: "{url}"
fetched_at: "2026-05-05T10:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: tak
human_edited: true
status: draft
auto_section_managed: false
---

## 概要 (要約)
{body}

## 公式ドキュメント
→ {url}
（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)
補足。
""",
        encoding="utf-8",
    )


def test_verify_links_passes_with_200_and_no_match(
    tmp_path: Path, repo_root: Path
) -> None:
    vault = _make_vault(tmp_path, repo_root)
    article = vault / "sources" / "official" / "hooks" / "x.md"
    _write_source(article, "https://docs.claude.com/claude-code/hooks/x", body="独自要約")

    head_client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200)),
        follow_redirects=True,
    )
    fetch_client = httpx.Client(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200,
                text="完全に異なる raw コンテンツ",
                headers={"ETag": "v1"},
            )
        ),
        follow_redirects=True,
    )
    fetcher = HttpFetcher(WHITELIST, rate_limit_sleep=0, client=fetch_client)
    summary = verify_links(
        vault_root=vault,
        http_client=head_client,
        fetcher=fetcher,
    )
    assert summary.files_checked == 1
    assert summary.passed, summary.format()


def test_verify_links_fails_on_404(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    article = vault / "sources" / "official" / "hooks" / "y.md"
    _write_source(article, "https://docs.claude.com/claude-code/hooks/y")

    head_client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(404)),
        follow_redirects=True,
    )
    summary = verify_links(
        vault_root=vault,
        http_client=head_client,
        check_transclusion=False,
    )
    assert not summary.passed
    assert any("404" in i.message for i in summary.issues)


def test_verify_links_detects_transclusion(
    tmp_path: Path, repo_root: Path
) -> None:
    vault = _make_vault(tmp_path, repo_root)
    common = "あ" * 120
    article = vault / "sources" / "official" / "hooks" / "z.md"
    _write_source(
        article, "https://docs.claude.com/claude-code/hooks/z", body=common
    )

    head_client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200)),
        follow_redirects=True,
    )
    fetch_client = httpx.Client(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200,
                text=f"prefix {common} suffix",
                headers={"ETag": "v1"},
            )
        ),
        follow_redirects=True,
    )
    fetcher = HttpFetcher(WHITELIST, rate_limit_sleep=0, client=fetch_client)
    summary = verify_links(
        vault_root=vault,
        http_client=head_client,
        fetcher=fetcher,
    )
    assert not summary.passed
    assert any(i.field == "transclusion" for i in summary.issues)
