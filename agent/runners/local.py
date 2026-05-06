"""ローカル CLI ランナー。

スラッシュコマンド `/wiki-*` から sub-process として呼ばれる薄いラッパ。
終了コード:
  0 = 成功
  1 = 検証エラー
  2 = 取得エラー / ホワイトリスト外
  3 = LLM エラー
  4 = lint 違反
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent.errors import (
    EXIT_FETCH,
    EXIT_LINT,
    EXIT_LLM,
    EXIT_OK,
    EXIT_VALIDATION,
    FetchFailedError,
    FrontmatterValidationError,
    LLMGenerationError,
    SourceNotWhitelistedError,
)


def _default_vault_root() -> Path:
    """カレントディレクトリから vault/ を探す。"""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / "vault" / "90_meta").is_dir():
            return parent / "vault"
    return cwd / "vault"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent",
        description="LLM-Wiki for Claude Code: agent CLI",
    )
    parser.add_argument(
        "--vault-root",
        type=Path,
        default=None,
        help="vault ディレクトリ（既定: カレントから自動探索）",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="新ソース取込み")
    p_ingest.add_argument("--source-url", required=True)
    p_ingest.add_argument(
        "--category",
        required=True,
        choices=["hooks", "cli", "slash-commands", "mcp", "settings", "sdk"],
    )
    p_ingest.add_argument("--claude-code-version", default="1.5.0")

    p_regen = sub.add_parser("regenerate", help="既存ページの再生成")
    p_regen.add_argument("--target", required=True, type=Path)

    p_lint = sub.add_parser("lint", help="lint 検査")
    p_lint.add_argument("--all", action="store_true")

    p_validate = sub.add_parser("validate", help="機械的検証")
    p_validate.add_argument("--all", action="store_true")
    p_validate.add_argument("--target", type=Path, default=None)

    p_verify = sub.add_parser(
        "verify-links",
        help="source_url の HTTP 到達確認 + 連続100文字一致検査（ネットワーク依存）",
    )
    p_verify.add_argument("--target", type=Path, default=None)
    p_verify.add_argument(
        "--no-transclusion",
        action="store_true",
        help="transclusion 検査を省略し HEAD 到達確認のみ実施",
    )

    return parser


def _cmd_ingest(args: argparse.Namespace, vault_root: Path) -> int:
    from agent.orchestration.ingest import ingest_source

    try:
        result = ingest_source(
            source_url=args.source_url,
            category=args.category,
            vault_root=vault_root,
            claude_code_version=args.claude_code_version,
        )
    except SourceNotWhitelistedError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_FETCH
    except FetchFailedError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_FETCH
    except LLMGenerationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_LLM
    except (ValueError, FileExistsError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_VALIDATION

    print(f"Ingested: {result.article_path} (changed={result.write_result.changed})")
    return EXIT_OK


def _cmd_regenerate(args: argparse.Namespace, vault_root: Path) -> int:
    from agent.orchestration.regenerate import regenerate_source

    try:
        result = regenerate_source(args.target, vault_root=vault_root)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_VALIDATION
    except FrontmatterValidationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_VALIDATION
    except SourceNotWhitelistedError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_FETCH
    except FetchFailedError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_FETCH
    except LLMGenerationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_LLM

    state = "updated" if result.write_result.changed else "no changes"
    print(f"Regenerated: {result.article_path} ({state})")
    return EXIT_OK


def _cmd_lint(args: argparse.Namespace, vault_root: Path) -> int:
    from agent.orchestration.lint import lint_all

    report = lint_all(vault_root)
    print(report.format())
    return EXIT_LINT if report.total_violations > 0 else EXIT_OK


def _cmd_validate(args: argparse.Namespace, vault_root: Path) -> int:
    from agent.orchestration.validate import validate_all, validate_target

    if args.target:
        summary = validate_target(args.target, vault_root=vault_root)
    else:
        summary = validate_all(vault_root)
    print(summary.format())
    return EXIT_OK if summary.passed else EXIT_VALIDATION


def _cmd_verify_links(args: argparse.Namespace, vault_root: Path) -> int:
    from agent.orchestration.verify_links import verify_links

    try:
        summary = verify_links(
            vault_root=vault_root,
            target=args.target,
            check_transclusion=not args.no_transclusion,
        )
    except (SourceNotWhitelistedError, FetchFailedError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_FETCH
    print(summary.format())
    return EXIT_OK if summary.passed else EXIT_VALIDATION


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    vault_root = args.vault_root or _default_vault_root()

    if args.command == "ingest":
        return _cmd_ingest(args, vault_root)
    if args.command == "regenerate":
        return _cmd_regenerate(args, vault_root)
    if args.command == "lint":
        return _cmd_lint(args, vault_root)
    if args.command == "validate":
        return _cmd_validate(args, vault_root)
    if args.command == "verify-links":
        return _cmd_verify_links(args, vault_root)
    parser.print_help()
    return EXIT_VALIDATION


if __name__ == "__main__":
    sys.exit(main())
