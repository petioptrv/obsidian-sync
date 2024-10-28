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
from typing import List, Set, Tuple

from ..constants import SRS_NOTE_IDENTIFIER_PROPERTY_NAME, MODEL_ID_PROPERTY_NAME, NOTE_ID_PROPERTY_NAME, \
    TAGS_PROPERTY_NAME, DATE_MODIFIED_PROPERTY_NAME, DATETIME_FORMAT, SRS_NOTE_FIELD_IDENTIFIER_COMMENT, \
    DATE_SYNCED_PROPERTY_NAME, DECK_NAME_SEPARATOR
from ..markup_translator import MarkupTranslator


class ObsidianNoteParser:
    def __init__(self, config_handler: ConfigHandler, note_converter: MarkupTranslator):
        self._config_handler = config_handler
        self._note_converter = note_converter

    def parse_deck_from_obsidian_note_path(self, file_path: Path) -> str:
        relative_path = Path(os.path.relpath(path=file_path, start=self._config_handler.srs_folder_in_obsidian))
        deck_name = str(relative_path.parent).replace(os.path.sep, DECK_NAME_SEPARATOR)
        return deck_name

    def get_model_id_from_obsidian_note_content(self, content: str) -> int:
        model_id_str = self._get_note_property(property_name=MODEL_ID_PROPERTY_NAME, content=content)
        return int(model_id_str)

    def get_note_id_from_obsidian_note_content(self, content: str) -> int:
        note_id = self._get_note_property(property_name=NOTE_ID_PROPERTY_NAME, content=content)
        return int(note_id)

    def get_field_names_text_and_images_from_obsidian_note_content(
        self, content: str
    ) -> List[Tuple[str, str, List[Path]]]:
        note_body = self._get_note_body(content=content)
        field_names_and_text = self._extract_headers_and_paragraphs(note_body=note_body)
        field_names_text_and_images = [
            (name, text, self._extract_obsidian_image_paths_from_field_text(field_text=text))
            for name, text in field_names_and_text
        ]
        return field_names_text_and_images

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

    def _extract_obsidian_image_paths_from_field_text(self, field_text: str) -> List[Path]:

        return []
