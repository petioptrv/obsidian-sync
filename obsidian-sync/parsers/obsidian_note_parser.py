# -*- coding: utf-8 -*-
# Obsidian Sync Add-on for Anki
#
# Copyright (C)  2024 Petrov P.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <mailto:petioptrv@icloud.com>.
#
# Any modifications to this file must keep this entire header intact.
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Set

from ..utils import get_field_title_format_string
from ..constants import ANKI_NOTE_IDENTIFIER_PROPERTY_NAME, MODEL_ID_PROPERTY_NAME, NOTE_ID_PROPERTY_NAME, \
    TAGS_PROPERTY_NAME, DATE_MODIFIED_PROPERTY_NAME, DATETIME_FORMAT, ANKI_NOTE_FIELD_IDENTIFIER_COMMENT, \
    DATE_SYNCED_PROPERTY_NAME, DECK_NAME_SEPARATOR
from ..config_handler import ConfigHandler
from ..markup_converter import MarkupConverter


class ObsidianNoteParser:
    def __init__(self, config_handler: ConfigHandler, note_converter: MarkupConverter):
        self._config_handler = config_handler
        self._note_converter = note_converter

    def is_anki_note_in_obsidian(self, note_content: str) -> bool:
        property_value = self._config_handler.anki_note_in_obsidian_property_value
        pattern = (
            rf"^---\s*(?:.*\n)*?{re.escape(ANKI_NOTE_IDENTIFIER_PROPERTY_NAME)}\s*:\s*{re.escape(property_value)}\s*(?:.*\n)*?---"
        )
        return re.match(pattern, note_content) is not None

    def parse_deck_from_obsidian_note_path(self, file_path: Path) -> str:
        relative_path = Path(os.path.relpath(path=file_path, start=self._config_handler.anki_folder_in_obsidian))
        deck_name = str(relative_path.parent).replace(os.path.sep, DECK_NAME_SEPARATOR)
        return deck_name

    def get_model_id_from_obsidian_note_content(self, content: str) -> int:
        model_id_str = self._get_note_property(property_name=MODEL_ID_PROPERTY_NAME, content=content)
        return int(model_id_str)

    def get_note_id_from_obsidian_note_content(self, content: str) -> int:
        note_id = self._get_note_property(property_name=NOTE_ID_PROPERTY_NAME, content=content)
        return int(note_id)

    def get_fields_from_obsidian_note_content(self, content: str) -> List[str]:
        note_body = self._get_note_body(content=content)
        fields = self._extract_paragraphs_after_headers(note_body=note_body)
        return fields

    def get_tags_from_obsidian_note_content(self, content: str) -> Set[str]:
        tags = self._get_note_property(property_name=TAGS_PROPERTY_NAME, content=content)
        return set(tags)

    def get_modified_dt(self, content: str) -> datetime:
        modified_dt = datetime.strptime(
            self._get_note_property(property_name=DATE_MODIFIED_PROPERTY_NAME, content=content),
            DATETIME_FORMAT,
        )
        return modified_dt

    def get_synced_dt(self, content: str) -> datetime:
        synced_dt_str = self._get_note_property(property_name=DATE_SYNCED_PROPERTY_NAME, content=content)
        if synced_dt_str:
            synced_dt = datetime.strptime(
                self._get_note_property(property_name=DATE_SYNCED_PROPERTY_NAME, content=content),
                DATETIME_FORMAT,
            )
        else:
            synced_dt = datetime.now()
        return synced_dt

    def _get_note_property(self, property_name: str, content: str) -> any:
        properties_content = self._get_note_properties(content=content)

        if property_name == TAGS_PROPERTY_NAME:
            tags_match = re.findall(r"\n\s*-\s*(.+)", properties_content)
            value = [tag.strip() for tag in tags_match if tag.strip()]
        else:
            value_pattern = rf"{property_name}:[ \t]*(.+)"
            value_match = re.search(value_pattern, properties_content)

            if value_match:
                value = value_match.group(1).strip()
            else:
                raise ValueError(f"No property {property_name} found.")

        return value

    @staticmethod
    def _get_note_properties(content: str) -> str:
        pattern = r"^---\n(.*?\n)---\n(.*)$"
        match = re.search(pattern=pattern, string=content, flags=re.DOTALL)
        return match.group(1)

    @staticmethod
    def _get_note_body(content: str) -> str:
        pattern = r"^---\n(.*?\n)---\n(.*)$"
        match = re.search(pattern=pattern, string=content, flags=re.DOTALL)
        return match.group(2)

    def _extract_paragraphs_after_headers(self, note_body: str) -> List[str]:
        pattern = self._build_field_title_matcher()
        pattern += f"([\s\S]*?)(?={ANKI_NOTE_FIELD_IDENTIFIER_COMMENT}|\Z)"
        matches = re.findall(pattern, note_body, re.DOTALL)
        result = [para.strip() if para else "" for header, para in matches]
        return result

    def _build_field_title_matcher(self) -> str:
        field_format_string = get_field_title_format_string(
            html_header_tag=self._config_handler.field_name_header_tag
        )
        pattern = field_format_string.format(field="(.*?)")
        return pattern
