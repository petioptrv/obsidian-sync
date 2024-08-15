import json
from pathlib import Path
from typing import List

from aqt import mw

from .constants import ADD_ON_NAME, TEMPLATES_FOLDER_JSON_FIELD_NAME, ANKI_NOTE_FIELD_IDENTIFIER_COMMENT


def format_add_on_message(message: str) -> str:
    return f"[{ADD_ON_NAME}] {message}"


def is_markdown_file(path: Path) -> bool:
    return path.suffix == ".md"


def get_templates_folder_path(obsidian_vault: Path) -> Path:
    templates_json_path = obsidian_vault / ".obsidian" / "templates.json"

    if not templates_json_path.is_file():
        raise RuntimeError("The templates core plugin is not enabled.")

    with open(templates_json_path, "r") as f:
        templates_json = json.load(f)
        templates_path = obsidian_vault / templates_json[TEMPLATES_FOLDER_JSON_FIELD_NAME]

    return templates_path


def get_field_title_format_string(html_header_tag: str) -> str:
    field_string = f"{ANKI_NOTE_FIELD_IDENTIFIER_COMMENT}\n<{html_header_tag}>{{field}}</{html_header_tag}>"
    return field_string


def get_field_names_from_anki_model_id(id: int) -> List[str]:
    model = mw.col.models.get(id=id)
    field_names = mw.col.models.field_names(model)
    return field_names


def move_obsidian_note_to_trash_folder(obsidian_vault: Path, obsidian_note_path: Path):
    obsidian_note_path.unlink()
    # todo: implement
