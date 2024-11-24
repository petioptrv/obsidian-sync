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
from obsidian_sync.obsidian.attachments_manager import ObsidianAttachmentsManager
from obsidian_sync.obsidian.content.content import ObsidianContent, ObsidianNoteContent, ObsidianTemplateContent
from obsidian_sync.obsidian.content.field.field import ObsidianField
from obsidian_sync.file_utils import check_is_markdown_file
from obsidian_sync.obsidian.content.properties import ObsidianProperties, ObsidianTemplateProperties, \
    ObsidianNoteProperties


class ObsidianFile(ABC):
    def __init__(
        self,
        path: Path,
        attachment_manager: ObsidianAttachmentsManager,
        addon_config: AddonConfig,
    ):
        assert check_is_markdown_file(path=path)

        self._path = path
        self._attachments_manager = attachment_manager
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

    @content.setter
    def content(self, value: ObsidianNoteContent):
        assert isinstance(value, ObsidianNoteContent)
        self._content = value

    def is_corrupt(self) -> bool:
        corrupt = False

        try:
            assert self.content
        except Exception:
            corrupt = True

        return corrupt


class ObsidianTemplateFile(ObsidianFile):
    @property
    def properties(self) -> ObsidianTemplateProperties:
        return self.content.properties

    @property
    def content(self) -> Optional[ObsidianTemplateContent]:
        if self._content is None and self.raw_content is not None:
            self._content = ObsidianTemplateContent.from_obsidian_file_text(
                file_text=self.raw_content, addon_config=self._addon_config
            )
        return self._content

    @content.setter
    def content(self, value: ObsidianTemplateContent):
        assert isinstance(value, ObsidianTemplateContent)
        self._content = value


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
                obsidian_attachments_manager=self._attachments_manager,
                addon_config=self._addon_config,
            )
        return self._content

    @content.setter
    def content(self, content: ObsidianNoteContent):
        self._content = content
