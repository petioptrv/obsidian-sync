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
from typing import Optional

from obsidian_sync.base_types.note import Note
from obsidian_sync.constants import DEFAULT_NOTE_ID_FOR_NEW_NOTES
from obsidian_sync.obsidian.content.obsidian_content import ObsidianNoteContent
from obsidian_sync.obsidian.content.obsidian_properties import ObsidianNoteProperties
from obsidian_sync.obsidian.obsidian_file import ObsidianNoteFile


@dataclass
class ObsidianNote(Note):
    def __init__(
        self,
        file: Optional[ObsidianNoteFile] = None,
        note_id: Optional[int] = None,
    ):
        self._file: Optional[ObsidianNoteFile] = file
        self._note_id: Optional[int] = note_id

    @property
    def id(self) -> int:
        if self._note_id is None:
            self._note_id = self.content.properties.note_id
        return self.content.properties.note_id

    @property
    def content(self) -> Optional[ObsidianNoteContent]:
        content = self._file.content if self._file is not None else None
        return content

    @property
    def file(self) -> Optional[ObsidianNoteFile]:
        return self._file

    @file.setter
    def file(self, file: ObsidianNoteFile):
        self._file = file

    @property
    def properties(self) -> ObsidianNoteProperties:
        return self._file.properties

    @property
    def obsidian_url(self) -> str:
        return self._file.obsidian_url

    def is_new(self) -> bool:
        return self._file is None or self.id == DEFAULT_NOTE_ID_FOR_NEW_NOTES

    def is_corrupt(self) -> bool:
        return self._file.is_corrupt()
