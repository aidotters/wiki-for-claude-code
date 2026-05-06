"""agent/validators/link_validator のテスト（HTTP モック）。"""

from __future__ import annotations

from pathlib import Path

import httpx

from agent.validators.link_validator import validate_file


def _make_source(tmp_path: Path) -> Path:
    p = tmp_path / "s.md"
    p.write_text(
        "---\n"
        "title: x\n"
        "type: source\n"
        "source_url: https://docs.claude.com/x\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    return p


def test_link_200_returns_no_issue(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(200))
    client = httpx.Client(transport=transport, follow_redirects=True)
    issues = validate_file(_make_source(tmp_path), client=client)
    assert issues == []


def test_link_404_returns_issue(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(404))
    client = httpx.Client(transport=transport, follow_redirects=True)
    issues = validate_file(_make_source(tmp_path), client=client)
    assert any("404" in i.message for i in issues)


def test_concept_skipped(tmp_path: Path) -> None:
    p = tmp_path / "c.md"
    p.write_text("---\ntitle: c\ntype: concept\n---\nbody\n", encoding="utf-8")
    issues = validate_file(p)
    assert issues == []
