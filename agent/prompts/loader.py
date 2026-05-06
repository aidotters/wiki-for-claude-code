"""プロンプトテンプレートのロードと変数展開。"""

from __future__ import annotations

import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
_TEMPLATE_VAR = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def load_prompt(name: str) -> str:
    """`source-ingest`, `source-regenerate` 等のテンプレート文字列を取得する。"""
    candidates = [PROMPTS_DIR / f"{name}.md", PROMPTS_DIR / name]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt template not found: {name}")


def render_prompt(template: str, variables: dict[str, str]) -> str:
    """`{{key}}` 形式の変数を置換する。

    - 定義済み変数は値で置換
    - 未定義変数は空文字列に展開（テンプレート崩壊を避ける）
    """

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(variables.get(key, ""))

    return _TEMPLATE_VAR.sub(_replace, template)
