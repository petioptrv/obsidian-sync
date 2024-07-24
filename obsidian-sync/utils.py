from pathlib import Path

from .constants import ADD_ON_NAME


def format_add_on_message(message: str) -> str:
    return f"[{ADD_ON_NAME}] {message}"


def is_markdown_file(path: Path) -> bool:
    return path.suffix == ".md"
