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
from typing import List, Optional

from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_content import ObsidianContent, ObsidianField, ObsidianNoteContent, ObsidianTemplateContent, \
    ObsidianTemplateProperties, ObsidianNoteProperties
from obsidian_sync.file_utils import check_is_markdown_file, move_file_to_system_trash
from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.constants import (
    OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE, OBSIDIAN_LOCAL_TRASH_OPTION_VALUE,
    OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE, OBSIDIAN_LOCAL_TRASH_FOLDER,
)
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_content import ObsidianProperties


class ObsidianFile(ABC):
    def __init__(
        self,
        path: Path,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
        markup_translator: MarkupTranslator,
    ):
        assert check_is_markdown_file(path=path)

        self._path = path
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
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
        """No need to delete linked resources (images, etc.). We don't know if the resource
        is linked to by other notes and deleting a file in obsidian does not delete the linked
        resources either."""
        trash_option = self._obsidian_config.trash_option

        if trash_option is None or trash_option == OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE:
            move_file_to_system_trash(file_path=self._path)
        elif trash_option == OBSIDIAN_LOCAL_TRASH_OPTION_VALUE:
            self._move_to_local_trash()
        elif trash_option == OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE:
            self.path.unlink()
        else:
            raise NotImplementedError  # unrecognized delete option

    def _move_to_local_trash(self):
        trash_folder = self._addon_config.obsidian_vault_path / OBSIDIAN_LOCAL_TRASH_FOLDER

        trash_folder.mkdir(parents=True, exist_ok=True)

        new_file_path = trash_folder / self.name

        self.path.rename(new_file_path)


class ObsidianNoteFile(ObsidianFile):
    @property
    def properties(self) -> ObsidianNoteProperties:
        return self.content.properties

    @property
    def content(self) -> Optional[ObsidianNoteContent]:
        if self._content is None and self.raw_content is not None:
            self._content = ObsidianNoteContent.from_obsidian_file_text(
                file_text=self.raw_content, markup_translator=self._markup_translator
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
                file_text=self.raw_content, markup_translator=self._markup_translator
            )
        return self._content

    @content.setter
    def content(self, value: ObsidianTemplateContent):
        assert isinstance(value, ObsidianTemplateContent)
        self._content = value
