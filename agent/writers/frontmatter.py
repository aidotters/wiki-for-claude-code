"""frontmatter 読み書きユーティリティ。

YAML frontmatter のパース / シリアライズと、type 別必須キー欠損検出を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

COMMON_REQUIRED_KEYS = {
    "title",
    "type",
    "confidence",
    "sources",
    "last_updated",
    "stale",
    "tags",
    "reviewer",
    "human_edited",
    "status",
    "auto_section_managed",
}

SOURCE_REQUIRED_KEYS = {
    "source_url",
    "fetched_at",
    "claude_code_version",
}

VALID_TYPES = {"source", "concept", "entity", "comparison", "synthesis"}
VALID_STATUSES = {"draft", "reviewed", "published"}


@dataclass
class FrontmatterDocument:
    """frontmatter と本文の組。"""

    metadata: dict[str, Any]
    body: str


def parse(text: str) -> FrontmatterDocument:
    """文字列から frontmatter + 本文をパースする。

    frontmatter が無いファイルは metadata={} で返す。
    """
    if not text.startswith("---\n"):
        return FrontmatterDocument(metadata={}, body=text)

    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return FrontmatterDocument(metadata={}, body=text)

    raw_yaml = parts[1]
    body = parts[2]
    try:
        meta = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}") from e
    if not isinstance(meta, dict):
        raise ValueError("Frontmatter must be a YAML mapping")
    return FrontmatterDocument(metadata=meta, body=body)


def serialize(doc: FrontmatterDocument) -> str:
    """frontmatter + 本文を文字列化する。"""
    if not doc.metadata:
        return doc.body
    yaml_text = yaml.safe_dump(
        doc.metadata,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    body = doc.body
    if not body.startswith("\n"):
        body = "\n" + body
    return f"---\n{yaml_text}---{body}"


def read_file(path: Path) -> FrontmatterDocument:
    return parse(path.read_text(encoding="utf-8"))


def write_file(path: Path, doc: FrontmatterDocument) -> None:
    path.write_text(serialize(doc), encoding="utf-8")


def missing_keys(meta: dict[str, Any]) -> set[str]:
    """共通必須キー + type 別必須キーの欠損を集計する。"""
    missing = COMMON_REQUIRED_KEYS - set(meta.keys())
    if meta.get("type") == "source":
        missing |= SOURCE_REQUIRED_KEYS - set(meta.keys())
    return missing
