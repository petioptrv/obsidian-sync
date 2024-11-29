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
from typing import List, Optional

from obsidian_sync.obsidian.content.obsidian_content import ObsidianTemplateContent
from obsidian_sync.obsidian.content.field.obsidian_field import ObsidianField
from obsidian_sync.obsidian.content.obsidian_properties import ObsidianTemplateProperties
from obsidian_sync.obsidian.obsidian_file import ObsidianTemplateFile
from obsidian_sync.base_types.template import Template


@dataclass
class ObsidianTemplate(Template):
    def __init__(
        self,
        file: Optional[ObsidianTemplateFile] = None,
    ):
        self._file: Optional[ObsidianTemplateFile] = file

    @property
    def content(self) -> Optional[ObsidianTemplateContent]:
        content = self._file.content if self._file is not None else None
        return content

    @property
    def model_name(self) -> str:
        return self._file.properties.model_name

    @property
    def file(self) -> Optional[ObsidianTemplateFile]:
        return self._file

    @file.setter
    def file(self, file: ObsidianTemplateFile):
        self._file = file

    @property
    def properties(self) -> ObsidianTemplateProperties:
        return self._file.properties

    @property
    def fields(self) -> List[ObsidianField]:
        return self._file.fields

    def is_corrupt(self) -> bool:
        return self.file.is_corrupt()
