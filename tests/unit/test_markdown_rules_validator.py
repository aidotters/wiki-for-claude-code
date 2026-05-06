"""agent/validators/markdown_rules_validator のテスト。"""

from __future__ import annotations

from agent.validators.markdown_rules_validator import validate_text


def test_clean_markdown_passes() -> None:
    text = "# Title\n\n- item\n- [[link]]\n"
    assert validate_text(text) == []


def test_dataview_block_detected() -> None:
    text = "# T\n\n```dataview\nLIST FROM #foo\n```\n"
    issues = validate_text(text)
    assert any("Dataview" in i.message for i in issues)


def test_callout_detected() -> None:
    text = "# T\n\n> [!note]\n> body\n"
    issues = validate_text(text)
    assert any("Callout" in i.message for i in issues)


def test_obsidian_embed_detected() -> None:
    text = "# T\n\n![[some-image]]\n"
    issues = validate_text(text)
    assert any("埋め込み" in i.message for i in issues)


def test_multiple_violations_collected() -> None:
    text = "```dataview\nx\n```\n> [!warning]\n![[image]]\n"
    issues = validate_text(text)
    assert len(issues) == 3


def test_normal_wikilink_not_detected_as_embed() -> None:
    text = "[[link]]"
    assert validate_text(text) == []
