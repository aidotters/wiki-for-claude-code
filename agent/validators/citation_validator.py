"""派生種別（concept/entity/comparison/synthesis）の引用必須バリダ。

Phase 1 では type=source 中心のため最小実装。
- 派生種別の `sources` frontmatter キーが空でない
- 引用ターゲット wikilink が実在ファイルを指している
"""

from __future__ import annotations

import re
from pathlib import Path

from agent.validators.frontmatter_validator import ValidationIssue
from agent.writers.frontmatter import parse

DERIVED_TYPES = {"concept", "entity", "comparison", "synthesis"}
WIKILINK_PATTERN = re.compile(r"\[\[([^\]\|]+?)(?:\|[^\]]*)?\]\]")


def _wikilink_to_path(vault_root: Path, wikilink: str) -> Path:
    """`[[a/b/c]]` → `vault_root/a/b/c.md`."""
    return vault_root / f"{wikilink.strip()}.md"


def validate_file(path: Path, vault_root: Path) -> list[ValidationIssue]:
    doc = parse(path.read_text(encoding="utf-8"))
    type_value = doc.metadata.get("type")
    if type_value not in DERIVED_TYPES:
        return []

    issues: list[ValidationIssue] = []
    sources = doc.metadata.get("sources", [])
    if not isinstance(sources, list) or not sources:
        issues.append(
            ValidationIssue(
                file_path=path,
                field="sources",
                message="派生種別は `sources` frontmatter に最低1件の引用が必要",
            )
        )

    # 引用先の実在確認（frontmatter `sources` のみ）
    if isinstance(sources, list):
        for s in sources:
            if not isinstance(s, str):
                continue
            m = WIKILINK_PATTERN.search(s)
            link = m.group(1) if m else s.strip()
            target = _wikilink_to_path(vault_root, link)
            if not target.exists():
                issues.append(
                    ValidationIssue(
                        file_path=path,
                        field="sources",
                        message=f"引用先が存在しません: {link}",
                    )
                )
    return issues
