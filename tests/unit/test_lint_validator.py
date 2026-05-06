"""agent/validators/lint_validator のテスト。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from agent.validators.lint_validator import lint_vault


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_source_md(
    last_updated: str = "2026-05-05",
    confidence: float = 0.9,
    stale: bool = False,
    status: str = "published",
    tags: list[str] | None = None,
    body: str = "",
) -> str:
    tags_repr = tags or ["sample"]
    tags_yaml = "[" + ", ".join(tags_repr) + "]"
    return (
        "---\n"
        "title: T\n"
        "type: source\n"
        f"confidence: {confidence}\n"
        "sources: []\n"
        f"last_updated: {last_updated}\n"
        f"stale: {str(stale).lower()}\n"
        f"tags: {tags_yaml}\n"
        "source_url: https://docs.claude.com/x\n"
        "fetched_at: '2026-05-05T10:00:00Z'\n"
        "claude_code_version: '1.5.0'\n"
        "reviewer: tak\n"
        "human_edited: true\n"
        f"status: {status}\n"
        "auto_section_managed: false\n"
        "---\n"
        f"\n{body}\n"
    )


def test_orphan_detection(tmp_path: Path) -> None:
    _write(tmp_path / "index.md", "# Index\n- [[sources/official/cli/a]]\n")
    _write(tmp_path / "sources/official/cli/a.md", _make_source_md(body="A"))
    _write(tmp_path / "sources/official/cli/orphan.md", _make_source_md(body="Orphan"))
    report = lint_vault(tmp_path, today=date(2026, 5, 5))
    assert any(p.name == "orphan.md" for p in report.orphans)


def test_stale_by_last_updated(tmp_path: Path) -> None:
    _write(tmp_path / "index.md", "# Index\n- [[sources/official/cli/a]]\n")
    _write(
        tmp_path / "sources/official/cli/a.md",
        _make_source_md(last_updated="2026-01-01", body="old"),
    )
    report = lint_vault(tmp_path, today=date(2026, 5, 5))
    assert any(p.name == "a.md" for p, _ in report.stale)


def test_stale_by_flag(tmp_path: Path) -> None:
    _write(tmp_path / "index.md", "# Index\n- [[a]]\n")
    _write(
        tmp_path / "a.md",
        _make_source_md(stale=True, body="stale"),
    )
    report = lint_vault(tmp_path, today=date(2026, 5, 5))
    assert any(p.name == "a.md" for p, _ in report.stale)


def test_low_confidence(tmp_path: Path) -> None:
    _write(tmp_path / "index.md", "# Index\n- [[low]]\n")
    _write(tmp_path / "low.md", _make_source_md(confidence=0.3, body="x"))
    report = lint_vault(tmp_path, today=date(2026, 5, 5))
    assert any(p.name == "low.md" for p, _ in report.low_confidence)


def test_broken_wikilink(tmp_path: Path) -> None:
    _write(tmp_path / "index.md", "# Index\n- [[a]]\n")
    _write(tmp_path / "a.md", _make_source_md(body="See [[nonexistent]]"))
    report = lint_vault(tmp_path, today=date(2026, 5, 5))
    assert any("nonexistent" in link for _, link in report.broken_wikilinks)


def test_index_sync_missing(tmp_path: Path) -> None:
    _write(tmp_path / "index.md", "# Index\n")
    _write(tmp_path / "a.md", _make_source_md(body="A"))
    report = lint_vault(tmp_path, today=date(2026, 5, 5))
    assert any(p.name == "a.md" for p in report.index_sync_missing)


def test_index_sync_passes_when_listed(tmp_path: Path) -> None:
    _write(tmp_path / "index.md", "# Index\n- [[a]]\n")
    _write(tmp_path / "a.md", _make_source_md(body="A"))
    report = lint_vault(tmp_path, today=date(2026, 5, 5))
    assert all(p.name != "a.md" for p in report.index_sync_missing)


def test_excluded_dirs_not_orphan(tmp_path: Path) -> None:
    _write(tmp_path / "index.md", "# Index\n")
    _write(
        tmp_path / "90_meta" / "frontmatter-spec.md",
        "---\ntitle: spec\n---\nx\n",
    )
    report = lint_vault(tmp_path, today=date(2026, 5, 5))
    assert all("90_meta" not in str(p) for p in report.orphans)


def test_total_violations_counted(tmp_path: Path) -> None:
    _write(tmp_path / "index.md", "# Index\n")
    _write(tmp_path / "a.md", _make_source_md(confidence=0.2, body="link [[x]]"))
    report = lint_vault(tmp_path, today=date(2026, 5, 5))
    assert report.total_violations >= 2
