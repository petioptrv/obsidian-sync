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
from obsidian_sync.anki.anki_template import AnkiTemplate
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_template import ObsidianTemplate
from obsidian_sync.anki.anki_app import AnkiApp
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.utils import format_add_on_message
from obsidian_sync.constants import ADD_ON_NAME


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
        obsidian_vault: ObsidianVault,
        markup_translator: MarkupTranslator,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        self._obsidian_vault = obsidian_vault
        self._markup_translator = markup_translator

    def synchronize_templates(self):
        try:
            anki_templates = self._anki_app.get_all_anki_note_templates()
            obsidian_templates = self._obsidian_vault.get_all_obsidian_templates()

            obsidian_templates = self._remove_deleted_templates(
                anki_templates=anki_templates, obsidian_templates=obsidian_templates
            )

            for model_id, anki_template in anki_templates.items():
                if model_id not in obsidian_templates:
                    ObsidianTemplate.from_template(
                        template=anki_template,
                        addon_config=self._addon_config,
                        obsidian_vault=self._obsidian_vault,
                        markup_translator=self._markup_translator,
                    )
                else:
                    obsidian_templates[model_id].update_with_template(template=anki_template)

            self._anki_app.show_tooltip(tip=format_add_on_message("Templates synced successfully."))
        except Exception as e:
            logging.exception("Failed to sync note templates.")
            self._anki_app.show_critical(
                text=format_add_on_message(f"Error syncing note templates: {str(e)}"),
                title=ADD_ON_NAME,
            )

    @staticmethod
    def _remove_deleted_templates(
        anki_templates: Dict[int, AnkiTemplate],
        obsidian_templates: Dict[int, ObsidianTemplate],
    ) -> Dict[int, ObsidianTemplate]:
        model_ids_to_delete = []

        for model_id, template in obsidian_templates.items():
            if model_id not in anki_templates:
                template.delete()
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
