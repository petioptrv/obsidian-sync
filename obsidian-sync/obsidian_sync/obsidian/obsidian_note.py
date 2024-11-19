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
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.base_types.note import Note
from obsidian_sync.constants import MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH
from obsidian_sync.file_utils import clean_string_for_file_name
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_content import ObsidianNoteProperties, ObsidianNoteContent
from obsidian_sync.obsidian.obsidian_file import ObsidianNoteFile

if TYPE_CHECKING:  # avoid circular imports
    from obsidian_sync.obsidian.obsidian_vault import ObsidianVault


@dataclass
class ObsidianNote(Note):
    def __init__(
        self,
        addon_config: AddonConfig,
        obsidian_vault: "ObsidianVault",
        markup_translator: MarkupTranslator,
        file: Optional[ObsidianNoteFile] = None,
    ):
        self._file: Optional[ObsidianNoteFile] = file
        self._addon_config = addon_config
        self._obsidian_vault = obsidian_vault
        self._markup_translator = markup_translator

    @property
    def id(self) -> int:
        return self.content.properties.note_id

    @property
    def content(self) -> Optional[ObsidianNoteContent]:
        content = self._file.content if self._file is not None else None
        return content

    @property
    def file(self) -> Optional[ObsidianNoteFile]:
        return self._file

    @property
    def properties(self) -> ObsidianNoteProperties:
        return self._file.properties

    @classmethod
    def from_note(
        cls,
        note: Note,
        addon_config: AddonConfig,
        obsidian_vault: "ObsidianVault",
        markup_translator: MarkupTranslator,
    ) -> "ObsidianNote":
        obsidian_note = cls(
            addon_config=addon_config,
            obsidian_vault=obsidian_vault,
            markup_translator=markup_translator,
        )

        obsidian_note.update_with_note(note=note)

        return obsidian_note

    def update_with_note(self, note: Note):
        if self._file is None or self.is_corrupt():
            self._file is not None and self._file.delete()
            note_path = self._build_obsidian_note_path_from_note(note=note)
            self._file = ObsidianNoteFile(
                path=note_path,
                obsidian_vault=self._obsidian_vault,
                markup_translator=self._markup_translator,
            )
            if self._file.exists:
                self._file.delete()

        content_from_note = ObsidianNoteContent.from_content(
            content=note.content,
            obsidian_vault=self._obsidian_vault,
            markup_translator=self._markup_translator,
            note_path=self._file.path,
        )
        if self._file.content != content_from_note:
            self._file.content = content_from_note
            self._file.save()

    def is_corrupt(self) -> bool:
        corrupt = False

        if self._file is not None:
            try:
                assert self.content
            except Exception as e:
                corrupt = True

        return corrupt

    def delete(self):
        self._file.delete()

    def _build_obsidian_note_path_from_note(self, note: Note) -> Path:
        note_file_name = self._build_obsidian_note_file_name_from_note(note=note)
        note_path = self._addon_config.srs_folder / note_file_name
        return note_path

    @staticmethod
    def _build_obsidian_note_file_name_from_note(note: Note) -> str:
        suffix = ".md"
        max_file_name = MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH - len(suffix)
        file_name = note.content.fields[0].to_markdown() or note.content.properties.note_id
        file_name = clean_string_for_file_name(string=file_name)
        file_name = file_name[:max_file_name]
        file_name = f"{file_name}{suffix}"
        return file_name
