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
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from aqt import mw
from aqt.utils import showCritical, tooltip

from ..builders.obsidian_note_builder import ObsidianNoteBuilder
from ..obsidian_note_parser import ObsidianNoteParser
from ..utils import format_add_on_message, is_markdown_file, get_templates_folder_path, \
    delete_obsidian_note
from ..constants import MODEL_ID_PROPERTY_NAME, TEMPLATE_DATE_FORMAT, TEMPLATE_TIME_FORMAT, \
    ADD_ON_NAME, NOTE_PROPERTIES_BASE_STRING
from ..config_handler import ConfigHandler


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
    def __init__(
        self,
        config_handler: ConfigHandler,
        obsidian_note_builder: ObsidianNoteBuilder,
        obsidian_note_parser: ObsidianNoteParser,
    ):
        self._config_handler = config_handler
        self._obsidian_note_builder = obsidian_note_builder
        self._obsidian_note_parser = obsidian_note_parser

    def sync_note_templates(self):
        try:

            anki_templates = self._get_all_anki_note_templates()
            obsidian_templates = self._get_all_obsidian_note_templates()
            model_ids_to_delete = []

            for model_id, template in obsidian_templates.items():
                if model_id not in anki_templates:
                    delete_obsidian_note(
                        obsidian_vault=self._config_handler.vault_path, obsidian_note_path=template.path
                    )
                    model_ids_to_delete.append(model_id)

            for model_id in model_ids_to_delete:
                del obsidian_templates[model_id]

            for model_id, template in anki_templates.items():
                if model_id not in obsidian_templates:
                    self._create_anki_template_in_obsidian(template=template)
                else:
                    self._merge_templates(anki_template=template, obsidian_template=obsidian_templates[model_id])

        except Exception as e:
            logging.exception("Failed to sync note templates.")
            showCritical(
                text=format_add_on_message(f"Error syncing note templates: {str(e)}"),
                title=ADD_ON_NAME,
            )
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
        templates_folder_path = get_templates_folder_path(obsidian_vault=self._config_handler.vault_path)
        templates_folder_path.mkdir(parents=True, exist_ok=True)

        templates = {}

        for template_file_path in templates_folder_path.iterdir():
            if is_markdown_file(template_file_path):
                with open(template_file_path, "r", encoding="utf-8") as f:
                    template_content = f.read()
                if self._obsidian_note_parser.is_anki_note_in_obsidian(note_content=template_content):
                    template_id = None
                    try:
                        template_id = self._obsidian_note_parser.get_model_id_from_obsidian_note_content(
                            content=template_content
                        )
                    except Exception:
                        logging.exception(f"Failed to sync note template {template_file_path}.")
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
        templates_folder_path = get_templates_folder_path(obsidian_vault=self._config_handler.vault_path)
        template_path = templates_folder_path / f"{template.model_name}.md"

        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)

    def _convert_to_obsidian_template_content(self, anki_template: AnkiTemplate):
        obsidian_template = NOTE_PROPERTIES_BASE_STRING.format(
            model_id=anki_template.model_id,
            note_id=0,
            tags="",
            date_modified=f"\"{{{{date:{TEMPLATE_DATE_FORMAT} {TEMPLATE_TIME_FORMAT}}}}}\"",
            date_synced="",
            anki_note_identifier_property_value=self._config_handler.anki_note_in_obsidian_property_value,
        )

        for field in anki_template.fields:
            title = self._obsidian_note_builder.build_field_title(field_name=field)
            obsidian_template += f"{title}\n\n\n"

        return obsidian_template

    @staticmethod
    def _extract_note_templates_data_to_file_for_development(templates):
        addon_dir = os.path.dirname(__file__)
        file_path = os.path.join(addon_dir, "anki_note_templates_data.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
