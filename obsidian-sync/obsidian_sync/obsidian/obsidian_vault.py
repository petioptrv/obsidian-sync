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
import os
from pathlib import Path
from typing import Dict, Generator

from obsidian_sync.anki.anki_app import AnkiApp
from obsidian_sync.file_utils import check_is_srs_file
from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_file import ObsidianTemplateFile
from obsidian_sync.obsidian.obsidian_template import ObsidianTemplate
from obsidian_sync.constants import DECK_NAME_SEPARATOR
from obsidian_sync.utils import format_add_on_message
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig


class ObsidianVault:
    def __init__(
        self,
        anki_app: AnkiApp,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
        markup_translator: MarkupTranslator,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        self._markup_translator = markup_translator

    @staticmethod
    def build_relative_path_from_deck(deck: str) -> Path:
        relative_path = Path(deck.replace(DECK_NAME_SEPARATOR, os.path.sep))
        return relative_path

    def build_obsidian_note_folder_path_from_deck(self, deck: str) -> Path:
        relative_path = self.build_relative_path_from_deck(deck=deck)
        path = Path(self._addon_config.srs_folder_in_obsidian / relative_path)
        return path

    def get_all_obsidian_templates(self) -> Dict[int, ObsidianTemplate]:
        self._obsidian_config.templates_folder.mkdir(parents=True, exist_ok=True)
        templates = {}

        for template_file in self._get_srs_template_files_in_obsidian(markup_translator=self._markup_translator):
            template = None
            try:
                template = ObsidianTemplate(
                    file=template_file,
                    addon_config=self._addon_config,
                    obsidian_config=self._obsidian_config,
                    markup_translator=self._markup_translator,
                )
            except Exception:
                logging.exception(f"Failed to sync note template {template_file.path}.")
                self._anki_app.show_critical(
                    text=format_add_on_message(f"Failed to sync note template {template_file.path}."),
                    title="Failed to sync template",
                )
            if template is not None:
                if template.properties.model_id in templates:
                    self._anki_app.show_critical(
                        text=format_add_on_message(
                            f"Duplicate Anki note templates found (model ID {template.properties.model_id}) with names"
                            f" {templates[template.properties.model_id].name} and {template_file.name}."
                            f" Only synchronizing {template_file.name}."
                        ),
                        title="Duplicate Anki note templates",
                    )
                templates[template.properties.model_id] = template

        return templates

    def _get_srs_template_files_in_obsidian(
        self, markup_translator: MarkupTranslator
    ) -> Generator[ObsidianTemplateFile, None, None]:
        templates_folder_path = self._obsidian_config.templates_folder
        templates_folder_path.mkdir(parents=True, exist_ok=True)

        for file_path in templates_folder_path.iterdir():
            if check_is_srs_file(path=file_path):
                obsidian_file = ObsidianTemplateFile(
                    path=file_path,
                    addon_config=self._addon_config,
                    obsidian_config=self._obsidian_config,
                    markup_translator=markup_translator,
                )
                yield obsidian_file

