from .constants import ADD_ON_NAME


def format_add_on_message(message: str) -> str:
    return f"[{ADD_ON_NAME}] {message}"
