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
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from aqt import gui_hooks, mw
from aqt.utils import showCritical, showInfo, qconnect, tooltip

from .html_to_markdown import HTMLToMarkdown
from .obsidian_note_finder import ObsidianNoteFinder
from .utils import format_add_on_message, is_markdown_file
from .constants import TEMPLATES_FOLDER_JSON_FIELD_NAME, MODEL_ID_PROPERTY_NAME, TEMPLATES_PROPERTIES_TEMPLATE
from .config_handler import ConfigHandler


@dataclass
class AnkiTemplate:
    model_id: int
    model_name: str
    fields: List[str]


@dataclass
class ObsidianTemplate:
    path: Path
    content: str


class TemplatesSynchronizer:
    def __init__(self, config_handler: ConfigHandler, obsidian_note_finder: ObsidianNoteFinder):
        self._config_handler = config_handler
        self._obsidian_note_finder = obsidian_note_finder
        self._markdown_converter = HTMLToMarkdown()

    def sync_note_templates(self):
        try:

            anki_templates = self._get_all_anki_note_templates()
            obsidian_templates = self._get_all_obsidian_note_templates()
            model_ids_to_delete = []

            for model_id, template in obsidian_templates.items():
                if model_id not in anki_templates:
                    template.path.unlink()
                    model_ids_to_delete.append(model_id)

            for model_id in model_ids_to_delete:
                del obsidian_templates[model_id]

            for model_id, template in anki_templates.items():
                if model_id not in obsidian_templates:
                    self._create_anki_template_in_obsidian(template=template)
                else:
                    self._merge_templates(anki_template=template, obsidian_template=obsidian_templates[model_id])

        except Exception as e:
            showCritical(format_add_on_message(f"Error syncing note templates: {str(e)}"))
        tooltip(format_add_on_message("Templates synced successfully."))

    @staticmethod
    def _get_all_anki_note_templates() -> Dict[int, AnkiTemplate]:
        templates = {}
        for model in mw.col.models.all():
            template = AnkiTemplate(
                model_id=model["id"],
                model_name=model["name"],
                fields=[field["name"] for field in model["flds"]],
            )
            templates[model["id"]] = template
        return templates

    def _get_all_obsidian_note_templates(self) -> Dict[int, ObsidianTemplate]:
        templates_folder_path = self._get_templates_folder_path()
        templates_folder_path.mkdir(parents=True, exist_ok=True)

        templates = {}

        for template_file_path in templates_folder_path.iterdir():
            if is_markdown_file(template_file_path):
                with open(template_file_path, "r", encoding="utf-8") as f:
                    template_content = f.read()
                if self._obsidian_note_finder.is_anki_note_in_obsidian(note_content=template_content):
                    template_id = None
                    try:
                        template_id = self._obsidian_note_finder.get_template_id_from_anki_note_in_obsidian_content(
                            content=template_content
                        )
                    except Exception:
                        showCritical(
                            format_add_on_message(
                                f"Failed to extract value for property {MODEL_ID_PROPERTY_NAME}"
                                f" for Obsidian template {template_file_path.name}. Template file will be ignored."
                            )
                        )
                    if template_id is not None:
                        template = ObsidianTemplate(path=template_file_path, content=template_content)
                        if template_id in templates:
                            showCritical(
                                format_add_on_message(
                                    f"Duplicate Anki note templates found (model ID {template_id}) with names"
                                    f" {templates[template_id].path.name} and {template_file_path.name}."
                                    f" Only synchronizing {template_file_path.name}."
                                )
                            )
                        templates[template_id] = template

        return templates

    def _merge_templates(self, anki_template: AnkiTemplate, obsidian_template: ObsidianTemplate):
        obsidian_template_content_from_anki = self._convert_to_obsidian_template_content(anki_template=anki_template)
        if obsidian_template_content_from_anki != obsidian_template.content:
            self._create_anki_template_in_obsidian(template=anki_template)

    def _create_anki_template_in_obsidian(self, template: AnkiTemplate):
        template_content = self._convert_to_obsidian_template_content(anki_template=template)
        template_path = self._get_templates_folder_path() / f"{template.model_name}.md"

        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)

    def _convert_to_obsidian_template_content(self, anki_template: AnkiTemplate):
        obsidian_template = TEMPLATES_PROPERTIES_TEMPLATE.format(model_id=anki_template.model_id)
        html_header_tag = self._config_handler.field_name_header_tag

        for field in anki_template.fields:
            html_title = f"<{html_header_tag}>{field}</{html_header_tag}>"
            markdown_title = self._markdown_converter.convert(html=html_title)
            obsidian_template += f"\n{markdown_title}\n"

        return obsidian_template

    def _get_templates_folder_path(self) -> Path:
        templates_json_path = self._config_handler.vault_path / ".obsidian" / "templates.json"

        if not templates_json_path.is_file():
            raise RuntimeError("The templates core plugin is not enabled.")

        with open(templates_json_path, "r") as f:
            templates_json = json.load(f)
            templates_path = self._config_handler.vault_path / templates_json[TEMPLATES_FOLDER_JSON_FIELD_NAME]

        return templates_path

    @staticmethod
    def _extract_note_templates_data_to_file_for_development(templates):
        addon_dir = os.path.dirname(__file__)
        file_path = os.path.join(addon_dir, "anki_note_templates_data.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
