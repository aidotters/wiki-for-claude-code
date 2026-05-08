"""orchestration ユースケースの統合テスト（LLM スタブ + Mock HTTP）。"""

from __future__ import annotations

import shutil
from pathlib import Path

import httpx
import pytest

from agent.errors import (
    FrontmatterValidationError,
    SourceNotWhitelistedError,
)
from agent.fetchers.http_fetcher import HttpFetcher
from agent.orchestration.ingest import ingest_source, slug_from_url
from agent.orchestration.lint import lint_all
from agent.orchestration.llm import StubLLMClient
from agent.orchestration.regenerate import regenerate_source
from agent.orchestration.validate import validate_all, validate_target

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
    """テスト用 vault を実 schema/sources を含めて構築する。"""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "sources" / "official" / "hooks").mkdir(parents=True)
    (vault / "sources" / "official" / "cli").mkdir(parents=True)
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


def _make_fetcher() -> HttpFetcher:
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200,
            text="raw content from official docs about hooks 公式コンテンツ",
            headers={"ETag": "v1"},
        )
    )
    client = httpx.Client(transport=transport, follow_redirects=True)
    return HttpFetcher(WHITELIST, rate_limit_sleep=0, client=client)


def _stub_response(source_url: str, fetched_at: str = "2026-05-05T10:00:00Z") -> str:
    return f"""---
title: "Pre-Tool-Use Hook"
type: source
confidence: 0.85
sources: []
last_updated: 2026-05-05
stale: false
tags: [hooks, pre-tool-use]
source_url: "{source_url}"
fetched_at: "{fetched_at}"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: false
status: draft
auto_section_managed: true
---

## 概要 (要約)
<!-- AUTO:START purpose=summary-1-paragraph -->
Pre-Tool-Use Hook はツール実行前に呼ばれます。
<!-- AUTO:END -->

## 公式ドキュメント
→ {source_url}
（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）
"""


def test_slug_from_url() -> None:
    assert slug_from_url("https://docs.claude.com/claude-code/hooks/pre-tool-use") == "pre-tool-use"
    assert slug_from_url("https://docs.claude.com/claude-code/hooks/") == "hooks"


