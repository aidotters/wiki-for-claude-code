"""Markdown 制約バリデータ。

禁止記法（Dataview, Callout, Obsidian 埋め込み）の検出を行う。
"""

from __future__ import annotations

import re
from pathlib import Path

from agent.validators.frontmatter_validator import ValidationIssue

DATAVIEW_PATTERN = re.compile(r"^```dataview\b", re.MULTILINE)
CALLOUT_PATTERN = re.compile(r"^>\s*\[![A-Za-z]+\]", re.MULTILINE)
EMBED_PATTERN = re.compile(r"!\[\[[^\]]+\]\]")


def validate_text(text: str, file_path: Path | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if DATAVIEW_PATTERN.search(text):
        issues.append(
            ValidationIssue(file_path=file_path, field="markdown", message="Dataview ブロックは禁止")
        )
    if CALLOUT_PATTERN.search(text):
        issues.append(
            ValidationIssue(file_path=file_path, field="markdown", message="Callout 記法は禁止")
        )
    if EMBED_PATTERN.search(text):
        issues.append(
            ValidationIssue(
                file_path=file_path,
                field="markdown",
                message="Obsidian の `![[...]]` 埋め込み記法は禁止",
            )
        )
    return issues


def validate_file(path: Path) -> list[ValidationIssue]:
    return validate_text(path.read_text(encoding="utf-8"), file_path=path)
