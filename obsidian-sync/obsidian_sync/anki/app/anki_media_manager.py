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
from typing import List

import aqt
from bs4 import BeautifulSoup

from obsidian_sync.base_types.content import MediaReference
from obsidian_sync.file_utils import check_is_media_file


class AnkiReferencesManager:
    @property
    def media_directory(self) -> Path:
        return Path(aqt.mw.col.media.dir())

    def get_media_file_paths_from_card_field_text(self, model_id: int, field_text: str) -> List[Path]:
        file_paths = []
        for file_name in aqt.mw.col.media.files_in_str(mid=model_id, string=field_text):
            file_path = self.media_directory / file_name
            if check_is_media_file(path=file_path) and file_path.exists():
                file_paths.append(file_path)
        return file_paths

    def ensure_media_is_in_anki(self, reference: MediaReference) -> Path:
        media = aqt.mw.col.media
        if not media.have(fname=reference.path.name):
            media.add_file(path=reference.path)
        media_path = self.media_directory / reference.path.name
        return media_path

    @staticmethod
    def get_obsidian_urls_from_card_field_text(field_text: str) -> List[str]:
        soup = BeautifulSoup(field_text, "html.parser")
        obsidian_links = soup.find_all("a", href=lambda href: href and href.startswith("obsidian://open"))
        obsidian_urls = [link["href"] for link in obsidian_links]
        return obsidian_urls
