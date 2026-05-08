"""recipe 種別の frontmatter_validator テスト（Phase 2-A）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.validators.frontmatter_validator import load_schema, validate_metadata


@pytest.fixture
def validator(schema_path: Path):
    return load_schema(schema_path)


@pytest.fixture
def sample_recipe_metadata() -> dict[str, object]:
    return {
        "title": "Setup Recipe",
        "type": "recipe",
        "use_case": "新規プロジェクトに Claude Code を導入する",
        "confidence": 0.7,
        "sources": [
            "[[sources/official/cli/installation]]",
            "[[sources/official/cli/configuration]]",
        ],
        "last_updated": "2026-05-06",
        "stale": False,
        "tags": ["recipe", "setup"],
        "reviewer": "tak",
        "human_edited": True,
        "status": "draft",
        "auto_section_managed": True,
    }


def test_complete_recipe_passes(validator, sample_recipe_metadata):
    issues = validate_metadata(sample_recipe_metadata, validator)
    assert issues == []


def test_recipe_missing_use_case_fails(validator, sample_recipe_metadata):
    del sample_recipe_metadata["use_case"]
    issues = validate_metadata(sample_recipe_metadata, validator)
    assert any("use_case" in i.message for i in issues)


def test_recipe_with_one_source_fails(validator, sample_recipe_metadata):
    sample_recipe_metadata["sources"] = ["[[sources/official/cli/installation]]"]
    issues = validate_metadata(sample_recipe_metadata, validator)
    assert any("too short" in i.message.lower() or "minitems" in i.message.lower() for i in issues)


def test_recipe_with_empty_use_case_fails(validator, sample_recipe_metadata):
    sample_recipe_metadata["use_case"] = ""
    issues = validate_metadata(sample_recipe_metadata, validator)
    assert any("use_case" in i.field or "minLength" in i.message.lower() for i in issues)
