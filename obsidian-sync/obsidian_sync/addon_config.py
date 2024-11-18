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
from typing import Tuple, Callable, List

from obsidian_sync.anki.anki_app import AnkiApp
from obsidian_sync.utils import format_add_on_message
from obsidian_sync.constants import (
    ADD_ON_NAME, ADD_ON_ID, CONF_VAULT_PATH, CONF_SRS_FOLDER_IN_OBSIDIAN, CONF_SYNC_WITH_OBSIDIAN_ON_ANKI_WEB_SYNC,
    CONF_ANKI_DECK_NAME_FOR_OBSIDIAN_IMPORTS
)


class AddonConfigUpdateListener:
    def __init__(self, on_update: Callable):
        self._on_update = on_update

    def issue_update(self):
        self._on_update()


class AddonConfig:
    def __init__(self, anki_app: AnkiApp):
        self._anki_app = anki_app
        self._anki_app.addon_config_editor_will_update_json.append(self._on_config_update)
        self._config_update_listeners: List[AddonConfigUpdateListener] = []
        self._on_config_update(json.dumps(self._anki_app.config), __name__)

    @property
    def config(self):
        return self._anki_app.config

    @property
    def obsidian_vault_path(self) -> Path:
        path = Path(self.config[CONF_VAULT_PATH])
        return path

    @property
    def srs_folder(self) -> Path:
        anki_folder_in_obsidian = self.config[CONF_SRS_FOLDER_IN_OBSIDIAN]
        if anki_folder_in_obsidian:
            path = Path(self.obsidian_vault_path / self.config[CONF_SRS_FOLDER_IN_OBSIDIAN])
        else:
            path = self.obsidian_vault_path
        return path

    @property
    def sync_with_obsidian_on_anki_web_sync(self) -> bool:
        return self.config[CONF_SYNC_WITH_OBSIDIAN_ON_ANKI_WEB_SYNC]

    @property
    def anki_deck_name_for_obsidian_imports(self) -> str:
        return self.config[CONF_ANKI_DECK_NAME_FOR_OBSIDIAN_IMPORTS]

    def register_config_update_listener(self, listener: AddonConfigUpdateListener):
        self._config_update_listeners.append(listener)

    def _on_config_update(self, text: str, add_on_id: str) -> str:
        if add_on_id in (ADD_ON_ID, ADD_ON_NAME.lower(), __name__):
            config = json.loads(text)
            vault_path = Path(config[CONF_VAULT_PATH])
            prompt_canceled = False

            while not self._check_valid_vault_path(vault_path=vault_path) and not prompt_canceled:
                self._anki_app.show_info(
                    text=format_add_on_message("Please specify the path to your Obsidian vault."),
                    title=ADD_ON_NAME,
                )
                vault_path, prompt_canceled = self._prompt_for_vault_path(vault_path)

                if prompt_canceled:
                    self._anki_app.show_critical(
                        text=format_add_on_message(
                            message=(
                                f"No valid Obsidian vault path selected. "
                                f"Please set the path in the add-on configs for {ADD_ON_NAME}."
                            ),
                        ),
                        title=ADD_ON_NAME,
                    )
                elif not self._check_valid_vault_path(vault_path=vault_path):
                    self._anki_app.show_critical(
                        text=format_add_on_message(
                            message=(
                                "Selected directory is not a valid Obsidian vault. "
                                "Please select a directory containing a .obsidian folder."
                            ),
                        ),
                        title=ADD_ON_NAME,
                    )
                else:
                    config[CONF_VAULT_PATH] = str(vault_path)
                    self._anki_app.write_config(config=config)
                    self._anki_app.show_tooltip(tip=format_add_on_message("Obsidian vault path updated successfully."))

            text = json.dumps(config)

            self._update_listeners()
        return text

    def _update_listeners(self):
        for listener in self._config_update_listeners:
            listener.issue_update()

    @staticmethod
    def _check_valid_vault_path(vault_path: Path) -> bool:
        return (vault_path / ".obsidian").exists()

    def _prompt_for_vault_path(self, current_path: Path) -> Tuple[Path, bool]:
        return self._anki_app.prompt_for_path(starting_path=current_path.parent)
