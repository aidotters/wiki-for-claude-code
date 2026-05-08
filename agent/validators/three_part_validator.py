"""source 種別の縮退仕様バリデータ（ADR-017 / Phase 2-A）。

「## 概要 (要約)」「## 公式ドキュメント」がこの順序で存在することを検証する。
旧 ADR-003 の「## 補足解説 (日本語)」は ADR-017 で撤廃された（type=source のみ対象）。

`auto_section_managed: true` のファイルは「## 概要 (要約)」配下に AUTO 領域 1 件以上を要求する。
"""

from __future__ import annotations

import re
from pathlib import Path

from agent.validators.frontmatter_validator import ValidationIssue
from agent.writers.frontmatter import parse
from agent.writers.markdown_writer import AUTO_END_MARKER

# `<!-- AUTO:START -->` または `<!-- AUTO:START purpose=... -->` の両方を検出する。
# 詳細は agent/writers/markdown_writer.py の `_AUTO_START_RE` と整合（ADR-019）。
_AUTO_START_PATTERN = re.compile(r"<!-- AUTO:START(?:\s+purpose=[a-z0-9-]+)?\s*-->")

REQUIRED_HEADINGS = [
    "## 概要 (要約)",
    "## 公式ドキュメント",
]

OFFICIAL_LINK_PATTERN = re.compile(r"^→\s+https?://", re.MULTILINE)
LAST_CHECKED_PATTERN = re.compile(r"最終確認:\s*(\d{4}-\d{2}-\d{2})")
TARGET_VERSION_PATTERN = re.compile(r"対象バージョン:\s*(\d+\.\d+\.\d+)")


def validate_body(
    body: str,
    file_path: Path | None = None,
    *,
    auto_section_managed: bool = False,
) -> list[ValidationIssue]:
    """source 種別の本文を縮退仕様（ADR-017）で検証する。

    `auto_section_managed=True` の場合は「## 概要 (要約)」配下に AUTO 領域 1 件以上を要求する。
    """
    issues: list[ValidationIssue] = []
    last_index = -1
    for heading in REQUIRED_HEADINGS:
        idx = body.find(heading)
        if idx == -1:
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    field="shrunk_spec",
                    message=f"縮退仕様の見出しが欠落: {heading!r}",
                )
            )
        elif idx <= last_index:
            issues.append(
                ValidationIssue(
                    file_path=file_path,
                    field="shrunk_spec",
                    message=f"縮退仕様の見出し順序が不正: {heading!r}",
                )
            )
        else:
            last_index = idx

    # AUTO 領域の存在確認（auto_section_managed: true のみ）
    if auto_section_managed:
        summary_idx = body.find("## 概要 (要約)")
        official_idx = body.find("## 公式ドキュメント")
        if summary_idx >= 0:
            section_end = official_idx if official_idx > summary_idx else len(body)
            summary_section = body[summary_idx:section_end]
            if (
                _AUTO_START_PATTERN.search(summary_section) is None
                or AUTO_END_MARKER not in summary_section
            ):
                issues.append(
                    ValidationIssue(
                        file_path=file_path,
                        field="auto_section",
                        message=(
                            "auto_section_managed=true のファイルは "
                            "`## 概要 (要約)` 配下に AUTO 領域が必要"
                        ),
                    )
                )

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
    """ファイルが type=source の場合のみ縮退仕様を検証する。"""
    doc = parse(path.read_text(encoding="utf-8"))
    if doc.metadata.get("type") != "source":
        return []
    return validate_body(
        doc.body,
        file_path=path,
        auto_section_managed=bool(doc.metadata.get("auto_section_managed", False)),
    )
