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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_content import ObsidianContent, ObsidianField, ObsidianNoteContent, ObsidianTemplateContent, \
    ObsidianTemplateProperties, ObsidianNoteProperties
from obsidian_sync.file_utils import check_is_markdown_file
from obsidian_sync.obsidian.obsidian_content import ObsidianProperties

if TYPE_CHECKING:  # avoids circular imports
    from obsidian_sync.obsidian.obsidian_vault import ObsidianVault


class ObsidianFile(ABC):
    def __init__(
        self,
        path: Path,
        obsidian_vault: "ObsidianVault",
        markup_translator: MarkupTranslator,
    ):
        assert check_is_markdown_file(path=path)

        self._path = path
        self._obsidian_vault = obsidian_vault
        self._markup_translator = markup_translator

        self._raw_content = None
        self._content = None

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self.path == other.path
            and self.content == other.content
        )

    @property
    def exists(self) -> bool:
        return self._path.exists()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def raw_content(self) -> Optional[str]:
        if self._raw_content is None and self.path.exists():
            self._raw_content = self.path.read_text(encoding="utf-8")
        return self._raw_content

    @property
    @abstractmethod
    def content(self) -> Optional[ObsidianContent]:
        ...

    @content.setter
    @abstractmethod
    def content(self, value: ObsidianContent):
        ...

    @property
    def properties(self) -> ObsidianProperties:
        return self.content.properties

    @property
    def fields(self) -> List[ObsidianField]:
        return self.content.fields

    def save(self):
        file_text = self.content.to_obsidian_file_text()

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(file_text, encoding="utf-8")

    def delete(self):
        self._obsidian_vault.delete_file(file_path=self.path)


class ObsidianNoteFile(ObsidianFile):
    @property
    def properties(self) -> ObsidianNoteProperties:
        return self.content.properties

    @property
    def content(self) -> Optional[ObsidianNoteContent]:
        if self._content is None and self.raw_content is not None:
            self._content = ObsidianNoteContent.from_obsidian_file_text(
                file_text=self.raw_content,
                note_path=self._path,
                obsidian_attachments_manager=self._obsidian_vault.attachments_manager,
                markup_translator=self._markup_translator,
            )
        return self._content

    @content.setter
    def content(self, value: ObsidianNoteContent):
        assert isinstance(value, ObsidianNoteContent)
        self._content = value


class ObsidianTemplateFile(ObsidianFile):
    @property
    def properties(self) -> ObsidianTemplateProperties:
        return self.content.properties

    @property
    def content(self) -> Optional[ObsidianTemplateContent]:
        if self._content is None and self.raw_content is not None:
            self._content = ObsidianTemplateContent.from_obsidian_file_text(
                file_text=self.raw_content,
                note_path=self._path,
                obsidian_attachments_manager=self._obsidian_vault.attachments_manager,
                markup_translator=self._markup_translator,
            )
        return self._content

    @content.setter
    def content(self, value: ObsidianTemplateContent):
        assert isinstance(value, ObsidianTemplateContent)
        self._content = value
