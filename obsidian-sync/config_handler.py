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
from typing import Tuple

from aqt import gui_hooks, mw
from aqt.utils import showCritical, showInfo, qconnect, tooltip
from aqt.qt import QFileDialog

from .utils import format_add_on_message
from .constants import (
    ADD_ON_NAME, ADD_ON_ID, CONF_VAULT_PATH, CONF_FIELD_NAME_HEADER_TAG, \
    CONF_ANKI_NOTE_IN_OBSIDIAN_PROPERTY_VALUE, CONF_ANKI_FOLDER
)


class ConfigHandler:
    def __init__(self):
        gui_hooks.addon_config_editor_will_update_json.append(self._on_config_update)
        self._config = mw.addonManager.getConfig(__name__)
        self._on_config_update(json.dumps(self._config), __name__)

    @property
    def config(self):
        config = mw.addonManager.getConfig(__name__) or self._config
        self._config = config or self._config
        return config

    @property
    def vault_path(self) -> Path:
        path = Path(self.config[CONF_VAULT_PATH])
        return path

    @property
    def anki_folder(self) -> Path:
        anki_folder = self.config[CONF_ANKI_FOLDER]
        if anki_folder:
            path = Path(self.vault_path / self.config[CONF_ANKI_FOLDER])
        else:
            path = self.vault_path
        return path

    @property
    def anki_note_in_obsidian_property_value(self) -> str:
        return self.config[CONF_ANKI_NOTE_IN_OBSIDIAN_PROPERTY_VALUE]

    @property
    def field_name_header_tag(self) -> str:
        return self.config[CONF_FIELD_NAME_HEADER_TAG]

    def _on_config_update(self, text: str, add_on_id: str) -> str:
        if add_on_id in (ADD_ON_ID, ADD_ON_NAME.lower(), __name__):
            config = json.loads(text)
            vault_path = Path(config[CONF_VAULT_PATH])
            prompt_canceled = False

            while not self._check_valid_vault_path(vault_path=vault_path) and not prompt_canceled:
                showInfo(
                    text=format_add_on_message("Please specify the path to your Obsidian vault."),
                    title=ADD_ON_NAME,
                )
                vault_path, prompt_canceled = self._prompt_for_vault_path(vault_path)

                if prompt_canceled:
                    showCritical(
                        text=format_add_on_message(
                            message=(
                                f"No valid Obsidian vault path selected. "
                                f"Please set the path in the add-on configs for {ADD_ON_NAME}."
                            ),
                        ),
                        help=None,
                        title=ADD_ON_NAME,
                    )
                elif not self._check_valid_vault_path(vault_path=vault_path):
                    showCritical(
                        text=format_add_on_message(
                            message=(
                                "Selected directory is not a valid Obsidian vault. "
                                "Please select a directory containing a .obsidian folder."
                            ),
                        ),
                        help=None,
                        title=ADD_ON_NAME,
                    )
                else:
                    config[CONF_VAULT_PATH] = str(vault_path)
                    mw.addonManager.writeConfig(__name__, config)
                    tooltip(format_add_on_message("Obsidian vault path updated successfully."))

            text = json.dumps(config)
        return text

    @staticmethod
    def _check_valid_vault_path(vault_path: Path) -> bool:
        return (vault_path / ".obsidian").exists()

    @staticmethod
    def _prompt_for_vault_path(current_path: Path) -> Tuple[Path, bool]:
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setDirectory(str(current_path.parent))

        new_path = current_path
        canceled = False

        if dialog.exec():
            selected_paths = dialog.selectedFiles()
            if selected_paths:
                new_path = Path(selected_paths[0])
        else:
            canceled = True

        return new_path, canceled
