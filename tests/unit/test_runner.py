"""agent/runners/local CLI のユニットテスト。"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from agent.errors import EXIT_LINT, EXIT_OK, EXIT_VALIDATION
from agent.runners.local import _build_parser, main


def test_parser_recognizes_subcommands() -> None:
    parser = _build_parser()
    args = parser.parse_args(
        ["ingest", "--source-url", "https://x", "--category", "hooks"]
    )
    assert args.command == "ingest"
    assert args.category == "hooks"


def test_parser_rejects_invalid_category() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["ingest", "--source-url", "https://x", "--category", "tutorials"]
        )


def test_action_stub_raises() -> None:
    from agent.runners.action import main as action_main

    with pytest.raises(NotImplementedError):
        action_main()


def _make_vault(tmp_path: Path, repo_root: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
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


def test_validate_all_returns_zero_on_empty_vault(
    tmp_path: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = _make_vault(tmp_path, repo_root)
    code = main(["--vault-root", str(vault), "validate", "--all"])
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert "Validated 0 files" in out


def test_lint_all_returns_zero_on_empty_vault(
    tmp_path: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = _make_vault(tmp_path, repo_root)
    code = main(["--vault-root", str(vault), "lint", "--all"])
    assert code == EXIT_OK


def test_lint_returns_4_when_violations(
    tmp_path: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = _make_vault(tmp_path, repo_root)
    # 低 confidence で違反を作る
    bad = vault / "sources" / "official" / "cli" / "bad.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        "---\n"
        "title: bad\n"
        "type: source\n"
        "confidence: 0.3\n"
        "sources: []\n"
        "last_updated: 2026-05-05\n"
        "stale: false\n"
        "tags: [bad]\n"
        "source_url: https://docs.claude.com/x\n"
        "fetched_at: '2026-05-05T10:00:00Z'\n"
        "claude_code_version: '1.5.0'\n"
        "reviewer: tak\n"
        "human_edited: true\n"
        "status: published\n"
        "auto_section_managed: false\n"
        "---\n\nbody\n",
        encoding="utf-8",
    )
    code = main(["--vault-root", str(vault), "lint", "--all"])
    assert code == EXIT_LINT


def test_validate_returns_1_on_violation(
    tmp_path: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = _make_vault(tmp_path, repo_root)
    bad = vault / "sources" / "official" / "cli" / "no-fm.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("just body, no frontmatter\n", encoding="utf-8")
    code = main(["--vault-root", str(vault), "validate", "--all"])
    assert code == EXIT_VALIDATION
