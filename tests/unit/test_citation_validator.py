"""agent/validators/citation_validator のテスト。"""

from __future__ import annotations

from pathlib import Path

from agent.validators.citation_validator import validate_file


def test_source_type_skipped(tmp_path: Path) -> None:
    target = tmp_path / "s.md"
    target.write_text("---\ntitle: s\ntype: source\nsources: []\n---\nbody\n", encoding="utf-8")
    assert validate_file(target, vault_root=tmp_path) == []


def test_concept_with_empty_sources_fails(tmp_path: Path) -> None:
    target = tmp_path / "c.md"
    target.write_text("---\ntitle: c\ntype: concept\nsources: []\n---\nbody\n", encoding="utf-8")
    issues = validate_file(target, vault_root=tmp_path)
    assert issues, "empty sources should fail for concept"


def test_concept_with_existing_source_passes(tmp_path: Path) -> None:
    (tmp_path / "ref").mkdir()
    (tmp_path / "ref" / "x.md").write_text("body", encoding="utf-8")
    target = tmp_path / "c.md"
    target.write_text(
        "---\ntitle: c\ntype: concept\nsources: ['[[ref/x]]']\n---\nbody\n",
        encoding="utf-8",
    )
    assert validate_file(target, vault_root=tmp_path) == []


def test_concept_with_missing_source_fails(tmp_path: Path) -> None:
    target = tmp_path / "c.md"
    target.write_text(
        "---\ntitle: c\ntype: concept\nsources: ['[[ref/missing]]']\n---\nbody\n",
        encoding="utf-8",
    )
    issues = validate_file(target, vault_root=tmp_path)
    assert any("存在しません" in i.message for i in issues)
