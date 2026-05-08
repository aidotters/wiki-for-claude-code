"""ADR-019: `regenerate_source` AUTO 領域経路の per-region LLM 呼び出しテスト。

検証対象:
- AUTO 経路で `llm.generate` が領域数だけ呼ばれる
- content_hash 一致 + force=False で LLM 未呼び出し（早期 return）
- content_hash 一致 + force=True で LLM 呼び出される
- `purpose` 既定値推論（source / recipe）
- LLM 空応答時 `LLMGenerationError`
- `auto_section_managed != true` は `FrontmatterValidationError`
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest

from agent.errors import FrontmatterValidationError, LLMGenerationError
from agent.fetchers.http_fetcher import HttpFetcher
from agent.orchestration.regenerate import _default_purpose, regenerate_source

WHITELIST = [
    {
        "id": "anthropic-claude-docs",
        "name": "Anthropic",
        "base_url": "https://docs.claude.com/",
        "fetch_method": "http",
        "rate_limit": "1 req/sec",
        "license_notes": "...",
        "enabled": True,
    }
]


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _make_vault(tmp_path: Path, repo_root: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "sources" / "official" / "hooks").mkdir(parents=True)
    (vault / "90_meta" / "_schemas").mkdir(parents=True)
    shutil.copy(
        repo_root / "vault" / "90_meta" / "_schemas" / "frontmatter.schema.json",
        vault / "90_meta" / "_schemas" / "frontmatter.schema.json",
    )
    shutil.copy(
        repo_root / "vault" / "90_meta" / "sources.md",
        vault / "90_meta" / "sources.md",
    )
    (vault / "index.md").write_text("# Index\n", encoding="utf-8")
    (vault / "log.md").write_text("# Log\n", encoding="utf-8")
    return vault


def _make_fetcher(etag: str = "v1") -> HttpFetcher:
    transport = httpx.MockTransport(
        lambda req: httpx.Response(
            200, text="raw content for AUTO region", headers={"ETag": etag}
        )
    )
    return HttpFetcher(
        WHITELIST,
        rate_limit_sleep=0,
        client=httpx.Client(transport=transport, follow_redirects=True),
    )


@dataclass
class _RecordingLLM:
    """`llm.generate` の呼び出し回数と prompt を記録する mock。"""

    response: str = "再生成された要約。"
    calls: list[str] | None = None

    def __post_init__(self) -> None:
        if self.calls is None:
            self.calls = []

    def generate(self, prompt: str) -> str:
        assert self.calls is not None
        self.calls.append(prompt)
        return self.response


def _write_source_page(
    path: Path,
    *,
    source_url: str,
    source_version: str | None = None,
    auto_section_managed: bool = True,
    inner_body: str = "既存の要約内容。",
    purpose_attr: str = " purpose=summary-1-paragraph",
) -> None:
    sv = "null" if source_version is None else f'"{source_version}"'
    auto_managed = "true" if auto_section_managed else "false"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
title: "Test Source"
type: source
confidence: 0.85
sources: []
last_updated: 2026-05-05
stale: false
tags: [hooks]
source_url: "{source_url}"
fetched_at: "2026-05-05T10:00:00Z"
source_version: {sv}
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: false
status: draft
auto_section_managed: {auto_managed}
---

## 概要 (要約)
<!-- AUTO:START{purpose_attr} -->
{inner_body}
<!-- AUTO:END -->

## 公式ドキュメント
→ {source_url}
（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）
""",
        encoding="utf-8",
    )


class TestDefaultPurpose:
    def test_source_returns_summary(self) -> None:
        assert _default_purpose("source", 0) == "summary-1-paragraph"
        assert _default_purpose("source", 5) == "summary-1-paragraph"

    def test_recipe_first_is_tldr(self) -> None:
        assert _default_purpose("recipe", 0) == "recipe-tldr"

    def test_recipe_second_is_steps(self) -> None:
        assert _default_purpose("recipe", 1) == "recipe-steps"

    def test_recipe_third_raises(self) -> None:
        with pytest.raises(FrontmatterValidationError, match="purpose 既定値"):
            _default_purpose("recipe", 2)

    def test_unknown_type_raises(self) -> None:
        with pytest.raises(FrontmatterValidationError, match="purpose 既定値"):
            _default_purpose("concept", 0)


