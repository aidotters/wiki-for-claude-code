"""agent/prompts/loader のテスト。"""

from __future__ import annotations

import pytest

from agent.prompts.loader import load_prompt, render_prompt


def test_load_prompt_existing() -> None:
    text = load_prompt("source-ingest")
    assert "type: source" in text
    assert "{{source_url}}" in text


def test_load_prompt_missing_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent")


def test_render_substitutes_variables() -> None:
    template = "URL: {{source_url}}, today: {{today}}"
    result = render_prompt(template, {"source_url": "https://x.example", "today": "2026-05-05"})
    assert result == "URL: https://x.example, today: 2026-05-05"


def test_render_undefined_variables_left_blank() -> None:
    template = "Hello {{name}}"
    result = render_prompt(template, {})
    assert result == "Hello "


def test_render_preserves_unrelated_braces() -> None:
    template = "{{name}} {literal}"
    result = render_prompt(template, {"name": "X"})
    assert result == "X {literal}"
