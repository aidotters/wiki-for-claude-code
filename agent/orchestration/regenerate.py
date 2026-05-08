"""regenerate_source ユースケース（ADR-015 / ADR-017 / ADR-019）。

`type=source` のページを対象に、AUTO マーカー領域（`auto_section_managed=true`）を
LLM で再生成する。各 AUTO 領域は `purpose` 属性（または既定値推論）で per-region
プロンプトテンプレを選択し、`llm.generate` を呼び出す。

content_hash 比較で取込み元に変化がない場合は冪等性のため早期 return する。
`force=True` 指定時は content_hash 一致時も LLM を呼ぶ（empirical 検証 / 手動再生成用）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from agent.errors import FrontmatterValidationError, LLMGenerationError
from agent.fetchers.http_fetcher import HttpFetcher, load_whitelist
from agent.orchestration.llm import LLMClient, make_backend
from agent.prompts.loader import load_prompt, render_prompt
from agent.writers.frontmatter import FrontmatterDocument, parse, serialize
from agent.writers.markdown_writer import (
    AutoRegion,
    WriteResult,
    extract_auto_regions,
    replace_auto_regions,
)
from agent.writers.nav_files import append_log


@dataclass
class RegenerateResult:
    article_path: Path
    write_result: WriteResult


def _default_purpose(doc_type: str, region_index: int) -> str:
    """`purpose` 省略時の既定値推論（auto-marker-spec.md / ADR-019）。

    - source 種別: 全領域 `summary-1-paragraph`
    - recipe 種別: 配置順 0 -> `recipe-tldr`, 1 -> `recipe-steps`
    - それ以外 / 範囲外は `FrontmatterValidationError`
    """
    if doc_type == "source":
        return "summary-1-paragraph"
    if doc_type == "recipe":
        if region_index == 0:
            return "recipe-tldr"
        if region_index == 1:
            return "recipe-steps"
        raise FrontmatterValidationError(
            f"recipe 種別の region {region_index} には purpose 既定値がありません。"
            " AUTO:START に purpose 属性を明示してください。"
        )
    raise FrontmatterValidationError(
        f"type={doc_type!r} の AUTO 領域は purpose 既定値を推論できません。"
        " AUTO:START に purpose 属性を明示してください。"
    )


def _build_region_prompts(
    regions: list[AutoRegion],
    *,
    doc_type: str,
    source_url: str,
    raw_content: str,
    today: str,
    claude_code_version: str,
) -> list[str]:
    """各 AUTO 領域について `purpose` から prompt を組み立てる。"""
    prompts: list[str] = []
    for idx, region in enumerate(regions):
        purpose = region.purpose or _default_purpose(doc_type, idx)
        try:
            template = load_prompt(f"auto-region/{purpose}")
        except FileNotFoundError as e:
            raise FrontmatterValidationError(
                f"未知の purpose です: {purpose!r}（region {idx}）。"
                " auto-marker-spec.md の purpose 一覧と"
                " agent/prompts/auto-region/ を確認してください。"
            ) from e
        prompt = render_prompt(
            template,
            {
                "source_url": source_url,
                "raw_content": raw_content,
                "existing_inner": "\n".join(region.inner_lines),
                "today": today,
                "claude_code_version": claude_code_version,
            },
        )
        prompts.append(prompt)
    return prompts


def regenerate_source(
    target_path: Path,
    vault_root: Path,
    fetcher: HttpFetcher | None = None,
    llm: LLMClient | None = None,
    claude_code_version: str | None = None,
    *,
    force: bool = False,
) -> RegenerateResult:
    if not target_path.exists():
        raise FileNotFoundError(f"target not found: {target_path}")
    target_path = target_path.resolve()
    vault_root = vault_root.resolve()

    existing_doc = parse(target_path.read_text(encoding="utf-8"))
    doc_type = existing_doc.metadata.get("type")
    if doc_type != "source":
        raise FrontmatterValidationError(
            f"regenerate は type=source のみ対象: {target_path}"
        )
    source_url = existing_doc.metadata.get("source_url")
    if not isinstance(source_url, str):
        raise FrontmatterValidationError(
            f"source_url が無い、または不正: {target_path}"
        )
    if existing_doc.metadata.get("auto_section_managed") is not True:
        raise FrontmatterValidationError(
            f"auto_section_managed=true 必須（ADR-017 / ADR-019）: {target_path}"
        )

    if fetcher is None:
        whitelist = load_whitelist(vault_root / "90_meta" / "sources.md")
        fetcher = HttpFetcher(whitelist)

    if llm is None:
        # 全バックエンド（Stub / Anthropic / ClaudeCode）は `generate` も `invoke` も
        # 実装するが Protocol の表現上は `LLMBackend` を返すため、`LLMClient` に cast。
        llm = cast(LLMClient, make_backend())

    fetch_result = fetcher.fetch(source_url)

    # content_hash 比較で更新要否を判定（force=True 指定時はスキップ）
    existing_hash = existing_doc.metadata.get("source_version")  # ETag を使い回し
    if (
        not force
        and existing_hash
        and existing_hash == fetch_result.source_version
    ):
        # 取込み元に変化なし。冪等性のため何も書き込まない。
        # 監査証跡として log.md には追記する。
        rel = target_path.relative_to(vault_root)
        append_log(vault_root, "regenerate", f"{rel} (no changes)")
        return RegenerateResult(
            article_path=target_path,
            write_result=WriteResult(
                file_path=target_path, changed=False, diff_summary="source unchanged"
            ),
        )

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    cc_version = str(
        claude_code_version
        or existing_doc.metadata.get("claude_code_version", "1.5.0")
    )

    regions = extract_auto_regions(target_path.read_text(encoding="utf-8"))
    if not regions:
        raise FrontmatterValidationError(
            f"auto_section_managed=true なのに AUTO 領域がありません: {target_path}"
        )

    prompts = _build_region_prompts(
        regions,
        doc_type=doc_type,
        source_url=source_url,
        raw_content=fetch_result.raw_content,
        today=today,
        claude_code_version=cc_version,
    )

    new_inner_contents: list[str] = []
    for idx, prompt in enumerate(prompts):
        generated = llm.generate(prompt)
        if not generated.strip():
            raise LLMGenerationError(
                f"LLM が AUTO 領域 {idx} に空応答を返しました"
            )
        new_inner_contents.append(generated.strip("\n"))

    # AUTO 領域を一括書き戻し（領域外バイト一致は replace_auto_regions が保証）
    replace_auto_regions(target_path, new_inner_contents)

    # frontmatter の機械的更新（last_updated / fetched_at / source_version / stale）
    refreshed_doc = parse(target_path.read_text(encoding="utf-8"))
    merged_meta = dict(refreshed_doc.metadata)
    merged_meta["fetched_at"] = fetch_result.fetched_at
    merged_meta["last_updated"] = today
    merged_meta["stale"] = False
    if fetch_result.source_version is not None:
        merged_meta["source_version"] = fetch_result.source_version
    final_doc = FrontmatterDocument(metadata=merged_meta, body=refreshed_doc.body)
    target_path.write_text(serialize(final_doc), encoding="utf-8")

    rel = target_path.relative_to(vault_root)
    append_log(
        vault_root,
        "regenerate",
        f"{rel} (AUTO regions, {len(prompts)} generated{', forced' if force else ''})",
    )
    return RegenerateResult(
        article_path=target_path,
        write_result=WriteResult(
            file_path=target_path,
            changed=True,
            diff_summary=f"AUTO regions regenerated: {len(prompts)} region(s)",
        ),
    )
