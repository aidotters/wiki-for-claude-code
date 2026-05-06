"""source 種別の3部構成バリデータ。

「## 概要 (要約)」「## 公式ドキュメント」「## 補足解説 (日本語)」が
この順序で存在することを検証する（type=source のみ対象）。
"""

from __future__ import annotations

import re
from pathlib import Path

from agent.validators.frontmatter_validator import ValidationIssue
from agent.writers.frontmatter import parse

REQUIRED_HEADINGS = [
    "## 概要 (要約)",
    "## 公式ドキュメント",
    "## 補足解説 (日本語)",
]

OFFICIAL_LINK_PATTERN = re.compile(r"^→\s+https?://", re.MULTILINE)
LAST_CHECKED_PATTERN = re.compile(r"最終確認:\s*(\d{4}-\d{2}-\d{2})")
TARGET_VERSION_PATTERN = re.compile(r"対象バージョン:\s*(\d+\.\d+\.\d+)")


def validate_body(
    body: str,
    file_path: Path | None = None,
) -> list[ValidationIssue]:
    """source 種別の本文を検証する。"""
    issues: list[ValidationIssue] = []
    last_index = -1
    for heading in REQUIRED_HEADINGS:
        idx = body.find(heading)
        if idx == -1:
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    field="three_part",
                    message=f"3部構成の見出しが欠落: {heading!r}",
                )
            )
        elif idx <= last_index:
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    field="three_part",
                    message=f"3部構成の見出し順序が不正: {heading!r}",
                )
            )
        else:
            last_index = idx

    # 「## 公式ドキュメント」セクションのフォーマット
    official_idx = body.find("## 公式ドキュメント")
    if official_idx >= 0:
        # 次の見出しまでをセクションとして扱う
        next_idx = body.find("\n## ", official_idx + 1)
        section = body[official_idx:next_idx] if next_idx >= 0 else body[official_idx:]
        if not OFFICIAL_LINK_PATTERN.search(section):
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    field="official_doc",
                    message="公式ドキュメントセクションに `→ {URL}` 行がありません",
                )
            )
        if not LAST_CHECKED_PATTERN.search(section):
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    field="official_doc",
                    message="公式ドキュメントセクションに `最終確認: YYYY-MM-DD` がありません",
                )
            )
        if not TARGET_VERSION_PATTERN.search(section):
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    field="official_doc",
                    message="公式ドキュメントセクションに `対象バージョン: X.Y.Z` がありません",
                )
            )

    return issues


def validate_file(path: Path) -> list[ValidationIssue]:
    """ファイルが type=source の場合のみ3部構成を検証する。"""
    doc = parse(path.read_text(encoding="utf-8"))
    if doc.metadata.get("type") != "source":
        return []
    return validate_body(doc.body, file_path=path)
