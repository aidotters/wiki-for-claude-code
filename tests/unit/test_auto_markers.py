"""AUTO マーカー処理のユニットテスト（Phase 2-A / ADR-015）。

仕様:
- `<!-- AUTO:START -->` と `<!-- AUTO:END -->` を行頭限定で抽出
- 1 ファイル内複数領域可、ネスト禁止
- 領域外バイト一致を `replace_auto_regions` で保持
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.errors import MalformedAutoMarkerError
from agent.writers.markdown_writer import (
    AutoRegion,
    extract_auto_regions,
    replace_auto_regions,
)


class TestExtractAutoRegions:
    def test_no_regions(self) -> None:
        content = "## Header\n\nSome content without markers.\n"
        assert extract_auto_regions(content) == []

    def test_single_region(self) -> None:
        content = (
            "## 概要\n"
            "<!-- AUTO:START -->\n"
            "本文\n"
            "<!-- AUTO:END -->\n"
            "## 公式\n"
        )
        regions = extract_auto_regions(content)
        assert len(regions) == 1
        assert regions[0] == AutoRegion(start_line=1, end_line=3, inner_lines=("本文",))

    def test_multiple_regions(self) -> None:
        content = (
            "<!-- AUTO:START -->\n"
            "A\n"
            "<!-- AUTO:END -->\n"
            "middle\n"
            "<!-- AUTO:START -->\n"
            "B\n"
            "B2\n"
            "<!-- AUTO:END -->\n"
        )
        regions = extract_auto_regions(content)
        assert len(regions) == 2
        assert regions[0].inner_lines == ("A",)
        assert regions[1].inner_lines == ("B", "B2")

    def test_unmatched_start_raises(self) -> None:
        content = "<!-- AUTO:START -->\n本文\n"
        with pytest.raises(MalformedAutoMarkerError, match="対応する AUTO:END"):
            extract_auto_regions(content)

    def test_unmatched_end_raises(self) -> None:
        content = "本文\n<!-- AUTO:END -->\n"
        with pytest.raises(MalformedAutoMarkerError, match="対応する AUTO:START のない"):
            extract_auto_regions(content)

    def test_nested_raises(self) -> None:
        content = (
            "<!-- AUTO:START -->\n"
            "<!-- AUTO:START -->\n"
            "<!-- AUTO:END -->\n"
            "<!-- AUTO:END -->\n"
        )
        with pytest.raises(MalformedAutoMarkerError, match="ネスト"):
            extract_auto_regions(content)

    def test_inline_marker_raises(self) -> None:
        content = "前置 <!-- AUTO:START --> 後置\n本文\n<!-- AUTO:END -->\n"
        with pytest.raises(MalformedAutoMarkerError, match="行頭以外"):
            extract_auto_regions(content)

    def test_empty_region(self) -> None:
        content = "<!-- AUTO:START -->\n<!-- AUTO:END -->\n"
        regions = extract_auto_regions(content)
        assert len(regions) == 1
        assert regions[0].inner_lines == ()


class TestReplaceAutoRegions:
    def test_replace_single_region(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        original = (
            "前\n"
            "<!-- AUTO:START -->\n"
            "古い本文\n"
            "<!-- AUTO:END -->\n"
            "後\n"
        )
        path.write_text(original, encoding="utf-8")
        replace_auto_regions(path, ["新しい本文"])
        result = path.read_text(encoding="utf-8")
        assert result == (
            "前\n"
            "<!-- AUTO:START -->\n"
            "新しい本文\n"
            "<!-- AUTO:END -->\n"
            "後\n"
        )

    def test_replace_multiple_regions(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        original = (
            "<!-- AUTO:START -->\n"
            "A\n"
            "<!-- AUTO:END -->\n"
            "中間\n"
            "<!-- AUTO:START -->\n"
            "B\n"
            "<!-- AUTO:END -->\n"
        )
        path.write_text(original, encoding="utf-8")
        replace_auto_regions(path, ["X", "Y\nY2"])
        result = path.read_text(encoding="utf-8")
        assert result == (
            "<!-- AUTO:START -->\n"
            "X\n"
            "<!-- AUTO:END -->\n"
            "中間\n"
            "<!-- AUTO:START -->\n"
            "Y\nY2\n"
            "<!-- AUTO:END -->\n"
        )

    def test_outside_bytes_preserved(self, tmp_path: Path) -> None:
        """領域外のバイト列が完全一致することを保証。"""
        path = tmp_path / "test.md"
        original = (
            "---\n"
            "title: test\n"
            "---\n"
            "\n"
            "## 見出し\n"
            "  インデント付きテキスト\n"
            "<!-- AUTO:START -->\n"
            "old\n"
            "<!-- AUTO:END -->\n"
            "  末尾もインデント\n"
        )
        path.write_text(original, encoding="utf-8")
        replace_auto_regions(path, ["new"])
        result = path.read_text(encoding="utf-8")
        # 領域外（frontmatter / 見出し / インデント / 末尾）は完全保持
        assert "---\ntitle: test\n---\n" in result
        assert "  インデント付きテキスト\n" in result
        assert "  末尾もインデント\n" in result
        assert "new" in result
        assert "old" not in result

    def test_region_count_mismatch_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        path.write_text(
            "<!-- AUTO:START -->\nA\n<!-- AUTO:END -->\n", encoding="utf-8"
        )
        with pytest.raises(MalformedAutoMarkerError, match="領域数"):
            replace_auto_regions(path, ["A", "B"])

    def test_no_regions_noop(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        original = "## Header\nplain text\n"
        path.write_text(original, encoding="utf-8")
        replace_auto_regions(path, [])
        assert path.read_text(encoding="utf-8") == original

    def test_trailing_newline_preserved(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        original_with_newline = "<!-- AUTO:START -->\nA\n<!-- AUTO:END -->\n"
        path.write_text(original_with_newline, encoding="utf-8")
        replace_auto_regions(path, ["B"])
        assert path.read_text(encoding="utf-8").endswith("\n")

        original_no_newline = "<!-- AUTO:START -->\nA\n<!-- AUTO:END -->"
        path.write_text(original_no_newline, encoding="utf-8")
        replace_auto_regions(path, ["B"])
        assert not path.read_text(encoding="utf-8").endswith("\n")


class TestAutoRegionPurpose:
    """ADR-019: AUTO マーカー `purpose` 属性のパース検証。"""

    def test_purpose_parsed_when_present(self) -> None:
        content = (
            "<!-- AUTO:START purpose=summary-1-paragraph -->\n"
            "本文\n"
            "<!-- AUTO:END -->\n"
        )
        regions = extract_auto_regions(content)
        assert len(regions) == 1
        assert regions[0].purpose == "summary-1-paragraph"
        assert regions[0].inner_lines == ("本文",)

    def test_purpose_none_when_absent(self) -> None:
        content = "<!-- AUTO:START -->\n本文\n<!-- AUTO:END -->\n"
        regions = extract_auto_regions(content)
        assert len(regions) == 1
        assert regions[0].purpose is None

    def test_purpose_preserved_per_region(self) -> None:
        content = (
            "<!-- AUTO:START purpose=recipe-tldr -->\n"
            "TL;DR\n"
            "<!-- AUTO:END -->\n"
            "\n"
            "<!-- AUTO:START purpose=recipe-steps -->\n"
            "1. step\n"
            "<!-- AUTO:END -->\n"
        )
        regions = extract_auto_regions(content)
        assert [r.purpose for r in regions] == ["recipe-tldr", "recipe-steps"]

    def test_purpose_uppercase_raises(self) -> None:
        content = "<!-- AUTO:START purpose=Summary -->\n本文\n<!-- AUTO:END -->\n"
        with pytest.raises(MalformedAutoMarkerError, match="purpose 属性値が不正"):
            extract_auto_regions(content)

    def test_purpose_underscore_raises(self) -> None:
        content = (
            "<!-- AUTO:START purpose=foo_bar -->\n本文\n<!-- AUTO:END -->\n"
        )
        with pytest.raises(MalformedAutoMarkerError, match="purpose 属性値が不正"):
            extract_auto_regions(content)

    def test_purpose_empty_raises(self) -> None:
        content = "<!-- AUTO:START purpose= -->\n本文\n<!-- AUTO:END -->\n"
        with pytest.raises(MalformedAutoMarkerError, match="purpose 属性値が不正"):
            extract_auto_regions(content)

    def test_end_marker_with_attribute_raises(self) -> None:
        content = (
            "<!-- AUTO:START -->\n本文\n<!-- AUTO:END purpose=foo -->\n"
        )
        with pytest.raises(MalformedAutoMarkerError, match="AUTO:END"):
            extract_auto_regions(content)

    def test_replace_preserves_purpose_attribute(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        original = (
            "<!-- AUTO:START purpose=summary-1-paragraph -->\n"
            "old body\n"
            "<!-- AUTO:END -->\n"
        )
        path.write_text(original, encoding="utf-8")
        replace_auto_regions(path, ["new body"])
        result = path.read_text(encoding="utf-8")
        assert "<!-- AUTO:START purpose=summary-1-paragraph -->" in result
        assert "new body" in result
        assert "old body" not in result
