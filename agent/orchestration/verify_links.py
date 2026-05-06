"""verify_links ユースケース。

source 種別記事の ``source_url`` に対して HTTP HEAD で 200 到達確認を行う
ネットワーク依存サブコマンド。``agent validate --all`` には含めず、CI を
ネットワーク非依存に保つために分離した（ADR ロードマップ参照）。

raw コンテンツが取得できる場合は同時に transclusion（連続100文字一致）
検査も実施し、全文転載リスクを機械的に検出する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import httpx

from agent.fetchers.http_fetcher import HttpFetcher, load_whitelist
from agent.validators.frontmatter_validator import ValidationIssue
from agent.validators.link_validator import validate_file as validate_link_file
from agent.validators.transclusion_validator import (
    validate as validate_transclusion,
)
from agent.writers.frontmatter import parse as parse_frontmatter

VAULT_EXCLUDE_DIRS = {"30_drafts"}


@dataclass
class VerifyLinksSummary:
    issues: list[ValidationIssue] = field(default_factory=list)
    files_checked: int = 0

    @property
    def passed(self) -> bool:
        return not self.issues

    def format(self) -> str:
        lines = [f"Verified {self.files_checked} source articles"]
        for issue in self.issues:
            lines.append(str(issue))
        if self.passed:
            lines.append("All link/transclusion checks PASSED")
        else:
            lines.append(f"FAILED with {len(self.issues)} issues")
        return "\n".join(lines)


def _list_source_articles(vault_root: Path) -> list[Path]:
    files: list[Path] = []
    for p in (vault_root / "sources").rglob("*.md"):
        rel = p.relative_to(vault_root)
        if rel.parts[0] in VAULT_EXCLUDE_DIRS:
            continue
        files.append(p)
    return files


def verify_links(
    vault_root: Path,
    target: Path | None = None,
    http_client: httpx.Client | None = None,
    fetcher: HttpFetcher | None = None,
    check_transclusion: bool = True,
) -> VerifyLinksSummary:
    """source 種別記事の URL 到達確認 + 任意で連続100文字一致検査。

    ``fetcher`` を渡した場合、各記事の raw コンテンツを取得して transclusion 検査する。
    ``fetcher`` 未指定時は HEAD 確認のみ。
    """
    files = [target] if target is not None else _list_source_articles(vault_root)

    if fetcher is None and check_transclusion:
        try:
            whitelist = load_whitelist(vault_root / "90_meta" / "sources.md")
            fetcher = HttpFetcher(whitelist)
        except (FileNotFoundError, OSError):
            fetcher = None

    summary = VerifyLinksSummary()
    for f in files:
        try:
            doc = parse_frontmatter(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if doc.metadata.get("type") != "source":
            continue
        summary.files_checked += 1

        link_issues = validate_link_file(f, client=http_client)
        summary.issues.extend(link_issues)

        if check_transclusion and fetcher is not None and not link_issues:
            url = doc.metadata.get("source_url")
            if isinstance(url, str):
                try:
                    raw = fetcher.fetch(url).raw_content
                except Exception as e:  # noqa: BLE001
                    summary.issues.append(
                        ValidationIssue(
                            file_path=f,
                            field="transclusion",
                            message=f"raw 取得失敗（transclusion 検査スキップ）: {e}",
                        )
                    )
                    continue
                summary.issues.extend(
                    validate_transclusion(doc.body, raw, file_path=f)
                )

    return summary
