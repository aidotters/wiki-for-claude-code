"""agent/validators/frontmatter_validator のテスト。"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.validators.frontmatter_validator import (
    load_schema,
    validate_metadata,
)


@pytest.fixture
def validator(schema_path: Path):
    return load_schema(schema_path)


def test_complete_source_passes(validator, sample_source_metadata):
    issues = validate_metadata(sample_source_metadata, validator)
    assert issues == []


def test_missing_common_key_fails(validator, sample_source_metadata):
    del sample_source_metadata["title"]
    issues = validate_metadata(sample_source_metadata, validator)
    assert any("title" in i.message for i in issues)


def test_missing_source_url_fails_for_source_type(validator, sample_source_metadata):
    del sample_source_metadata["source_url"]
    issues = validate_metadata(sample_source_metadata, validator)
    assert any("source_url" in i.message for i in issues)


def test_invalid_status_enum_fails(validator, sample_source_metadata):
    sample_source_metadata["status"] = "rejected"
    issues = validate_metadata(sample_source_metadata, validator)
    assert any("status" in str(i) or "enum" in i.message for i in issues)


def test_invalid_type_enum_fails(validator, sample_source_metadata):
    sample_source_metadata["type"] = "tutorial"
    issues = validate_metadata(sample_source_metadata, validator)
    assert any(i.field in ("type", "<root>") or "tutorial" in i.message or "enum" in i.message for i in issues)


def test_confidence_out_of_range_fails(validator, sample_source_metadata):
    sample_source_metadata["confidence"] = 1.5
    issues = validate_metadata(sample_source_metadata, validator)
    assert issues, "confidence > 1.0 should fail"


def test_concept_without_source_url_passes(validator):
    meta = {
        "title": "C",
        "type": "concept",
        "confidence": 0.8,
        "sources": ["[[x]]"],
        "last_updated": "2026-05-05",
        "stale": False,
        "tags": ["x"],
        "reviewer": "tak",
        "human_edited": True,
        "status": "published",
        "auto_section_managed": False,
    }
    issues = validate_metadata(meta, validator)
    assert issues == []


def test_invalid_semver_fails(validator, sample_source_metadata):
    sample_source_metadata["claude_code_version"] = "v1.5"
    issues = validate_metadata(sample_source_metadata, validator)
    assert issues
