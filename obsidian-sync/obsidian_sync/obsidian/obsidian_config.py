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
from pathlib import Path
from typing import Optional, Dict

from obsidian_sync.constants import OBSIDIAN_SETTINGS_FOLDER, OBSIDIAN_TEMPLATES_SETTINGS_FILE, \
    TEMPLATES_FOLDER_JSON_FIELD_NAME, OBSIDIAN_LOCAL_TRASH_OPTION_VALUE, OBSIDIAN_APP_SETTINGS_FILE, \
    OBSIDIAN_TRASH_OPTION_KEY, OBSIDIAN_LOCAL_TRASH_FOLDER, OBSIDIAN_USE_MARKDOWN_LINKS_OPTION_KEY, \
    OBSIDIAN_TEMPLATES_OPTION_KEY, CONF_SRS_FOLDER_IN_OBSIDIAN
from obsidian_sync.addon_config import AddonConfig


class ObsidianConfig:
    def __init__(self, addon_config: AddonConfig):
        self._addon_config = addon_config

    @property
    def templates_enabled(self) -> bool:
        templates = self._settings.get(OBSIDIAN_TEMPLATES_OPTION_KEY)
        return templates is not None and templates

    @property
    def templates_folder(self) -> Path:
        templates_path = (
            self._addon_config.obsidian_vault_path / self._templates_settings[TEMPLATES_FOLDER_JSON_FIELD_NAME]
        )
        return templates_path

    @property
    def trash_folder(self) -> Optional[Path]:
        trash_folder = None

        if self.trash_option == OBSIDIAN_LOCAL_TRASH_OPTION_VALUE:
            trash_folder = self._addon_config.obsidian_vault_path / OBSIDIAN_LOCAL_TRASH_FOLDER

            trash_folder.mkdir(parents=True, exist_ok=True)

        return trash_folder

    @property
    def trash_option(self) -> str:
        trash_option = self._settings.get(OBSIDIAN_TRASH_OPTION_KEY)
        return trash_option

    @property
    def use_markdown_links(self) -> bool:
        use_markdown_links_ = self._settings.get(OBSIDIAN_USE_MARKDOWN_LINKS_OPTION_KEY)
        return use_markdown_links_ is not None and use_markdown_links_

    @property
    def srs_attachments_folder(self) -> Path:
        anki_folder = self._addon_config.srs_folder
        if anki_folder:
            path = Path(anki_folder) / CONF_SRS_FOLDER_IN_OBSIDIAN  # attachment paths are specified relative to the obsidian vault folder
        else:
            path = CONF_SRS_FOLDER_IN_OBSIDIAN
        return path

    @property
    def _templates_settings(self) -> Dict[str, str]:
        templates_json_path = (
            self._addon_config.obsidian_vault_path / OBSIDIAN_SETTINGS_FOLDER / OBSIDIAN_TEMPLATES_SETTINGS_FILE
        )

        with open(templates_json_path, "r") as f:
            templates_settings_json = json.load(f)

        return templates_settings_json

    @property
    def _settings(self) -> Dict[str, str]:
        with open(
            self._addon_config.obsidian_vault_path / OBSIDIAN_SETTINGS_FOLDER / OBSIDIAN_APP_SETTINGS_FILE, "r"
        ) as f:
            settings = json.load(f)

        return settings
