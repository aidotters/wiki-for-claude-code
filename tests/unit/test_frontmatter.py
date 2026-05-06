"""agent/writers/frontmatter のテスト。"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.writers.frontmatter import (
    FrontmatterDocument,
    missing_keys,
    parse,
    read_file,
    serialize,
    write_file,
)


class TestParseSerialize:
    def test_parse_with_frontmatter(self) -> None:
        text = (
            "---\n"
            "title: Test\n"
            "type: source\n"
            "---\n"
            "\n## Body\n"
        )
        doc = parse(text)
        assert doc.metadata == {"title": "Test", "type": "source"}
        assert "## Body" in doc.body

    def test_parse_without_frontmatter(self) -> None:
        text = "## Just body"
        doc = parse(text)
        assert doc.metadata == {}
        assert doc.body == text

    def test_serialize_roundtrip(self) -> None:
        meta = {"title": "Test", "type": "source", "tags": ["a", "b"]}
        doc = FrontmatterDocument(metadata=meta, body="\n## Body\nHello\n")
        serialized = serialize(doc)
        assert serialized.startswith("---\n")
        reparsed = parse(serialized)
        assert reparsed.metadata == meta
        assert "## Body" in reparsed.body

    def test_serialize_empty_metadata(self) -> None:
        doc = FrontmatterDocument(metadata={}, body="just body")
        assert serialize(doc) == "just body"

    def test_invalid_yaml_raises(self) -> None:
        text = "---\ntitle: : :\n---\n"
        with pytest.raises(ValueError):
            parse(text)


class TestFileIO:
    def test_read_write_roundtrip(self, tmp_path: Path) -> None:
        meta = {"title": "Test", "type": "concept"}
        doc = FrontmatterDocument(metadata=meta, body="\n## Hello\n")
        target = tmp_path / "test.md"
        write_file(target, doc)
        loaded = read_file(target)
        assert loaded.metadata == meta
        assert "## Hello" in loaded.body


class TestMissingKeys:
    def test_complete_source_no_missing(self, sample_source_metadata: dict[str, object]) -> None:
        assert missing_keys(sample_source_metadata) == set()

    def test_source_missing_source_url(self, sample_source_metadata: dict[str, object]) -> None:
        del sample_source_metadata["source_url"]
        assert "source_url" in missing_keys(sample_source_metadata)

    def test_concept_does_not_require_source_keys(self) -> None:
        meta = {
            "title": "Concept",
            "type": "concept",
            "confidence": 0.8,
            "sources": ["[[foo]]"],
            "last_updated": "2026-05-05",
            "stale": False,
            "tags": ["x"],
            "reviewer": "tak",
            "human_edited": True,
            "status": "published",
            "auto_section_managed": False,
        }
        assert missing_keys(meta) == set()

    def test_missing_common_key(self) -> None:
        meta = {"type": "source"}
        m = missing_keys(meta)
        assert "title" in m
        assert "confidence" in m
        assert "source_url" in m  # source 種別なので追加要件
