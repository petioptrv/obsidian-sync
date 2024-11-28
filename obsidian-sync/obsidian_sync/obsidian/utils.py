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
import urllib.parse
from pathlib import Path


def obsidian_url_for_note_path(vault_path: Path, note_path: Path) -> str:
    vault_name = urllib.parse.quote(string=vault_path.name)
    note_path_string_relative_to_vault = urllib.parse.quote(
        string=str(note_path.relative_to(vault_path))
    )
    # obsidian_url = (
    #     f"obsidian://open?vault={vault_name}&amp;file={note_path_string_relative_to_vault}"
    # )
    obsidian_url = (
        f"obsidian://open?vault={vault_name}&file={note_path_string_relative_to_vault}"
    )
    return obsidian_url
