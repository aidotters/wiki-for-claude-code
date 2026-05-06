"""validate_all / validate_target ユースケース（CI 向け機械検証）。

transclusion_validator（連続100文字一致検出）は raw コンテンツが必要なため、
optional な ``raw_content`` / ``raw_content_map`` を受け取れる形で組み込む。
未指定時はスキップし、ネットワーク非依存で CI から呼べる挙動を維持する。
取得を伴う検証は ``agent verify-links`` サブコマンドが担う。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from agent.validators import (
    citation_validator,
    markdown_rules_validator,
    three_part_validator,
    transclusion_validator,
)
from agent.validators.frontmatter_validator import (
    ValidationIssue,
    load_schema,
)
from agent.validators.frontmatter_validator import (
    validate_file as validate_fm_file,
)
from agent.writers.frontmatter import parse as parse_frontmatter


@dataclass
class ValidationSummary:
    issues: list[ValidationIssue] = field(default_factory=list)
    files_checked: int = 0

    @property
    def passed(self) -> bool:
        return not self.issues

    def format(self) -> str:
        lines = [f"Validated {self.files_checked} files"]
        for issue in self.issues:
            lines.append(str(issue))
        if self.passed:
            lines.append("All checks PASSED")
        else:
            lines.append(f"FAILED with {len(self.issues)} issues")
        return "\n".join(lines)


VAULT_EXCLUDE_DIRS = {"30_drafts"}


def _list_target_files(vault_root: Path) -> list[Path]:
    files: list[Path] = []
    for p in vault_root.rglob("*.md"):
        rel = p.relative_to(vault_root)
        if rel.parts[0] in VAULT_EXCLUDE_DIRS:
            continue
        files.append(p)
    return files


def _run_transclusion(target: Path, raw_content: str | None) -> list[ValidationIssue]:
    if raw_content is None:
        return []
    doc = parse_frontmatter(target.read_text(encoding="utf-8"))
    if doc.metadata.get("type") != "source":
        return []
    return transclusion_validator.validate(doc.body, raw_content, file_path=target)


def validate_target(
    target: Path,
    vault_root: Path,
    raw_content: str | None = None,
) -> ValidationSummary:
    """単一ファイル検証（CI 用）。

    ``raw_content`` を渡した場合、source 種別記事に対して transclusion 検査も実行する。
    """
    schema_path = vault_root / "90_meta" / "_schemas" / "frontmatter.schema.json"
    schema = load_schema(schema_path)
    summary = ValidationSummary(files_checked=1)
    summary.issues.extend(validate_fm_file(target, schema))
    summary.issues.extend(markdown_rules_validator.validate_file(target))
    summary.issues.extend(three_part_validator.validate_file(target))
    summary.issues.extend(citation_validator.validate_file(target, vault_root=vault_root))
    summary.issues.extend(_run_transclusion(target, raw_content))
    return summary


def validate_all(
    vault_root: Path,
    raw_content_map: dict[Path, str] | None = None,
) -> ValidationSummary:
    """vault 配下全ページの検証（CI 用、機械的検証のみ）。

    ``raw_content_map`` を渡した場合、対応する source 種別記事に対して transclusion 検査も実行する。
    map に含まれない記事は transclusion 検査をスキップする（ネットワーク非依存維持）。
    """
    schema_path = vault_root / "90_meta" / "_schemas" / "frontmatter.schema.json"
    schema = load_schema(schema_path)
    summary = ValidationSummary()
    nav_files = {
        vault_root / "index.md",
        vault_root / "log.md",
        vault_root / "overview.md",
    }
    for f in _list_target_files(vault_root):
        if f in nav_files:
            continue
        if f.parts[-2] == "_schemas":
            continue
        if f.parent.name == "90_meta":
            # 90_meta の規約ドキュメントは frontmatter を持たないため除外
            continue
        summary.files_checked += 1
        summary.issues.extend(validate_fm_file(f, schema))
        summary.issues.extend(markdown_rules_validator.validate_file(f))
        summary.issues.extend(three_part_validator.validate_file(f))
        summary.issues.extend(citation_validator.validate_file(f, vault_root=vault_root))
        if raw_content_map is not None and f in raw_content_map:
            summary.issues.extend(_run_transclusion(f, raw_content_map[f]))
    return summary
