"""lint_all ユースケース。"""

from __future__ import annotations

from pathlib import Path

from agent.validators.lint_validator import LintReport, lint_vault
from agent.writers.nav_files import append_log


def lint_all(vault_root: Path, write_log: bool = True) -> LintReport:
    report = lint_vault(vault_root)
    if write_log:
        summary = (
            f"total={report.total_violations} "
            f"orphan={len(report.orphans)} "
            f"stale={len(report.stale)} "
            f"low_conf={len(report.low_confidence)} "
            f"broken={len(report.broken_wikilinks)} "
            f"index={len(report.index_sync_missing)} "
            f"contra={len(report.contradictions)}"
        )
        append_log(vault_root, "lint", summary)
    return report
