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
from typing import List, Optional

from obsidian_sync.constants import MARKDOWN_FILE_SUFFIX
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_content import ObsidianField, ObsidianTemplateContent, ObsidianTemplateProperties
from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.obsidian.obsidian_file import ObsidianTemplateFile
from obsidian_sync.template import Template


class ObsidianTemplate(Template):
    def __init__(
        self,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
        markup_translator: MarkupTranslator,
        file: Optional[ObsidianTemplateFile] = None,
    ):
        self._file: Optional[ObsidianTemplateFile] = file
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        self._markup_translator = markup_translator

    @property
    def model_name(self) -> str:
        return self._file.path.stem

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
        obsidian_config: ObsidianConfig,
        markup_translator: MarkupTranslator,
    ) -> "ObsidianTemplate":
        obsidian_template = ObsidianTemplate(
            addon_config=addon_config,
            obsidian_config=obsidian_config,
            markup_translator=markup_translator,
        )

        obsidian_template.update_with_template(template=template)

        return obsidian_template

    def update_with_template(self, template: Template):
        if self._file is None or f"{template.model_name}.{MARKDOWN_FILE_SUFFIX}" != self._file.name:
            template_path = self._obsidian_config.templates_folder / f"{template.model_name}.{MARKDOWN_FILE_SUFFIX}"
            self._file is not None and self._file.delete()
            self._file = ObsidianTemplateFile(
                path=template_path,
                addon_config=self._addon_config,
                obsidian_config=self._obsidian_config,
                markup_translator=self._markup_translator,
            )

        content_from_anki_template = ObsidianTemplateContent.from_template(
            template=template,
            obsidian_config=self._obsidian_config,
            markup_translator=self._markup_translator
        )
        if self._file.content != content_from_anki_template:
            self._file.content = content_from_anki_template
            self._file.save()

    def delete(self):
        self._file.delete()
