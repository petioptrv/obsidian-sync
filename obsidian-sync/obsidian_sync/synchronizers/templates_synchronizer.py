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

import json
import logging
import os
from typing import Dict

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.anki.template import AnkiTemplate
from obsidian_sync.obsidian.config import ObsidianConfig
from obsidian_sync.obsidian.template import ObsidianTemplate
from obsidian_sync.anki.app.app import AnkiApp
from obsidian_sync.obsidian.templates_manager import ObsidianTemplatesManager
from obsidian_sync.obsidian.vault import ObsidianVault
from obsidian_sync.utils import format_add_on_message
from obsidian_sync.constants import ADD_ON_NAME, OBSIDIAN_LINK_URL_FIELD_NAME


class TemplatesSynchronizer:
    """
    Templates are uni-directionally synchronized from Anki to Obsidian.

    All template changes must happen in Anki. (already added to the README.md)
    """

    def __init__(
        self,
        anki_app: AnkiApp,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        obsidian_vault = ObsidianVault(addon_config=addon_config, obsidian_config=obsidian_config)
        self._obsidian_templates_manager = ObsidianTemplatesManager(
            anki_app=anki_app,
            obsidian_config=obsidian_config,
            obsidian_vault=obsidian_vault,
            addon_config=addon_config,
        )

    def synchronize_templates(self):
        try:
            anki_templates = self._anki_app.get_all_anki_templates()
            anki_templates = self._check_anki_templates(anki_templates=anki_templates)
            obsidian_templates = self._obsidian_templates_manager.get_all_obsidian_templates()

            obsidian_templates = self._remove_deleted_templates(
                anki_templates=anki_templates, obsidian_templates=obsidian_templates
            )

            for model_id, anki_template in anki_templates.items():
                if model_id not in obsidian_templates:
                    self._obsidian_templates_manager.create_obsidian_template_from_template(
                        reference_template=anki_template,
                    )
                else:
                    self._obsidian_templates_manager.update_obsidian_template_with_template(
                        obsidian_template=obsidian_templates[model_id],
                        reference_template=anki_template,
                    )

            self._anki_app.show_tooltip(tip=format_add_on_message("Templates synced successfully."))
        except Exception as e:
            logging.exception("Failed to sync note templates.")
            self._anki_app.show_critical(
                text=format_add_on_message(f"Error syncing note templates: {str(e)}"),
                title=ADD_ON_NAME,
            )

    def _check_anki_templates(self, anki_templates: Dict[int, AnkiTemplate]) -> Dict[int, AnkiTemplate]:
        if self._addon_config.add_obsidian_url_in_anki:
            for anki_template in list(anki_templates.values()):
                if not any(
                    field.name == OBSIDIAN_LINK_URL_FIELD_NAME
                    for field in anki_template.content.fields
                ):
                    anki_templates[anki_template.model_id] = self._anki_app.add_field_to_anki_template(
                        template=anki_template, field_name=OBSIDIAN_LINK_URL_FIELD_NAME
                    )
        else:
            for anki_template in list(anki_templates.values()):
                if any(
                    field.name == OBSIDIAN_LINK_URL_FIELD_NAME
                    for field in anki_template.content.fields
                ):
                    anki_templates[anki_template.model_id] = self._anki_app.remove_field_from_anki_template(
                        template=anki_template, field_name=OBSIDIAN_LINK_URL_FIELD_NAME
                    )

        return anki_templates

    def _remove_deleted_templates(
        self,
        anki_templates: Dict[int, AnkiTemplate],
        obsidian_templates: Dict[int, ObsidianTemplate],
    ) -> Dict[int, ObsidianTemplate]:
        model_ids_to_delete = []

        for model_id, template in obsidian_templates.items():
            if model_id not in anki_templates:
                self._obsidian_templates_manager.delete_template(template=template)
                model_ids_to_delete.append(model_id)

        for model_id in model_ids_to_delete:
            del obsidian_templates[model_id]

        return obsidian_templates

    @staticmethod
    def _extract_note_templates_data_to_file_for_development(templates):
        addon_dir = os.path.dirname(__file__)
        file_path = os.path.join(addon_dir, "anki_note_templates_data.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
