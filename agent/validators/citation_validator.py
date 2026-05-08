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

DERIVED_TYPES = {"concept", "entity", "comparison", "synthesis", "recipe"}
WIKILINK_PATTERN = re.compile(r"\[\[([^\]\|]+?)(?:\|[^\]]*)?\]\]")
# recipe 種別の `sources` は `vault/sources/` 配下を指す wikilink を強制
RECIPE_SOURCE_PREFIX = "sources/"


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

    # recipe 種別は最低 2 件必須（ADR-016 / Phase 2-A）
    if type_value == "recipe" and isinstance(sources, list) and len(sources) < 2:
        issues.append(
            ValidationIssue(
                file_path=path,
                field="sources",
                message="recipe 種別は `sources` 最低 2 件必須（横断視点を担保）",
            )
        )

    # 引用先の実在確認（frontmatter `sources` のみ）
    if isinstance(sources, list):
        for s in sources:
            if not isinstance(s, str):
                continue
            m = WIKILINK_PATTERN.search(s)
            if not m:
                # recipe 種別は wikilink 形式必須
                if type_value == "recipe":
                    issues.append(
                        ValidationIssue(
                            file_path=path,
                            field="sources",
                            message=f"recipe の `sources` は wikilink 形式 [[...]] が必須: {s!r}",
                        )
                    )
                    continue
                link = s.strip()
            else:
                link = m.group(1)

            # recipe 種別は vault/sources/ 配下を指すこと
            if type_value == "recipe" and not link.lstrip("/").startswith(RECIPE_SOURCE_PREFIX):
                issues.append(
                    ValidationIssue(
                        file_path=path,
                        field="sources",
                        message=(
                            f"recipe の `sources` は `[[sources/...]]` を指す必要があります: {link}"
                        ),
                    )
                )

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
