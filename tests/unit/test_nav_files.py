"""agent/writers/nav_files のテスト。"""

from __future__ import annotations

from pathlib import Path

from agent.writers.nav_files import append_log, ensure_index_entry, read_recent_log


def test_append_log_creates_file(tmp_path: Path) -> None:
    append_log(tmp_path, "ingest", "first entry")
    log = (tmp_path / "log.md").read_text(encoding="utf-8")
    assert "# Operation Log" in log
    assert "ingest | first entry" in log


def test_append_log_appends(tmp_path: Path) -> None:
    log = tmp_path / "log.md"
    log.write_text("# Operation Log\n\n## [2026-01-01 00:00] init | seed\n", encoding="utf-8")
    append_log(tmp_path, "lint", "ran lint")
    text = log.read_text(encoding="utf-8")
    assert "init | seed" in text
    assert "lint | ran lint" in text


def test_read_recent_log_returns_last_n(tmp_path: Path) -> None:
    for i in range(15):
        append_log(tmp_path, "op", f"entry {i}")
    recent = read_recent_log(tmp_path, lines=10)
    assert len(recent) == 10
    assert "entry 14" in recent[-1]


def test_ensure_index_entry_detects_existing(tmp_path: Path) -> None:
    (tmp_path / "index.md").write_text(
        "# Index\n- [[sources/official/cli/installation]]\n",
        encoding="utf-8",
    )
    page = tmp_path / "sources" / "official" / "cli" / "installation.md"
    assert ensure_index_entry(tmp_path, page) is True


def test_ensure_index_entry_detects_missing(tmp_path: Path) -> None:
    (tmp_path / "index.md").write_text("# Index\n", encoding="utf-8")
    page = tmp_path / "sources" / "official" / "cli" / "missing.md"
    assert ensure_index_entry(tmp_path, page) is False
