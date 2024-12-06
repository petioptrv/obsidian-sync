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

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.obsidian.content.field.obsidian_note_field import ObsidianNoteFieldFactory, ObsidianNoteField
from obsidian_sync.obsidian.content.field.obsidian_template_field import ObsidianTemplateFieldFactory, ObsidianTemplateField
from obsidian_sync.obsidian.content.obsidian_content import ObsidianContent, ObsidianNoteContent, ObsidianTemplateContent
from obsidian_sync.file_utils import check_is_markdown_file
from obsidian_sync.obsidian.content.obsidian_properties import ObsidianProperties, ObsidianTemplateProperties, \
    ObsidianNoteProperties
from obsidian_sync.obsidian.utils import obsidian_url_for_note_path


class ObsidianFile(ABC):
    def __init__(
        self,
        path: Path,
        addon_config: AddonConfig,
    ):
        assert check_is_markdown_file(path=path)

        self._path = path
        self._addon_config = addon_config

        self._raw_content = None
        self._content = None

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self.path == other.path
            and self.content == other.content
        )

    @property
    @abstractmethod
    def content(self) -> Optional[ObsidianContent]:
        ...

    @content.setter
    @abstractmethod
    def content(self, value: ObsidianContent):
        ...

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

    @raw_content.setter
    def raw_content(self, value: Optional[str]):
        self._raw_content = value

    @property
    def properties(self) -> ObsidianProperties:
        return self.content.properties

    @content.setter
    def content(self, value: ObsidianNoteContent):
        assert isinstance(value, ObsidianNoteContent)
        self._content = value

    @property
    def obsidian_url(self) -> str:
        obsidian_url = obsidian_url_for_note_path(
            vault_path=self._addon_config.obsidian_vault_path, note_path=self.path
        )
        return obsidian_url

    def is_corrupt(self) -> bool:
        corrupt = False

        try:
            assert self.content
        except Exception as e:
            corrupt = True

        return corrupt


class ObsidianTemplateFile(ObsidianFile):
    def __init__(
        self,
        path: Path,
        addon_config: AddonConfig,
        field_factory: ObsidianTemplateFieldFactory,
    ):
        super().__init__(path=path, addon_config=addon_config)
        self._field_factory = field_factory

    @property
    def properties(self) -> ObsidianTemplateProperties:
        return self.content.properties

    @property
    def content(self) -> Optional[ObsidianTemplateContent]:
        if self._content is None and self.raw_content is not None:
            self._content = ObsidianTemplateContent.from_obsidian_file_text(
                file_text=self.raw_content, field_factory=self._field_factory
            )
        return self._content

    @content.setter
    def content(self, value: ObsidianTemplateContent):
        assert isinstance(value, ObsidianTemplateContent)
        self._content = value

    @property
    def fields(self) -> List[ObsidianTemplateField]:
        return self.content.fields


class ObsidianNoteFile(ObsidianFile):
    def __init__(
        self,
        path: Path,
        addon_config: AddonConfig,
        field_factory: ObsidianNoteFieldFactory,
    ):
        super().__init__(path=path, addon_config=addon_config)
        self._field_factory = field_factory

    @property
    def properties(self) -> ObsidianNoteProperties:
        return self.content.properties

    @property
    def content(self) -> Optional[ObsidianNoteContent]:
        if self._content is None and self.raw_content is not None:
            self._content = ObsidianNoteContent.from_obsidian_file_text(
                file_text=self.raw_content,
                note_path=self._path,
                obsidian_field_factory=self._field_factory,
            )
        return self._content

    @content.setter
    def content(self, content: ObsidianNoteContent):
        self._content = content

    @property
    def fields(self) -> List[ObsidianNoteField]:
        return self.content.fields
