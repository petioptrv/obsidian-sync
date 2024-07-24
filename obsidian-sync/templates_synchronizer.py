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
import os
from pathlib import Path
from typing import Dict

from aqt import gui_hooks, mw
from aqt.utils import showCritical, showInfo, qconnect, tooltip

from .obsidian_note_finder import ObsidianNoteFinder
from .utils import format_add_on_message, is_markdown_file
from .constants import TEMPLATES_FOLDER_JSON_FIELD_NAME
from .config_handler import ConfigHandler


class TemplatesSynchronizer:
    def __init__(self, config_handler: ConfigHandler, obsidian_note_finder: ObsidianNoteFinder):
        self._config_handler = config_handler
        self._obsidian_note_finder = obsidian_note_finder

    def sync_note_templates(self):
        try:
            templates_folder_path = self._get_templates_folder_path()
            templates_folder_path.mkdir(parents=True, exist_ok=True)

            anki_templates = self._get_all_anki_note_templates()
            obsidian_templates = self._get_all_obsidian_note_templates()

            for template in anki_templates:
                obsidian_template = self._convert_to_obsidian_template(template)
                template_file_path = templates_folder_path / f"{template['model_name']}.md"

                with open(template_file_path, "w", encoding="utf-8") as f:
                    f.write(obsidian_template)

        except Exception as e:
            showCritical(format_add_on_message(f"Error syncing note templates: {str(e)}"))
        tooltip(format_add_on_message("Templates synced successfully."))

    @staticmethod
    def _get_all_anki_note_templates() -> Dict[str, Dict]:
        templates = {}
        for model in mw.col.models.all():
            template_data = {
                "model_id": model["id"],
                "model_name": model["name"],
                "fields": [field["name"] for field in model["flds"]],
                "templates": []
            }
            for template in model["tmpls"]:
                template_data["templates"].append({
                    "name": template["name"],
                    "qfmt": template["qfmt"],
                    "afmt": template["afmt"]
                })
            templates[model["id"]] = template_data
        return templates

    def _get_all_obsidian_note_templates(self) -> Dict[str, Dict]:
        templates = {}
        templates_folder_path = self._get_templates_folder_path()

        for template_file_path in templates_folder_path.iterdir():
            if is_markdown_file(template_file_path):
                with open(template_file_path, "r", encoding="utf-8") as f:
                    template_content = f.read()
                if self._obsidian_note_finder.is_anki_note_in_obsidian(note_content=template_content):
                    raise NotImplementedError

        return templates

    def _get_templates_folder_path(self) -> Path:
        templates_json_path = self._config_handler.vault_path / ".obsidian" / "templates.json"

        if not templates_json_path.is_file():
            raise RuntimeError("The templates core plugin is not enabled.")

        with open(templates_json_path, "r") as f:
            templates_json = json.load(f)
            templates_path = self._config_handler.vault_path / templates_json[TEMPLATES_FOLDER_JSON_FIELD_NAME]

        return templates_path

    @staticmethod
    def _convert_to_obsidian_template(anki_template):
        obsidian_template = f"""---
    template: 
    mid: {anki_template['model_id']}
    nid: 0
    tags: []
    date: {{{{date}}}} {{{{time}}}}
    ---
    """
        for field in anki_template['fields']:
            obsidian_template += f"\n## {field}\n\n\n"

        return obsidian_template

    @staticmethod
    def _store_note_templates_data(templates):
        """For testing."""

        addon_dir = os.path.dirname(__file__)
        file_path = os.path.join(addon_dir, "anki_note_templates_data.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