class TestRegenerateAuto:
    def test_calls_llm_when_content_changed(
        self, tmp_path: Path, repo_root: Path
    ) -> None:
        vault = _make_vault(tmp_path, repo_root)
        url = "https://docs.claude.com/claude-code/hooks/changed"
        target = vault / "sources" / "official" / "hooks" / "changed.md"
        _write_source_page(target, source_url=url, source_version="v0-old")

        llm = _RecordingLLM(response="新しい要約段落です。")
        result = regenerate_source(
            target,
            vault_root=vault,
            fetcher=_make_fetcher(etag="v1"),
            llm=llm,
        )

        assert llm.calls is not None
        assert len(llm.calls) == 1, "領域数 1 に対し LLM が 1 回呼ばれるはず"
        assert result.write_result.changed is True
        body = target.read_text(encoding="utf-8")
        assert "新しい要約段落です。" in body
        assert "既存の要約内容。" not in body
        # AUTO 外（公式ドキュメント見出し）が残存
        assert "## 公式ドキュメント" in body

    def test_skips_llm_when_content_unchanged_and_not_forced(
        self, tmp_path: Path, repo_root: Path
    ) -> None:
        vault = _make_vault(tmp_path, repo_root)
        url = "https://docs.claude.com/claude-code/hooks/unchanged"
        target = vault / "sources" / "official" / "hooks" / "unchanged.md"
        _write_source_page(target, source_url=url, source_version="v1")

        llm = _RecordingLLM()
        result = regenerate_source(
            target,
            vault_root=vault,
            fetcher=_make_fetcher(etag="v1"),
            llm=llm,
        )

        assert llm.calls == [], "content_hash 一致 + force=False なら LLM 未呼び出し"
        assert result.write_result.changed is False

    def test_force_invokes_llm_even_when_unchanged(
        self, tmp_path: Path, repo_root: Path
    ) -> None:
        vault = _make_vault(tmp_path, repo_root)
        url = "https://docs.claude.com/claude-code/hooks/forced"
        target = vault / "sources" / "official" / "hooks" / "forced.md"
        _write_source_page(target, source_url=url, source_version="v1")

        llm = _RecordingLLM(response="強制再生成の要約。")
        result = regenerate_source(
            target,
            vault_root=vault,
            fetcher=_make_fetcher(etag="v1"),
            llm=llm,
            force=True,
        )

        assert llm.calls is not None
        assert len(llm.calls) == 1
        assert result.write_result.changed is True
        assert "強制再生成の要約。" in target.read_text(encoding="utf-8")

    def test_purpose_default_inferred_when_attribute_missing(
        self, tmp_path: Path, repo_root: Path
    ) -> None:
        """属性無しマーカーは既定値（source なら summary-1-paragraph）で動作する。"""
        vault = _make_vault(tmp_path, repo_root)
        url = "https://docs.claude.com/claude-code/hooks/no-attr"
        target = vault / "sources" / "official" / "hooks" / "no-attr.md"
        _write_source_page(
            target,
            source_url=url,
            source_version="v0-old",
            purpose_attr="",
        )

        llm = _RecordingLLM(response="既定 purpose で生成。")
        regenerate_source(
            target,
            vault_root=vault,
            fetcher=_make_fetcher(etag="v1"),
            llm=llm,
        )
        assert llm.calls is not None
        assert len(llm.calls) == 1

    def test_empty_llm_response_raises(
        self, tmp_path: Path, repo_root: Path
    ) -> None:
        vault = _make_vault(tmp_path, repo_root)
        url = "https://docs.claude.com/claude-code/hooks/empty"
        target = vault / "sources" / "official" / "hooks" / "empty.md"
        _write_source_page(target, source_url=url, source_version="v0-old")

        llm = _RecordingLLM(response="   \n  ")
        with pytest.raises(LLMGenerationError, match="空応答"):
            regenerate_source(
                target,
                vault_root=vault,
                fetcher=_make_fetcher(etag="v1"),
                llm=llm,
            )

    def test_auto_section_managed_false_raises(
        self, tmp_path: Path, repo_root: Path
    ) -> None:
        vault = _make_vault(tmp_path, repo_root)
        url = "https://docs.claude.com/claude-code/hooks/no-auto"
        target = vault / "sources" / "official" / "hooks" / "no-auto.md"
        _write_source_page(
            target,
            source_url=url,
            source_version="v0-old",
            auto_section_managed=False,
        )

        with pytest.raises(FrontmatterValidationError, match="auto_section_managed=true"):
            regenerate_source(
                target,
                vault_root=vault,
                fetcher=_make_fetcher(etag="v1"),
                llm=_RecordingLLM(),
            )

    def test_outside_bytes_preserved_after_regenerate(
        self, tmp_path: Path, repo_root: Path
    ) -> None:
        vault = _make_vault(tmp_path, repo_root)
        url = "https://docs.claude.com/claude-code/hooks/outside-bytes"
        target = vault / "sources" / "official" / "hooks" / "outside-bytes.md"
        _write_source_page(target, source_url=url, source_version="v0-old")

        before = target.read_text(encoding="utf-8")
        llm = _RecordingLLM(response="完全に異なる新規要約。")
        regenerate_source(
            target,
            vault_root=vault,
            fetcher=_make_fetcher(etag="v1"),
            llm=llm,
        )
        after = target.read_text(encoding="utf-8")

        # `## 公式ドキュメント` 行とその下の `→ URL` は AUTO 外で不変
        assert "## 公式ドキュメント\n→ " in before
        assert "## 公式ドキュメント\n→ " in after
        # AUTO マーカー行は purpose 属性込みで保持される
        assert "<!-- AUTO:START purpose=summary-1-paragraph -->" in after
        assert "<!-- AUTO:END -->" in after

    def test_log_records_generation_count(
        self, tmp_path: Path, repo_root: Path
    ) -> None:
        vault = _make_vault(tmp_path, repo_root)
        url = "https://docs.claude.com/claude-code/hooks/log-test"
        target = vault / "sources" / "official" / "hooks" / "log-test.md"
        _write_source_page(target, source_url=url, source_version="v0-old")

        llm = _RecordingLLM(response="新規本文。")
        regenerate_source(
            target,
            vault_root=vault,
            fetcher=_make_fetcher(etag="v1"),
            llm=llm,
        )
        log = (vault / "log.md").read_text(encoding="utf-8")
        assert "AUTO regions" in log
        assert "1 generated" in log
