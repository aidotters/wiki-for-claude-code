"""Markdown ファイル書き込み。冪等性のため意味のある差分判定を行う。

Phase 2-A から AUTO マーカー領域（`<!-- AUTO:START --> ... <!-- AUTO:END -->`）の
抽出・置換ロジックを併設する。詳細仕様は `vault/90_meta/auto-marker-spec.md`。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from agent.errors import MalformedAutoMarkerError
from agent.writers.frontmatter import FrontmatterDocument, read_file, serialize, write_file

AUTO_START_MARKER = "<!-- AUTO:START -->"
AUTO_END_MARKER = "<!-- AUTO:END -->"

# `<!-- AUTO:START -->` または `<!-- AUTO:START purpose=<value> -->` を許容する。
# `purpose` の値は `[a-z0-9-]+`（小文字英数 + ハイフン）に限定（auto-marker-spec.md）。
_AUTO_START_RE = re.compile(
    r"^<!-- AUTO:START(?:\s+purpose=(?P<purpose>[A-Za-z0-9_-]*))?\s*-->$"
)
_PURPOSE_VALUE_RE = re.compile(r"^[a-z0-9-]+$")

# 冪等性検査時に「機械的更新」として無視するキー（ハッシュ一致時は更新しない）
TIMESTAMP_KEYS = {"fetched_at", "last_updated"}


@dataclass
class WriteResult:
    file_path: Path
    changed: bool
    diff_summary: str


def compute_body_hash(body: str) -> str:
    """本文のみのハッシュ（空白・改行を正規化）。"""
    normalized = "\n".join(line.rstrip() for line in body.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_meaningful_hash(doc: FrontmatterDocument) -> str:
    """機械的更新キーを除外した frontmatter + 本文のハッシュ。

    冪等性チェックに用いる。同じ内容なら2回目の `regenerate` で差分0件になる。
    """
    meta_filtered = {k: v for k, v in doc.metadata.items() if k not in TIMESTAMP_KEYS}
    body_hash = compute_body_hash(doc.body)
    meta_repr = repr(sorted(meta_filtered.items()))
    return hashlib.sha256(f"{meta_repr}|{body_hash}".encode()).hexdigest()


def write(path: Path, new_doc: FrontmatterDocument) -> WriteResult:
    """ファイルを書き込み、意味のある変更があったか返す。

    既存ファイルが存在し、`compute_meaningful_hash` が一致する場合は
    タイムスタンプキーの更新も行わず、`changed=False` で返す。
    """
    if path.exists():
        old_doc = read_file(path)
        if compute_meaningful_hash(old_doc) == compute_meaningful_hash(new_doc):
            return WriteResult(file_path=path, changed=False, diff_summary="no meaningful changes")

    path.parent.mkdir(parents=True, exist_ok=True)
    write_file(path, new_doc)
    return WriteResult(file_path=path, changed=True, diff_summary="written")


def serialize_to_string(doc: FrontmatterDocument) -> str:
    """テスト用: 書き出し文字列を取得する。"""
    return serialize(doc)


@dataclass(frozen=True)
class AutoRegion:
    """1 つの AUTO 領域を表す。行番号は 0-origin、両端含む内部行のインデックス。

    `start_line`: `<!-- AUTO:START -->` のある行のインデックス
    `end_line`: `<!-- AUTO:END -->` のある行のインデックス
    `inner_lines`: マーカー行を含まない領域内の行（書き換え対象本文）
    `purpose`: AUTO 領域の用途メタデータ（例: "summary-1-paragraph"）。
        `<!-- AUTO:START purpose=... -->` から抽出。属性無しは `None`。
        既定値推論は orchestrator 側で実施（auto-marker-spec.md）。
    """

    start_line: int
    end_line: int
    inner_lines: tuple[str, ...]
    purpose: str | None = None


def extract_auto_regions(content: str) -> list[AutoRegion]:
    """文字列から AUTO 領域を順序付きで抽出する。

    構文不正（START/END 不対応・順序不正・ネスト・行頭以外配置）は
    `MalformedAutoMarkerError` を送出する。
    """
    lines = content.splitlines()
    regions: list[AutoRegion] = []
    open_start: int | None = None
    open_purpose: str | None = None

    for i, line in enumerate(lines):
        stripped = line.rstrip()
        start_match = _AUTO_START_RE.match(stripped)
        if start_match is not None:
            if open_start is not None:
                raise MalformedAutoMarkerError(
                    f"AUTO:START がネストしています (line {open_start + 1} と line {i + 1})"
                )
            raw_purpose = start_match.group("purpose")
            if raw_purpose is not None:
                if not _PURPOSE_VALUE_RE.match(raw_purpose):
                    raise MalformedAutoMarkerError(
                        f"AUTO:START の purpose 属性値が不正です "
                        f"(line {i + 1}, value={raw_purpose!r}). "
                        f"許容形式: [a-z0-9-]+"
                    )
                open_purpose = raw_purpose
            else:
                open_purpose = None
            open_start = i
        elif stripped == AUTO_END_MARKER:
            if open_start is None:
                raise MalformedAutoMarkerError(
                    f"対応する AUTO:START のない AUTO:END (line {i + 1})"
                )
            inner = tuple(lines[open_start + 1 : i])
            regions.append(
                AutoRegion(
                    start_line=open_start,
                    end_line=i,
                    inner_lines=inner,
                    purpose=open_purpose,
                )
            )
            open_start = None
            open_purpose = None
        else:
            # 行頭以外への配置・END に属性を付けた等の異常を検出
            if "<!-- AUTO:START" in line:
                raise MalformedAutoMarkerError(
                    f"AUTO:START が行頭以外、もしくは属性形式が不正です (line {i + 1})"
                )
            if "<!-- AUTO:END" in line and stripped != AUTO_END_MARKER:
                raise MalformedAutoMarkerError(
                    f"AUTO:END が行頭以外に配置されているか、属性が付与されています "
                    f"(line {i + 1})"
                )

    if open_start is not None:
        raise MalformedAutoMarkerError(
            f"対応する AUTO:END のない AUTO:START (line {open_start + 1})"
        )

    return regions


def replace_auto_regions(path: Path, new_contents: list[str]) -> None:
    """ファイルの AUTO 領域を順番に置換する。

    - 領域数と `new_contents` の長さが一致しない場合 `MalformedAutoMarkerError`
    - 領域外（マーカー行を含む）のバイト列は書き換え前後で完全一致を保証する
    - `new_contents[i]` の末尾改行は呼び出し側で省略可（区切り改行は本関数が補う）
    """
    original_text = path.read_text(encoding="utf-8")
    regions = extract_auto_regions(original_text)
    if len(regions) != len(new_contents):
        raise MalformedAutoMarkerError(
            f"AUTO 領域数 {len(regions)} と置換コンテンツ数 {len(new_contents)} が不一致"
        )
    if not regions:
        # 何もしない（書き込みもしない）
        return

    # 改行コード保持（オリジナルが \n 区切りである前提、CRLF は今は扱わない）
    has_trailing_newline = original_text.endswith("\n")
    original_lines = original_text.splitlines()

    new_lines: list[str] = []
    cursor = 0
    for region, replacement in zip(regions, new_contents, strict=True):
        # 領域の前（マーカー前まで）を保持
        new_lines.extend(original_lines[cursor : region.start_line + 1])
        # 置換本文（複数行可、内部の改行で split）
        if replacement:
            new_lines.extend(replacement.splitlines())
        # 領域終端マーカー以降は次ループへ
        cursor = region.end_line
    # 最後の領域の END マーカーから末尾まで
    new_lines.extend(original_lines[cursor:])

    new_text = "\n".join(new_lines)
    if has_trailing_newline:
        new_text += "\n"

    # 領域外バイト一致の事後検証
    _assert_outside_bytes_match(original_text, new_text, regions)

    path.write_text(new_text, encoding="utf-8")


def _assert_outside_bytes_match(
    original_text: str,
    new_text: str,
    regions: list[AutoRegion],
) -> None:
    """書き換え後のテキストの領域外行が、書き換え前と完全一致することを検証する。"""
    original_lines = original_text.splitlines()
    new_lines = new_text.splitlines()

    # 領域外区間（行範囲）を抽出
    outside_segments_orig: list[list[str]] = []
    outside_segments_new: list[list[str]] = []
    cursor = 0
    new_cursor = 0
    for region in regions:
        # 領域開始マーカー行までの「領域外 + START マーカー」を抽出
        outside_segments_orig.append(original_lines[cursor : region.start_line + 1])
        # 新ファイル側の対応セグメントは、cursor から new 側 START マーカー位置まで
        # 領域数が一致している前提で、各セグメントの開始マーカー位置を順次特定
        new_start_idx = _find_start_marker(new_lines, new_cursor)
        if new_start_idx == -1:
            raise MalformedAutoMarkerError(
                "書き換え後ファイルに AUTO:START が想定数より少ない"
            )
        outside_segments_new.append(new_lines[new_cursor : new_start_idx + 1])
        # END マーカー位置を新側で特定
        new_end_idx = _find_marker(new_lines, AUTO_END_MARKER, new_start_idx + 1)
        if new_end_idx == -1:
            raise MalformedAutoMarkerError(
                "書き換え後ファイルに AUTO:END が想定数より少ない"
            )
        cursor = region.end_line
        new_cursor = new_end_idx
    # 最後の領域 END から末尾までを領域外として追加
    outside_segments_orig.append(original_lines[cursor:])
    outside_segments_new.append(new_lines[new_cursor:])

    for seg_orig, seg_new in zip(outside_segments_orig, outside_segments_new, strict=True):
        if seg_orig != seg_new:
            raise MalformedAutoMarkerError(
                "AUTO 領域外のバイト列が変化しました（実装バグ）"
            )


def _find_marker(lines: list[str], marker: str, start: int) -> int:
    for i in range(start, len(lines)):
        if lines[i].rstrip() == marker:
            return i
    return -1


def _find_start_marker(lines: list[str], start: int) -> int:
    """`<!-- AUTO:START -->` または `<!-- AUTO:START purpose=... -->` を検索する。"""
    for i in range(start, len(lines)):
        if _AUTO_START_RE.match(lines[i].rstrip()) is not None:
            return i
    return -1
