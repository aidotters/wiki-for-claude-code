"""E2E スモーク: フェーズ12 受け入れ条件を機械的に確認する。

- agent validate --all が30秒以内
- 規約違反検出: 壊した frontmatter / 禁止記法 / 低信頼度
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from agent.errors import EXIT_LINT, EXIT_OK, EXIT_VALIDATION
from agent.runners.local import main

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_validate_all_under_30_seconds(capsys: pytest.CaptureFixture[str]) -> None:
    start = time.monotonic()
    code = main(["--vault-root", str(REPO_ROOT / "vault"), "validate", "--all"])
    elapsed = time.monotonic() - start
    capsys.readouterr()
    assert code == EXIT_OK
    assert elapsed < 30.0, f"validate took {elapsed:.2f}s, exceeds 30s budget"


def test_lint_all_under_30_seconds(capsys: pytest.CaptureFixture[str]) -> None:
    start = time.monotonic()
    main(["--vault-root", str(REPO_ROOT / "vault"), "lint", "--all"])
    elapsed = time.monotonic() - start
    capsys.readouterr()
    assert elapsed < 30.0


def test_broken_frontmatter_returns_exit_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # 30_drafts は除外されるため、sources/ に置く
    bad = tmp_path / "vault"
    (bad / "90_meta" / "_schemas").mkdir(parents=True)
    (bad / "sources" / "official" / "cli").mkdir(parents=True)
    import shutil

    shutil.copy(
        REPO_ROOT / "vault" / "90_meta" / "_schemas" / "frontmatter.schema.json",
        bad / "90_meta" / "_schemas" / "frontmatter.schema.json",
    )
    shutil.copy(
        REPO_ROOT / "vault" / "90_meta" / "sources.md",
        bad / "90_meta" / "sources.md",
    )

    # わざと frontmatter を壊した記事
    (bad / "sources" / "official" / "cli" / "broken.md").write_text(
        "---\ntitle: x\ntype: source\n---\n\nbody only, missing required keys\n",
        encoding="utf-8",
    )
    code = main(["--vault-root", str(bad), "validate", "--all"])
    capsys.readouterr()
    assert code == EXIT_VALIDATION


def test_dataview_block_caught_by_validate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "vault"
    (bad / "90_meta" / "_schemas").mkdir(parents=True)
    (bad / "sources" / "official" / "cli").mkdir(parents=True)
    import shutil

    shutil.copy(
        REPO_ROOT / "vault" / "90_meta" / "_schemas" / "frontmatter.schema.json",
        bad / "90_meta" / "_schemas" / "frontmatter.schema.json",
    )
    shutil.copy(
        REPO_ROOT / "vault" / "90_meta" / "sources.md",
        bad / "90_meta" / "sources.md",
    )

    target = bad / "sources" / "official" / "cli" / "with-dataview.md"
    target.write_text(
        "---\n"
        "title: x\n"
        "type: source\n"
        "confidence: 0.9\n"
        "sources: []\n"
        "last_updated: '2026-05-05'\n"
        "stale: false\n"
        "tags: [x]\n"
        "source_url: https://docs.claude.com/x\n"
        "fetched_at: '2026-05-05T10:00:00Z'\n"
        "claude_code_version: '1.5.0'\n"
        "reviewer: tak\n"
        "human_edited: true\n"
        "status: published\n"
        "auto_section_managed: false\n"
        "---\n"
        "\n## 概要 (要約)\nx\n\n"
        "## 公式ドキュメント\n→ https://docs.claude.com/x\n"
        "（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）\n\n"
        "## 補足解説 (日本語)\n"
        "```dataview\nLIST\n```\n",
        encoding="utf-8",
    )
    code = main(["--vault-root", str(bad), "validate", "--all"])
    capsys.readouterr()
    assert code == EXIT_VALIDATION


def test_low_confidence_caught_by_lint(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "vault"
    (bad / "90_meta" / "_schemas").mkdir(parents=True)
    (bad / "sources" / "official" / "cli").mkdir(parents=True)
    import shutil

    shutil.copy(
        REPO_ROOT / "vault" / "90_meta" / "_schemas" / "frontmatter.schema.json",
        bad / "90_meta" / "_schemas" / "frontmatter.schema.json",
    )
    shutil.copy(
        REPO_ROOT / "vault" / "90_meta" / "sources.md",
        bad / "90_meta" / "sources.md",
    )

    (bad / "index.md").write_text("# Index\n- [[low]]\n", encoding="utf-8")
    target = bad / "sources" / "official" / "cli" / "low.md"
    target.write_text(
        "---\n"
        "title: low\n"
        "type: source\n"
        "confidence: 0.3\n"
        "sources: []\n"
        "last_updated: '2026-05-05'\n"
        "stale: false\n"
        "tags: [x]\n"
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
    code = main(["--vault-root", str(bad), "lint", "--all"])
    capsys.readouterr()
    assert code == EXIT_LINT
