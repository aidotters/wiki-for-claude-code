"""Markdown ファイル書き込み。冪等性のため意味のある差分判定を行う。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from agent.writers.frontmatter import FrontmatterDocument, read_file, serialize, write_file

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
