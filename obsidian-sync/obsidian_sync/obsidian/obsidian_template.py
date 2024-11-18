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
from typing import List, Optional, TYPE_CHECKING

from obsidian_sync.constants import MARKDOWN_FILE_SUFFIX
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_content import ObsidianField, ObsidianTemplateContent, ObsidianTemplateProperties
from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.obsidian.obsidian_file import ObsidianTemplateFile
from obsidian_sync.base_types.template import Template

if TYPE_CHECKING:  # avoids circular imports
    from obsidian_sync.obsidian.obsidian_vault import ObsidianVault


@dataclass
class ObsidianTemplate(Template):
    def __init__(
        self,
        addon_config: AddonConfig,
        obsidian_vault: "ObsidianVault",
        markup_translator: MarkupTranslator,
        file: Optional[ObsidianTemplateFile] = None,
    ):
        self._file: Optional[ObsidianTemplateFile] = file
        self._addon_config = addon_config
        self._obsidian_vault = obsidian_vault
        self._markup_translator = markup_translator

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

    @property
    def properties(self) -> ObsidianTemplateProperties:
        return self._file.properties

    @property
    def fields(self) -> List[ObsidianField]:
        return self._file.fields

    @classmethod
    def from_template(
        cls,
        template: Template,
        addon_config: AddonConfig,
        obsidian_vault: "ObsidianVault",
        markup_translator: MarkupTranslator,
    ) -> "ObsidianTemplate":
        obsidian_template = cls(
            addon_config=addon_config,
            obsidian_vault=obsidian_vault,
            markup_translator=markup_translator,
        )

        obsidian_template.update_with_template(template=template)

        return obsidian_template

    def update_with_template(self, template: Template):
        if (
            self._file is None
            or f"{template.content.properties.model_name}{MARKDOWN_FILE_SUFFIX}" != self._file.name
            or self.is_corrupt()
        ):
            self._file is not None and self._file.delete()
            self._file = self._obsidian_vault.build_template_file_for_model(
                model_name=template.content.properties.model_name
            )
            self._file.exists and self._file.delete()

        content_from_template = ObsidianTemplateContent.from_content(
            content=template.content,
            obsidian_vault=self._obsidian_vault,
            markup_translator=self._markup_translator
        )
        if self._file.content != content_from_template:
            self._file.content = content_from_template
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
