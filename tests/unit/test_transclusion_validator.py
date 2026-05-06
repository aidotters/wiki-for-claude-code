"""agent/validators/transclusion_validator のテスト。"""

from __future__ import annotations

from agent.validators.transclusion_validator import find_long_match, validate


def test_no_match() -> None:
    assert find_long_match("これは要約。", "raw original content totally different") is None


def test_match_detected() -> None:
    common = "x" * 120
    article = f"intro {common} outro"
    raw = f"prefix {common} suffix"
    info = find_long_match(article, raw, window=100)
    assert info is not None
    assert len(info.matched_text) == 100


def test_short_inputs() -> None:
    assert find_long_match("short", "also short", window=100) is None


def test_validate_returns_no_issue_when_distinct() -> None:
    article = "completely different text" * 5
    raw = "another text entirely" * 10
    assert validate(article, raw) == []


def test_validate_returns_issue_on_match() -> None:
    common = "あ" * 120
    issues = validate(f"start {common} end", f"raw {common} raw")
    assert len(issues) == 1
    assert "100 文字" in issues[0].message
