"""agent/writers/markdown_writer のテスト。"""

from __future__ import annotations

from pathlib import Path

from agent.writers.frontmatter import FrontmatterDocument
from agent.writers.markdown_writer import (
    compute_body_hash,
    compute_meaningful_hash,
    write,
)


def _doc(meta: dict[str, object], body: str) -> FrontmatterDocument:
    return FrontmatterDocument(metadata=dict(meta), body=body)


def test_write_creates_new_file(tmp_path: Path) -> None:
    target = tmp_path / "sub" / "new.md"
    doc = _doc({"title": "X", "type": "concept"}, "\n## Body\n")
    result = write(target, doc)
    assert target.exists()
    assert result.changed is True


def test_write_idempotent_on_meaningful_match(tmp_path: Path) -> None:
    target = tmp_path / "page.md"
    meta1 = {"title": "X", "type": "source", "fetched_at": "2026-05-05T10:00:00Z"}
    write(target, _doc(meta1, "\n## Same\n"))
    meta2 = {"title": "X", "type": "source", "fetched_at": "2026-06-01T10:00:00Z"}
    result = write(target, _doc(meta2, "\n## Same\n"))
    assert result.changed is False
    assert "no meaningful changes" in result.diff_summary


def test_write_changes_when_body_differs(tmp_path: Path) -> None:
    target = tmp_path / "page.md"
    meta = {"title": "X", "type": "concept"}
    write(target, _doc(meta, "\n## A\n"))
    result = write(target, _doc(meta, "\n## B\n"))
    assert result.changed is True


def test_compute_body_hash_normalizes_whitespace() -> None:
    assert compute_body_hash("hello\nworld") == compute_body_hash("hello\nworld\n\n")
    assert compute_body_hash("a   ") == compute_body_hash("a")


def test_meaningful_hash_ignores_timestamps() -> None:
    doc1 = _doc(
        {"title": "X", "fetched_at": "2026-05-05T10:00:00Z", "last_updated": "2026-05-05"},
        "body",
    )
    doc2 = _doc(
        {"title": "X", "fetched_at": "2026-06-01T10:00:00Z", "last_updated": "2026-06-01"},
        "body",
    )
    assert compute_meaningful_hash(doc1) == compute_meaningful_hash(doc2)


def test_meaningful_hash_changes_on_real_metadata_change() -> None:
    doc1 = _doc({"title": "X", "confidence": 0.9}, "body")
    doc2 = _doc({"title": "X", "confidence": 0.5}, "body")
    assert compute_meaningful_hash(doc1) != compute_meaningful_hash(doc2)
