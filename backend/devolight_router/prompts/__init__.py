from pathlib import Path
from typing import Dict


_CACHE: Dict[str, str] = {}


def _prompts_root() -> Path:
    """Return project-level prompts directory."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "prompts"
        if candidate.exists() and any(child.suffix == ".md" for child in candidate.iterdir()):
            return candidate
    raise FileNotFoundError("未找到提示词目录 prompts，请确认项目结构。")


def load_prompt(name: str) -> str:
    """Load a prompt by filename (without extension)."""
    if name in _CACHE:
        return _CACHE[name]
    path = _prompts_root() / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"找不到提示词文件: {path}")
    content = path.read_text(encoding="utf-8")
    _CACHE[name] = content
    return content
