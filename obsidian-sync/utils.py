import json
import re
from pathlib import Path
from string import ascii_letters, digits

from .send2trash import send2trash
from .constants import ADD_ON_NAME, ANKI_NOTE_FIELD_IDENTIFIER_COMMENT, \
    OBSIDIAN_TRASH_OPTION_KEY, OBSIDIAN_LOCAL_TRASH_OPTION_VALUE, OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE, \
    OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE, MARKDOWN_FILE_SUFFIX, OBSIDIAN_SETTINGS_FOLDER, \
    OBSIDIAN_APP_SETTINGS_FILE, OBSIDIAN_LOCAL_TRASH_FOLDER


def format_add_on_message(message: str) -> str:
    return f"[{ADD_ON_NAME}] {message}"


def is_markdown_file(path: Path) -> bool:
    return path.suffix == MARKDOWN_FILE_SUFFIX


def get_field_title_format_string(html_header_tag: str) -> str:
    field_string = f"{ANKI_NOTE_FIELD_IDENTIFIER_COMMENT}\n<{html_header_tag}>{{field}}</{html_header_tag}>"
    return field_string


def clean_string_for_file_name(string: str) -> str:
    cloze_pattern = r"\{\{c\d+::(.*?)\}\}"
    string = re.sub(cloze_pattern, r"\1", string)  # remove cloze markers
    valid_chars = "-_.() %s%s" % (ascii_letters, digits)
    return "".join(c for c in string if c in valid_chars)


def delete_obsidian_note(obsidian_vault: Path, obsidian_note_path: Path):
    trash_option = get_obsidian_trash_option(obsidian_vault=obsidian_vault)

    if trash_option is None or trash_option == OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE:
        _move_to_system_trash(obsidian_note_path=obsidian_note_path)
    elif trash_option == OBSIDIAN_LOCAL_TRASH_OPTION_VALUE:
        _move_to_local_trash(obsidian_vault=obsidian_vault, obsidian_note_path=obsidian_note_path)
    elif trash_option == OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE:
        obsidian_note_path.unlink()


def get_obsidian_trash_option(obsidian_vault: Path) -> str:
    with open(obsidian_vault / OBSIDIAN_SETTINGS_FOLDER / OBSIDIAN_APP_SETTINGS_FILE, "r") as f:
        settings = json.load(f)

    trash_option = settings.get(OBSIDIAN_TRASH_OPTION_KEY)

    return trash_option


def get_obsidian_trash_folder(obsidian_vault: Path) -> Path:
    trash_folder = obsidian_vault / OBSIDIAN_LOCAL_TRASH_FOLDER

    trash_folder.mkdir(parents=True, exist_ok=True)

    return trash_folder


def _move_to_system_trash(obsidian_note_path: Path):
    send2trash.send2trash(paths=obsidian_note_path)


def _move_to_local_trash(obsidian_vault: Path, obsidian_note_path: Path):
    trash_folder = obsidian_vault / OBSIDIAN_LOCAL_TRASH_FOLDER

    trash_folder.mkdir(parents=True, exist_ok=True)

    new_file_path = trash_folder / obsidian_note_path.name

    obsidian_note_path.rename(new_file_path)
