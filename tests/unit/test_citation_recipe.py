"""recipe 種別の citation_validator テスト（Phase 2-A）。"""

from __future__ import annotations

from pathlib import Path

from agent.validators.citation_validator import validate_file


def _setup_vault(vault_root: Path) -> None:
    """`vault/sources/official/cli/` 配下に dummy source を 2 本配置。"""
    src_dir = vault_root / "sources" / "official" / "cli"
    src_dir.mkdir(parents=True)
    (src_dir / "installation.md").write_text("body", encoding="utf-8")
    (src_dir / "configuration.md").write_text("body", encoding="utf-8")


def test_recipe_with_two_sources_passes(tmp_path: Path) -> None:
    _setup_vault(tmp_path)
    target = tmp_path / "recipes" / "setup.md"
    target.parent.mkdir()
    target.write_text(
        "---\n"
        "title: setup\n"
        "type: recipe\n"
        "use_case: foo\n"
        "sources:\n"
        "  - '[[sources/official/cli/installation]]'\n"
        "  - '[[sources/official/cli/configuration]]'\n"
        "---\n"
        "body\n",
        encoding="utf-8",
    )
    assert validate_file(target, vault_root=tmp_path) == []


def test_recipe_with_one_source_fails(tmp_path: Path) -> None:
    _setup_vault(tmp_path)
    target = tmp_path / "r.md"
    target.write_text(
        "---\n"
        "title: r\n"
        "type: recipe\n"
        "use_case: foo\n"
        "sources:\n"
        "  - '[[sources/official/cli/installation]]'\n"
        "---\n"
        "body\n",
        encoding="utf-8",
    )
    issues = validate_file(target, vault_root=tmp_path)
    assert any("最低 2 件" in i.message for i in issues)


def test_recipe_non_wikilink_source_fails(tmp_path: Path) -> None:
    _setup_vault(tmp_path)
    target = tmp_path / "r.md"
    target.write_text(
        "---\n"
        "title: r\n"
        "type: recipe\n"
        "use_case: foo\n"
        "sources:\n"
        "  - 'plain string'\n"
        "  - '[[sources/official/cli/configuration]]'\n"
        "---\n"
        "body\n",
        encoding="utf-8",
    )
    issues = validate_file(target, vault_root=tmp_path)
    assert any("wikilink 形式" in i.message for i in issues)


def test_recipe_non_sources_path_fails(tmp_path: Path) -> None:
    _setup_vault(tmp_path)
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "foo.md").write_text("body", encoding="utf-8")
    target = tmp_path / "r.md"
    target.write_text(
        "---\n"
        "title: r\n"
        "type: recipe\n"
        "use_case: foo\n"
        "sources:\n"
        "  - '[[concepts/foo]]'\n"
        "  - '[[sources/official/cli/configuration]]'\n"
        "---\n"
        "body\n",
        encoding="utf-8",
    )
    issues = validate_file(target, vault_root=tmp_path)
    assert any("`[[sources/...]]`" in i.message for i in issues)


def test_recipe_with_missing_source_fails(tmp_path: Path) -> None:
    _setup_vault(tmp_path)
    target = tmp_path / "r.md"
    target.write_text(
        "---\n"
        "title: r\n"
        "type: recipe\n"
        "use_case: foo\n"
        "sources:\n"
        "  - '[[sources/official/cli/installation]]'\n"
        "  - '[[sources/official/cli/missing]]'\n"
        "---\n"
        "body\n",
        encoding="utf-8",
    )
    issues = validate_file(target, vault_root=tmp_path)
    assert any("存在しません" in i.message for i in issues)
