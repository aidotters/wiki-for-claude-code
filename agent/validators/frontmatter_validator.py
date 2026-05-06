"""frontmatter 規約バリデータ。

JSON Schema (`vault/90_meta/_schemas/frontmatter.schema.json`) を参照して
type 別の必須キー・型・enum を検証する。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema import ValidationError as JsonSchemaError

from agent.writers.frontmatter import FrontmatterDocument, parse


def _normalize(value: Any) -> Any:
    """YAML がパースした date/datetime を ISO 文字列に正規化する。

    Schema は文字列 + pattern で日付形式を検証するため、Python オブジェクトを
    そのまま渡すと型不一致でエラーになる。
    """
    if isinstance(value, datetime):
        # ISO 8601、UTC は `Z` 表記に揃える
        if value.tzinfo is None:
            return value.strftime("%Y-%m-%dT%H:%M:%SZ")
        return value.strftime("%Y-%m-%dT%H:%M:%S%z").replace("+0000", "Z")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


@dataclass
class ValidationIssue:
    file_path: Path | None
    field: str
    message: str

    def __str__(self) -> str:
        loc = str(self.file_path) if self.file_path else "<inline>"
        field = f".{self.field}" if self.field else ""
        return f"{loc}{field}: {self.message}"


def load_schema(schema_path: Path) -> Draft202012Validator:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_metadata(
    meta: dict[str, Any],
    validator: Draft202012Validator,
    file_path: Path | None = None,
) -> list[ValidationIssue]:
    """metadata の dict を JSON Schema で検証する。"""
    issues: list[ValidationIssue] = []
    normalized = _normalize(meta)
    for err in sorted(validator.iter_errors(normalized), key=lambda e: list(e.absolute_path)):
        field = ".".join(str(p) for p in err.absolute_path) or "<root>"
        issues.append(
            ValidationIssue(file_path=file_path, field=field, message=err.message)
        )
    return issues


def validate_file(
    path: Path,
    validator: Draft202012Validator,
) -> list[ValidationIssue]:
    """ファイルから frontmatter を読み出して検証する。"""
    try:
        doc = parse(path.read_text(encoding="utf-8"))
    except ValueError as e:
        return [ValidationIssue(file_path=path, field="<frontmatter>", message=str(e))]
    if not doc.metadata:
        return [
            ValidationIssue(
                file_path=path, field="<frontmatter>", message="missing frontmatter"
            )
        ]
    return validate_metadata(doc.metadata, validator, file_path=path)


def validate_document(
    doc: FrontmatterDocument,
    validator: Draft202012Validator,
) -> list[ValidationIssue]:
    return validate_metadata(doc.metadata, validator)


__all__ = [
    "JsonSchemaError",
    "ValidationIssue",
    "load_schema",
    "validate_document",
    "validate_file",
    "validate_metadata",
]
