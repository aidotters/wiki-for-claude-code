"""vault/index.md, vault/log.md, vault/overview.md の更新ヘルパー。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def append_log(vault_root: Path, operation: str, description: str) -> None:
    """vault/log.md の末尾に追記する。

    フォーマット: `## [YYYY-MM-DD HH:MM] operation | description`
    """
    log_path = vault_root / "log.md"
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
    entry = f"\n## [{timestamp}] {operation} | {description}\n"
    if log_path.exists():
        log_path.write_text(log_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"# Operation Log\n{entry}", encoding="utf-8")


def read_recent_log(vault_root: Path, lines: int = 10) -> list[str]:
    """log.md の末尾から `lines` 件分のエントリを返す。"""
    log_path = vault_root / "log.md"
    if not log_path.exists():
        return []
    entries = [
        line for line in log_path.read_text(encoding="utf-8").splitlines() if line.startswith("## [")
    ]
    return entries[-lines:]


def ensure_index_entry(vault_root: Path, page_path: Path) -> bool:
    """vault/index.md に対象ページへの wikilink が含まれているか確認する。

    Phase 1 では「含まれていなければ True を返して呼び出し側に通知」のみ。
    実際の挿入位置はカテゴリに依存するため、Phase 1 では手動編集とする。
    返り値: 既に index に存在すれば True、不在なら False。
    """
    index_path = vault_root / "index.md"
    if not index_path.exists():
        return False
    rel = page_path.relative_to(vault_root).with_suffix("")
    rel_str = rel.as_posix()
    text = index_path.read_text(encoding="utf-8")
    return f"[[{rel_str}]]" in text or f"[[{rel.name}]]" in text
