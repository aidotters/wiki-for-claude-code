"""source_url への HTTP HEAD リクエスト到達確認バリデータ（警告のみ）。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx

from agent.validators.frontmatter_validator import ValidationIssue
from agent.writers.frontmatter import parse


@dataclass
class LinkCheckResult:
    file_path: Path
    source_url: str
    status_code: int | None
    ok: bool
    error: str | None = None


def check_url(url: str, client: httpx.Client | None = None) -> tuple[int | None, str | None]:
    own_client = client is None
    c = client or httpx.Client(follow_redirects=True, timeout=10.0)
    try:
        response = c.head(url)
        return response.status_code, None
    except httpx.HTTPError as e:
        return None, str(e)
    finally:
        if own_client:
            c.close()


def validate_file(
    path: Path,
    client: httpx.Client | None = None,
) -> list[ValidationIssue]:
    """source_url の到達確認。HTTP 200 以外は警告として返す（fail させない上位呼び出し前提）。"""
    doc = parse(path.read_text(encoding="utf-8"))
    if doc.metadata.get("type") != "source":
        return []
    url = doc.metadata.get("source_url")
    if not isinstance(url, str):
        return [ValidationIssue(file_path=path, field="source_url", message="source_url が無効")]
    code, err = check_url(url, client=client)
    if err:
        return [
            ValidationIssue(
                file_path=path,
                field="source_url",
                message=f"HEAD リクエスト失敗: {err}",
            )
        ]
    if code != 200:
        return [
            ValidationIssue(
                file_path=path,
                field="source_url",
                message=f"HEAD ステータス {code}（200 以外）",
            )
        ]
    return []
