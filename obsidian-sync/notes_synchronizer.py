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

from aqt import gui_hooks, mw
from aqt.utils import showCritical, showInfo, qconnect, tooltip

from .config_handler import ConfigHandler
from .utils import format_add_on_message


class NotesSynchronizer:
    def __init__(self, config_handler: ConfigHandler):
        self._config_handler = config_handler

    def sync_notes(self):
        try:
            notes = self._get_all_notes()

            tooltip(format_add_on_message("Notes synced successfully."))
        except Exception as e:
            showCritical(format_add_on_message(f"Obsidian sync error: {str(e)}"))

    @staticmethod
    def _get_all_notes():
        notes = []
        for nid in mw.col.find_notes(""):
            note = mw.col.get_note(nid)
            note_data = {
                "nid": nid,
                "mid": note.mid,
                "model": note.model()["name"],
                "fields": note.fields,
                "tags": note.tags,
                "deck": mw.col.decks.name(note.cards()[0].did)
            }
            notes.append(note_data)
        return notes

    @staticmethod
    def _store_notes_data(notes):
        """For testing."""

        addon_dir = os.path.dirname(__file__)
        file_path = os.path.join(addon_dir, "anki_notes_data.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
