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

import logging
from typing import Dict, Generator

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.anki.app.anki_app import AnkiApp
from obsidian_sync.base_types.template import Template
from obsidian_sync.constants import MARKDOWN_FILE_SUFFIX
from obsidian_sync.file_utils import check_is_srs_file
from obsidian_sync.obsidian.config import ObsidianConfig
from obsidian_sync.obsidian.content.obsidian_content import ObsidianTemplateContent
from obsidian_sync.obsidian.content.field.obsidian_template_field import ObsidianTemplateFieldFactory
from obsidian_sync.obsidian.file import ObsidianTemplateFile
from obsidian_sync.obsidian.obsidian_template import ObsidianTemplate
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.utils import format_add_on_message


class ObsidianTemplatesManager:
    def __init__(
        self,
        anki_app: AnkiApp,
        obsidian_config: ObsidianConfig,
        obsidian_vault: ObsidianVault,
        addon_config: AddonConfig,
    ):
        self._anki_app = anki_app
        self._obsidian_config = obsidian_config
        self._obsidian_vault = obsidian_vault
        self._addon_config = addon_config
        self._field_factory = ObsidianTemplateFieldFactory(
            addon_config=addon_config,
        )

    def create_obsidian_template_from_template(self, reference_template: Template) -> ObsidianTemplate:
        obsidian_template = ObsidianTemplate()
        obsidian_template = self.update_obsidian_template_with_template(
            obsidian_template=obsidian_template, reference_template=reference_template
        )
        return obsidian_template

    def update_obsidian_template_with_template(
        self, obsidian_template: ObsidianTemplate, reference_template: Template
    ) -> ObsidianTemplate:
        file = obsidian_template.file

        if (
            file is None
            or f"{reference_template.content.properties.model_name}{MARKDOWN_FILE_SUFFIX}" != file.name
            or file.is_corrupt()
        ):
            if file is not None:
                self._obsidian_vault.delete_file(file=file)
            file = self._build_template_file_for_model(
                model_name=reference_template.content.properties.model_name
            )
            if file.exists:
                self._obsidian_vault.delete_file(file=file)

        content_from_template = ObsidianTemplateContent.from_content(
            content=reference_template.content, field_factory=self._field_factory
        )
        if file.content != content_from_template:
            file.content = content_from_template
            self._obsidian_vault.save_file(file=file)

        obsidian_template.file = file

        return obsidian_template

    def get_all_obsidian_templates(self) -> Dict[int, ObsidianTemplate]:
        self._obsidian_config.templates_folder.mkdir(parents=True, exist_ok=True)
        templates = {}

        for template_file in self._get_srs_template_files_in_obsidian():
            try:
                template = ObsidianTemplate(
                    file=template_file,
                )
            except Exception:
                logging.exception(f"Failed to sync note template {template_file.path}.")
                self._anki_app.show_critical(
                    text=format_add_on_message(f"Failed to sync note template {template_file.path}."),
                    title="Failed to sync template",
                )
            else:
                if template.is_corrupt():
                    logging.error(f"Failed to load corrupted template file {template_file.path}.")
                    self.delete_template(template=template)
                else:
                    if template.properties.model_id in templates:
                        self._anki_app.show_critical(
                            text=format_add_on_message(
                                f"Duplicate Anki note templates found (model ID {template.properties.model_id}) with"
                                f" names {templates[template.properties.model_id].file.name} and {template_file.name}."
                                f" Only synchronizing {template_file.name}."
                            ),
                            title="Duplicate Anki note templates",
                        )
                    templates[template.properties.model_id] = template

        return templates

    def delete_template(self, template: ObsidianTemplate):
        self._obsidian_vault.delete_file(file=template.file)

    def _build_template_file_for_model(self, model_name: str) -> ObsidianTemplateFile:
        template_path = (
            self._obsidian_config.templates_folder / f"{model_name}{MARKDOWN_FILE_SUFFIX}"
        )
        file = ObsidianTemplateFile(
            path=template_path,
            addon_config=self._addon_config,
            field_factory=self._field_factory,
        )
        return file

    def _get_srs_template_files_in_obsidian(self) -> Generator[ObsidianTemplateFile, None, None]:
        templates_folder_path = self._obsidian_config.templates_folder
        templates_folder_path.mkdir(parents=True, exist_ok=True)

        for file_path in templates_folder_path.iterdir():
            if check_is_srs_file(path=file_path):
                obsidian_file = ObsidianTemplateFile(
                    path=file_path,
                    addon_config=self._addon_config,
                    field_factory=self._field_factory,
                )
                yield obsidian_file
