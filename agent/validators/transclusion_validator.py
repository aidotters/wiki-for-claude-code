"""連続100文字一致検出バリデータ。

source 種別ページが取込み元 raw コンテンツと連続100文字以上一致しないことを検証する。
スライディングウィンドウ実装（簡易版、Phase 1 で十分）。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent.validators.frontmatter_validator import ValidationIssue
from agent.writers.frontmatter import parse

DEFAULT_WINDOW = 100


@dataclass
class MatchInfo:
    matched_text: str
    start_in_article: int


def _normalize(text: str) -> str:
    """改行・空白を正規化（半角化や句読点正規化はしない）。"""
    return "\n".join(line.rstrip() for line in text.splitlines())


def find_long_match(
    article_text: str,
    raw_text: str,
    window: int = DEFAULT_WINDOW,
) -> MatchInfo | None:
    """記事本文と raw 取込み元で連続 `window` 文字以上一致する箇所を返す。

    Phase 1 はナイーブなスライディングウィンドウ実装。
    """
    article = _normalize(article_text)
    raw = _normalize(raw_text)
    if len(article) < window or len(raw) < window:
        return None

    # raw 側の長さ window のすべての部分文字列を set 化
    raw_windows: set[str] = set()
    for i in range(len(raw) - window + 1):
        raw_windows.add(raw[i : i + window])

    for j in range(len(article) - window + 1):
        chunk = article[j : j + window]
        if chunk in raw_windows:
            return MatchInfo(matched_text=chunk, start_in_article=j)
    return None


def validate(
    article_body: str,
    raw_content: str,
    file_path: Path | None = None,
    window: int = DEFAULT_WINDOW,
) -> list[ValidationIssue]:
    match = find_long_match(article_body, raw_content, window=window)
    if match is None:
        return []
    return [
        ValidationIssue(
            file_path=file_path,
            field="transclusion",
            message=(
                f"raw コンテンツと連続 {window} 文字以上の一致を検出"
                f"（記事内 offset {match.start_in_article}）"
            ),
        )
    ]


def validate_file_against_raw(
    path: Path,
    raw_content: str,
    window: int = DEFAULT_WINDOW,
) -> list[ValidationIssue]:
    doc = parse(path.read_text(encoding="utf-8"))
    if doc.metadata.get("type") != "source":
        return []
    return validate(doc.body, raw_content, file_path=path, window=window)
