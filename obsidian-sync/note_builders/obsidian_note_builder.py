import os
from pathlib import Path

from ..utils import get_field_title_format_string
from ..markup_converter import MarkupConverter
from ..config_handler import ConfigHandler
from ..constants import DECK_NAME_SEPARATOR


class ObsidianNoteBuilder:
    def __init__(self, config_handler: ConfigHandler, markup_converter: MarkupConverter):
        self._config_handler = config_handler
        self._markup_converter = markup_converter

    def build_field_title(self, field_name: str) -> str:
        field_format_string = get_field_title_format_string(
            html_header_tag=self._config_handler.field_name_header_tag
        )
        field_title = field_format_string.format(field=field_name)
        return field_title

    def build_obsidian_note_folder_path_from_deck(self, deck: str) -> Path:
        relative_path_str = deck.replace(DECK_NAME_SEPARATOR, os.path.sep)
        relative_path = Path(self._config_handler.anki_folder / relative_path_str)
        return relative_path