def test_ingest_creates_article(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    url = "https://docs.claude.com/claude-code/hooks/pre-tool-use"
    llm = StubLLMClient(fixed_response=_stub_response(url))
    result = ingest_source(
        url, "hooks", vault_root=vault, fetcher=_make_fetcher(), llm=llm
    )
    assert result.article_path.exists()
    assert result.article_path.parent.name == "hooks"
    assert result.article_path.name == "pre-tool-use.md"
    assert result.write_result.changed is True
    log_text = (vault / "log.md").read_text(encoding="utf-8")
    assert "ingest" in log_text


def test_ingest_rejects_non_whitelisted(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    with pytest.raises(SourceNotWhitelistedError):
        ingest_source(
            "https://other.example.org/page",
            "hooks",
            vault_root=vault,
            fetcher=HttpFetcher(WHITELIST, rate_limit_sleep=0),
            llm=StubLLMClient(),
        )


def test_ingest_rejects_invalid_category(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    with pytest.raises(ValueError):
        ingest_source(
            "https://docs.claude.com/x",
            "tutorials",
            vault_root=vault,
            fetcher=_make_fetcher(),
            llm=StubLLMClient(),
        )


def test_ingest_duplicate_url_raises(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    url = "https://docs.claude.com/claude-code/hooks/duplicate"
    llm = StubLLMClient(fixed_response=_stub_response(url))
    ingest_source(url, "hooks", vault_root=vault, fetcher=_make_fetcher(), llm=llm)
    with pytest.raises(FileExistsError):
        ingest_source(url, "hooks", vault_root=vault, fetcher=_make_fetcher(), llm=llm)


def test_regenerate_idempotent(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    url = "https://docs.claude.com/claude-code/hooks/idempotent"
    llm = StubLLMClient(fixed_response=_stub_response(url))
    ingest = ingest_source(url, "hooks", vault_root=vault, fetcher=_make_fetcher(), llm=llm)

    # ingest 時に ETag を populate するため、初回 regenerate から完全冪等
    first = regenerate_source(
        ingest.article_path, vault_root=vault, fetcher=_make_fetcher(), llm=llm
    )
    assert first.write_result.changed is False
    second = regenerate_source(
        ingest.article_path, vault_root=vault, fetcher=_make_fetcher(), llm=llm
    )
    assert second.write_result.changed is False


def test_regenerate_logs_even_when_no_changes(tmp_path: Path, repo_root: Path) -> None:
    """no changes でも log.md に regenerate エントリが追記される（監査証跡）。"""
    vault = _make_vault(tmp_path, repo_root)
    url = "https://docs.claude.com/claude-code/hooks/audit"
    llm = StubLLMClient(fixed_response=_stub_response(url))
    ingest = ingest_source(url, "hooks", vault_root=vault, fetcher=_make_fetcher(), llm=llm)

    log_before = (vault / "log.md").read_text(encoding="utf-8")
    result = regenerate_source(
        ingest.article_path, vault_root=vault, fetcher=_make_fetcher(), llm=llm
    )
    assert result.write_result.changed is False
    log_after = (vault / "log.md").read_text(encoding="utf-8")
    assert log_after != log_before
    rel = str(ingest.article_path.relative_to(vault))
    assert "regenerate" in log_after
    assert rel in log_after
    assert "no changes" in log_after


def test_regenerate_rejects_non_source(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    target = vault / "concepts" / "x.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "---\ntitle: c\ntype: concept\nsources: []\n---\nbody\n", encoding="utf-8"
    )
    with pytest.raises(FrontmatterValidationError):
        regenerate_source(target, vault_root=vault)


def test_validate_target_passes_for_well_formed(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    url = "https://docs.claude.com/claude-code/hooks/well-formed"
    ingest = ingest_source(
        url,
        "hooks",
        vault_root=vault,
        fetcher=_make_fetcher(),
        llm=StubLLMClient(fixed_response=_stub_response(url)),
    )
    summary = validate_target(ingest.article_path, vault_root=vault)
    assert summary.passed, summary.format()


def test_validate_all_passes_with_only_well_formed(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    url = "https://docs.claude.com/claude-code/hooks/all-pass"
    ingest_source(
        url,
        "hooks",
        vault_root=vault,
        fetcher=_make_fetcher(),
        llm=StubLLMClient(fixed_response=_stub_response(url)),
    )
    summary = validate_all(vault)
    assert summary.passed, summary.format()


def test_lint_all_writes_log(tmp_path: Path, repo_root: Path) -> None:
    vault = _make_vault(tmp_path, repo_root)
    report = lint_all(vault)
    log_text = (vault / "log.md").read_text(encoding="utf-8")
    assert "lint" in log_text
    assert isinstance(report.total_violations, int)


def test_validate_target_with_raw_content_detects_transclusion(
    tmp_path: Path, repo_root: Path
) -> None:
    """source 種別記事と raw コンテンツで連続100文字一致がある場合 FAIL する。"""
    vault = _make_vault(tmp_path, repo_root)
    url = "https://docs.claude.com/claude-code/hooks/transclusion-test"
    common = "あ" * 120
    article_response = f"""---
title: "Transclusion Test"
type: source
confidence: 0.85
sources: []
last_updated: 2026-05-05
stale: false
tags: [hooks, test]
source_url: "{url}"
fetched_at: "2026-05-05T10:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: false
status: draft
auto_section_managed: false
---

## 概要 (要約)
{common}

## 公式ドキュメント
→ {url}
（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）

## 補足解説 (日本語)
本文補足。
"""
    ingest = ingest_source(
        url,
        "hooks",
        vault_root=vault,
        fetcher=_make_fetcher(),
        llm=StubLLMClient(fixed_response=article_response),
    )

    # raw_content に 100 文字超の同一連結を含めれば transclusion FAIL
    raw_with_match = f"raw prefix {common} raw suffix"
    summary = validate_target(
        ingest.article_path,
        vault_root=vault,
        raw_content=raw_with_match,
    )
    assert not summary.passed
    assert any(issue.field == "transclusion" for issue in summary.issues)

    # raw_content を渡さなければ transclusion 検査はスキップ（CI 向け既定動作）
    summary_offline = validate_target(ingest.article_path, vault_root=vault)
    assert summary_offline.passed, summary_offline.format()
