"""agent/validators/three_part_validator のテスト。"""

from __future__ import annotations

from pathlib import Path

from agent.validators.three_part_validator import validate_body, validate_file


def test_valid_three_part_passes() -> None:
    body = (
        "\n## 概要 (要約)\n要約\n\n"
        "## 公式ドキュメント\n→ https://docs.claude.com/x\n"
        "（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）\n\n"
        "## 補足解説 (日本語)\n補足\n"
    )
    assert validate_body(body) == []


def test_missing_summary_fails() -> None:
    body = (
        "\n## 公式ドキュメント\n→ https://docs.claude.com/x\n"
        "（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）\n\n"
        "## 補足解説 (日本語)\n補足\n"
    )
    issues = validate_body(body)
    assert any("概要" in i.message for i in issues)


def test_missing_official_doc_fails() -> None:
    body = "\n## 概要 (要約)\nx\n\n## 補足解説 (日本語)\ny\n"
    issues = validate_body(body)
    assert any("公式ドキュメント" in i.message for i in issues)


def test_missing_supplement_fails() -> None:
    body = (
        "\n## 概要 (要約)\nx\n\n"
        "## 公式ドキュメント\n→ https://docs.claude.com/x\n"
        "（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）\n"
    )
    issues = validate_body(body)
    assert any("補足解説" in i.message for i in issues)


def test_official_link_format_missing_url() -> None:
    body = (
        "\n## 概要 (要約)\nx\n\n"
        "## 公式ドキュメント\n（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）\n\n"
        "## 補足解説 (日本語)\ny\n"
    )
    issues = validate_body(body)
    assert any("→" in i.message or "URL" in i.message for i in issues)


def test_official_doc_missing_last_checked() -> None:
    body = (
        "\n## 概要 (要約)\nx\n\n"
        "## 公式ドキュメント\n→ https://docs.claude.com/x\n（対象バージョン: 1.5.0）\n\n"
        "## 補足解説 (日本語)\ny\n"
    )
    issues = validate_body(body)
    assert any("最終確認" in i.message for i in issues)


def test_official_doc_missing_target_version() -> None:
    body = (
        "\n## 概要 (要約)\nx\n\n"
        "## 公式ドキュメント\n→ https://docs.claude.com/x\n（最終確認: 2026-05-05）\n\n"
        "## 補足解説 (日本語)\ny\n"
    )
    issues = validate_body(body)
    assert any("対象バージョン" in i.message for i in issues)


def test_concept_file_skipped(tmp_path: Path) -> None:
    target = tmp_path / "c.md"
    target.write_text(
        "---\ntitle: c\ntype: concept\n---\n\n## 任意の構成\n本文\n",
        encoding="utf-8",
    )
    assert validate_file(target) == []


def test_source_file_with_full_three_part(tmp_path: Path) -> None:
    target = tmp_path / "s.md"
    target.write_text(
        "---\ntitle: s\ntype: source\n---\n"
        "\n## 概要 (要約)\nx\n\n"
        "## 公式ドキュメント\n→ https://docs.claude.com/x\n"
        "（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）\n\n"
        "## 補足解説 (日本語)\ny\n",
        encoding="utf-8",
    )
    assert validate_file(target) == []
