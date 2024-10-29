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
import filecmp
from pathlib import Path

from obsidian_sync.anki.anki_app import AnkiApp
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault


class MediaSynchronizer:
    def __init__(
        self,
        anki_app: AnkiApp,
        obsidian_vault: ObsidianVault,
    ):
        self._anki_app = anki_app
        self._obsidian_vault = obsidian_vault

    def synchronize_media(self):
        anki_media_files = self._anki_app.get_all_media_files()
        obsidian_srs_attachments = self._obsidian_vault.get_all_srs_attachment_files()

        obsidian_files_map = {f.name: f for f in obsidian_srs_attachments}

        for anki_file in anki_media_files:
            obsidian_file = obsidian_files_map.pop(anki_file.name, None)
            if obsidian_file is not None:
                self._synchronize_files(anki_file=anki_file, obsidian_file=obsidian_file)
            else:
                self._obsidian_vault.copy_file_to_srs_attachments_folder(file=anki_file)

        for obsidian_file in obsidian_files_map.values():
            self._anki_app.add_media_file(file=obsidian_file)

    def _synchronize_files(self, anki_file: Path, obsidian_file: Path):
        identical = filecmp.cmp(f1=anki_file, f2=obsidian_file, shallow=False)

        if not identical:
            if anki_file.stat().st_mtime_ns >= obsidian_file.stat().st_mtime_ns:
                obsidian_file.unlink()
                self._obsidian_vault.copy_file_to_srs_attachments_folder(file=anki_file)
            else:
                anki_file.unlink()
                self._anki_app.add_media_file(file=obsidian_file)
