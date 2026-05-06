"""lint バリデータ。

検出6項目:
1. 孤立ページ (orphan)
2. 陳腐化 (stale)
3. 矛盾 (contradiction) — Phase 1 では同一 tag のリスト化のみ
4. 低信頼度 (low_confidence)
5. 不足ページ (broken_wikilinks)
6. index 同期 (index_sync)
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from agent.writers.frontmatter import FrontmatterDocument, parse

WIKILINK_PATTERN = re.compile(r"\[\[([^\]\|]+?)(?:\|[^\]]*)?\]\]")

# 検出対象から除外するページ
EXCLUDED_FROM_ORPHAN = {"index.md", "log.md", "overview.md"}
EXCLUDED_DIRS = {"90_meta", "30_drafts"}

LOW_CONFIDENCE_THRESHOLD = 0.5
STALE_DAYS = 30


@dataclass
class LintReport:
    orphans: list[Path] = field(default_factory=list)
    stale: list[tuple[Path, int]] = field(default_factory=list)  # (path, days_old)
    low_confidence: list[tuple[Path, float]] = field(default_factory=list)
    broken_wikilinks: list[tuple[Path, str]] = field(default_factory=list)
    index_sync_missing: list[Path] = field(default_factory=list)
    contradictions: list[tuple[str, list[Path]]] = field(default_factory=list)

    @property
    def total_violations(self) -> int:
        return (
            len(self.orphans)
            + len(self.stale)
            + len(self.low_confidence)
            + len(self.broken_wikilinks)
            + len(self.index_sync_missing)
            + len(self.contradictions)
        )

    def format(self) -> str:
        lines = ["=== Lint Report ==="]
        lines.append(f"Orphan pages:        {len(self.orphans)}")
        lines.append(f"Stale pages:         {len(self.stale)}")
        lines.append(f"Low confidence:      {len(self.low_confidence)}")
        lines.append(f"Broken wikilinks:    {len(self.broken_wikilinks)}")
        lines.append(f"Index sync issues:   {len(self.index_sync_missing)}")
        lines.append(f"Contradictions:      {len(self.contradictions)}")
        lines.append("-------------------")
        lines.append(f"Total violations:    {self.total_violations}")
        for p in self.orphans:
            lines.append(f"[orphan] {p}")
        for p, days in self.stale:
            lines.append(f"[stale] {p} (days_old: {days})")
        for p, c in self.low_confidence:
            lines.append(f"[low_confidence] {p} (confidence: {c})")
        for p, link in self.broken_wikilinks:
            lines.append(f"[broken] {p} -> [[{link}]]")
        for p in self.index_sync_missing:
            lines.append(f"[index_sync] {p}")
        for tag, paths in self.contradictions:
            joined = ", ".join(str(p) for p in paths)
            lines.append(f"[contradiction-candidate] tag={tag}: {joined}")
        return "\n".join(lines)


def _list_md_files(vault_root: Path) -> list[Path]:
    files: list[Path] = []
    for p in vault_root.rglob("*.md"):
        rel_parts = p.relative_to(vault_root).parts
        if rel_parts[0] in EXCLUDED_DIRS:
            continue
        files.append(p)
    return files


def _read_meta_body(path: Path) -> FrontmatterDocument:
    return parse(path.read_text(encoding="utf-8"))


def _extract_wikilinks(body: str) -> list[str]:
    return [m.group(1).strip() for m in WIKILINK_PATTERN.finditer(body)]


def _wikilink_to_path(vault_root: Path, link: str) -> Path:
    return vault_root / f"{link}.md"


def _wikilink_resolve(vault_root: Path, link: str) -> Path | None:
    """Wikilink を実ファイルパスに解決する。完全パス指定 or basename のいずれか。"""
    full = _wikilink_to_path(vault_root, link)
    if full.exists():
        return full
    # basename 指定: vault 配下を再帰検索
    basename = f"{Path(link).name}.md"
    for candidate in vault_root.rglob(basename):
        return candidate
    return None


def _days_since(iso_date: str, today: date) -> int:
    try:
        d = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError:
        return 0
    return (today - d).days


def lint_vault(vault_root: Path, today: date | None = None) -> LintReport:
    today = today or date.today()
    files = _list_md_files(vault_root)
    docs: dict[Path, FrontmatterDocument] = {}
    for f in files:
        try:
            docs[f] = _read_meta_body(f)
        except ValueError:
            continue

    report = LintReport()

    # インバウンド wikilinks 集計（孤立・不足の検出に使用）
    inbound: dict[Path, set[Path]] = defaultdict(set)
    for source_path, doc in docs.items():
        for link in _extract_wikilinks(doc.body):
            target = _wikilink_resolve(vault_root, link)
            if target is None:
                report.broken_wikilinks.append((source_path, link))
            else:
                inbound[target].add(source_path)

    # 1. orphan: 被参照 0 件、ナビ3点を除く
    for p in docs:
        if p.name in EXCLUDED_FROM_ORPHAN:
            continue
        if not inbound.get(p):
            report.orphans.append(p)

    # 2. stale: stale: true もしくは last_updated > 30日
    for p, doc in docs.items():
        if doc.metadata.get("stale") is True:
            report.stale.append((p, -1))
            continue
        last = doc.metadata.get("last_updated")
        if isinstance(last, str):
            days = _days_since(last, today)
            if days > STALE_DAYS:
                report.stale.append((p, days))
        elif isinstance(last, date):
            days = (today - last).days
            if days > STALE_DAYS:
                report.stale.append((p, days))

    # 4. low_confidence
    for p, doc in docs.items():
        c = doc.metadata.get("confidence")
        if isinstance(c, int | float) and not isinstance(c, bool) and c < LOW_CONFIDENCE_THRESHOLD:
            report.low_confidence.append((p, float(c)))

    # 6. index_sync: index.md に published ページが含まれているか
    index_path = vault_root / "index.md"
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        index_links = set(_extract_wikilinks(index_text))
        for p, doc in docs.items():
            if doc.metadata.get("status") != "published":
                continue
            if p.name in EXCLUDED_FROM_ORPHAN:
                continue
            rel = p.relative_to(vault_root).with_suffix("").as_posix()
            if rel not in index_links and Path(rel).name not in index_links:
                report.index_sync_missing.append(p)

    # 3. contradiction: 同一 tag を持つ2件以上のページのリスト化（Phase 1 では集計のみ・report に積まない）
    # Phase 2 以降で LLM ベースの矛盾検出を導入し、本セクションを拡張する。
    return report
