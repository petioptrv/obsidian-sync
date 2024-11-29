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
from pathlib import Path

from obsidian_sync.file_utils import move_file_to_system_trash
from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.obsidian.reference_manager import ObsidianReferencesManager
from obsidian_sync.constants import OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE, OBSIDIAN_LOCAL_TRASH_OPTION_VALUE, \
    OBSIDIAN_LOCAL_TRASH_FOLDER, OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_file import ObsidianFile


class ObsidianVault:
    def __init__(
        self,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
    ):
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        self._attachments_manager = ObsidianReferencesManager(
            addon_config=addon_config, obsidian_config=obsidian_config
        )

    @property
    def attachments_manager(self) -> ObsidianReferencesManager:
        return self._attachments_manager

    def get_path_relative_to_vault(self, absolute_path: Path) -> Path:
        relative_path = absolute_path.relative_to(self._obsidian_config.vault_folder)
        return relative_path

    @staticmethod
    def save_file(file: ObsidianFile):
        file_text = file.content.to_obsidian_file_text()

        file.path.parent.mkdir(parents=True, exist_ok=True)
        file.path.write_text(file_text, encoding="utf-8")

    def delete_file(self, file: ObsidianFile):
        """No need to delete linked resources (images, etc.). We don't know if the resource
        is linked to by other notes and deleting a file in obsidian does not delete the linked
        resources either."""
        trash_option = self._obsidian_config.trash_option

        if trash_option is None or trash_option == OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE:
            move_file_to_system_trash(file_path=file.path)
        elif trash_option == OBSIDIAN_LOCAL_TRASH_OPTION_VALUE:
            self._move_to_local_trash(file_path=file.path)
        elif trash_option == OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE:
            file.path.unlink()
        else:
            raise NotImplementedError  # unrecognized delete option

    def _move_to_local_trash(self, file_path: Path):
        trash_folder = self._addon_config.obsidian_vault_path / OBSIDIAN_LOCAL_TRASH_FOLDER
        trash_folder.mkdir(parents=True, exist_ok=True)
        new_file_path = trash_folder / file_path.name
        file_path.rename(new_file_path)
