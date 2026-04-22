"""Prompt 模板加载器 — 支持热加载,改完 .md 不需要重启。"""
from pathlib import Path
from functools import lru_cache

_DIR = Path(__file__).parent / "system"


def load(name: str) -> str:
    """name 不含 .md 后缀。"""
    path = _DIR / f"{name}.md"
    if not path.exists():
        return f"You are the {name} agent. Analyze the given context and respond in JSON."
    return path.read_text(encoding="utf-8")


def list_prompts() -> list[str]:
    return [p.stem for p in _DIR.glob("*.md")]
