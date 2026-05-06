"""共通フィクスチャ。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_ROOT = REPO_ROOT / "vault"


@pytest.fixture
def vault_root() -> Path:
    return VAULT_ROOT


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def schema_path() -> Path:
    return VAULT_ROOT / "90_meta" / "_schemas" / "frontmatter.schema.json"


@pytest.fixture
def sample_source_metadata() -> dict[str, object]:
    return {
        "title": "Sample Source",
        "type": "source",
        "confidence": 0.85,
        "sources": [],
        "last_updated": "2026-05-05",
        "stale": False,
        "tags": ["sample"],
        "source_url": "https://docs.claude.com/claude-code/sample",
        "fetched_at": "2026-05-05T10:00:00Z",
        "source_version": None,
        "claude_code_version": "1.5.0",
        "reviewer": "tak",
        "human_edited": True,
        "status": "published",
        "auto_section_managed": False,
    }


@pytest.fixture
def sample_source_body() -> str:
    return (
        "\n"
        "## 概要 (要約)\n"
        "サンプルソースの概要です。\n\n"
        "## 公式ドキュメント\n"
        "→ https://docs.claude.com/claude-code/sample\n"
        "（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）\n\n"
        "## 補足解説 (日本語)\n"
        "サンプルソースの補足解説です。\n"
    )


@pytest.fixture
def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")
