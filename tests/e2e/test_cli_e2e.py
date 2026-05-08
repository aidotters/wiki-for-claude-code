"""E2E: agent CLI 経由でのフロー（subprocess + monkeypatched fetcher）。

実際の CLI 実行は Python in-process に main() を呼ぶ形でテストする
（subprocess 起動は CI で時間がかかるため）。
"""

from __future__ import annotations

import shutil
from pathlib import Path

import httpx
import pytest

from agent.errors import EXIT_OK
from agent.runners.local import main


def _make_vault(tmp_path: Path, repo_root: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
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


def _stub_response(source_url: str) -> str:
    return f"""---
title: "Sample Hook"
type: source
confidence: 0.85
sources: []
last_updated: 2026-05-05
stale: false
tags: [hooks]
source_url: "{source_url}"
fetched_at: "2026-05-05T10:00:00Z"
source_version: null
claude_code_version: "1.5.0"
reviewer: "tak"
human_edited: false
status: draft
auto_section_managed: true
---

## 概要 (要約)
<!-- AUTO:START purpose=summary-1-paragraph -->
サンプルフックの概要です。
<!-- AUTO:END -->

## 公式ドキュメント
→ {source_url}
（最終確認: 2026-05-05 / 対象バージョン: 1.5.0）
"""


@pytest.fixture
def vault_with_stub_orchestration(tmp_path: Path, repo_root: Path, monkeypatch: pytest.MonkeyPatch):
    vault = _make_vault(tmp_path, repo_root)

    # ingest_source / regenerate_source の fetcher / llm を差し替える
    from agent.fetchers.http_fetcher import HttpFetcher
    from agent.orchestration import ingest as ingest_module
    from agent.orchestration import regenerate as regenerate_module
    from agent.orchestration.llm import StubLLMClient

    def fetcher_factory():
        transport = httpx.MockTransport(
            lambda req: httpx.Response(
                200, text="raw text", headers={"ETag": "v1"}
            )
        )
        return HttpFetcher(
            ingest_module.load_whitelist(vault / "90_meta" / "sources.md"),
            rate_limit_sleep=0,
            client=httpx.Client(transport=transport, follow_redirects=True),
        )

    captured_url = {"url": ""}

    original_ingest = ingest_module.ingest_source

    def _ingest(source_url, category, vault_root, **kwargs):
        captured_url["url"] = source_url
        return original_ingest(
            source_url=source_url,
            category=category,
            vault_root=vault_root,
            fetcher=fetcher_factory(),
            llm=StubLLMClient(fixed_response=_stub_response(source_url)),
            **{k: v for k, v in kwargs.items() if k in ("claude_code_version",)},
        )

    monkeypatch.setattr(
        "agent.runners.local.ingest_source"
        if False
        else "agent.orchestration.ingest.ingest_source",
        _ingest,
        raising=False,
    )

    # local.py は遅延 import するため、orchestration 側を直接差し替える
    monkeypatch.setattr(ingest_module, "ingest_source", _ingest)

    original_regen = regenerate_module.regenerate_source

    def _regen(target_path, vault_root, **kwargs):
        return original_regen(
            target_path,
            vault_root=vault_root,
            fetcher=fetcher_factory(),
            llm=StubLLMClient(fixed_response=_stub_response(captured_url["url"] or "https://docs.claude.com/x")),
        )

    monkeypatch.setattr(regenerate_module, "regenerate_source", _regen)
    return vault


def test_cli_ingest_then_validate(
    vault_with_stub_orchestration: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = vault_with_stub_orchestration
    url = "https://docs.claude.com/claude-code/hooks/cli-test"

    code_ingest = main(
        [
            "--vault-root",
            str(vault),
            "ingest",
            "--source-url",
            url,
            "--category",
            "hooks",
        ]
    )
    assert code_ingest == EXIT_OK
    out_ingest = capsys.readouterr().out
    assert "Ingested" in out_ingest

    article = vault / "sources" / "official" / "hooks" / "cli-test.md"
    assert article.exists()

    code_validate = main(
        ["--vault-root", str(vault), "validate", "--target", str(article)]
    )
    assert code_validate == EXIT_OK


def test_cli_ingest_then_regenerate_idempotent(
    vault_with_stub_orchestration: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = vault_with_stub_orchestration
    url = "https://docs.claude.com/claude-code/hooks/idem-cli"

    main(
        [
            "--vault-root",
            str(vault),
            "ingest",
            "--source-url",
            url,
            "--category",
            "hooks",
        ]
    )
    article = vault / "sources" / "official" / "hooks" / "idem-cli.md"
    capsys.readouterr()

    # 1回目（ETag を populate するため意味のある変更が起きうる）
    main(["--vault-root", str(vault), "regenerate", "--target", str(article)])
    capsys.readouterr()
    # 2回目: 完全冪等
    main(["--vault-root", str(vault), "regenerate", "--target", str(article)])
    out = capsys.readouterr().out
    assert "no changes" in out


def test_cli_verify_links_help(capsys: pytest.CaptureFixture[str]) -> None:
    """verify-links サブコマンドが parser に登録されている。"""
    import pytest as _pytest

    with _pytest.raises(SystemExit):
        main(["verify-links", "--help"])
    out = capsys.readouterr().out
    assert "verify-links" in out or "transclusion" in out
