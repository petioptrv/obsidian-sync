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
import logging
from pathlib import Path
from typing import Dict

from aqt import mw
from aqt.utils import showCritical, tooltip

from ..change_log import ChangeLogBase
from ..note_types import AnkiNote, ObsidianNote
from ..builders.obsidian_note_builder import ObsidianNoteBuilder
from ..constants import DEFAULT_NODE_ID_FOR_NEW_OBSIDIAN_NOTES, ADD_ON_NAME
from ..obsidian_note_parser import ObsidianNoteParser
from ..config_handler import ConfigHandler
from ..utils import format_add_on_message, get_templates_folder_path


class NotesSynchronizer:
    def __init__(
        self,
        config_handler: ConfigHandler,
        obsidian_note_builder: ObsidianNoteBuilder,
        obsidian_note_parser: ObsidianNoteParser,
    ):
        self._config_handler = config_handler
        self._obsidian_note_builder = obsidian_note_builder
        self._obsidian_note_parser = obsidian_note_parser

    def sync_notes(self):
        try:
            anki_notes = self._get_all_anki_notes()
            obsidian_notes = self._get_all_obsidian_notes()

            change_log = ChangeLogBase.build_log(config_handler=self._config_handler)

            while len(anki_notes) != 0:
                note_id, anki_note = anki_notes.popitem()
                if note_id in obsidian_notes:
                    obsidian_note = obsidian_notes.pop(note_id)
                    obsidian_note.update_with_anki_note(anki_note=anki_note, change_log=change_log, print_to_log=True)
                    anki_note.update_with_obsidian_note(
                        obsidian_note=obsidian_note, changes_log=change_log, print_to_log=True
                    )
                else:
                    # todo: check if note file is in Obsidian trash folder and delete Anki note if so
                    ObsidianNote.create_note_file_from_anki_note(
                        config_handler=self._config_handler,
                        obsidian_note_builder=self._obsidian_note_builder,
                        anki_note=anki_note,
                        change_log=change_log,
                    )

            while len(obsidian_notes) != 0:
                note_id, obsidian_note = obsidian_notes.popitem()
                if note_id == DEFAULT_NODE_ID_FOR_NEW_OBSIDIAN_NOTES:
                    AnkiNote.create_in_anki_from_obsidian(obsidian_note=obsidian_note, change_log=change_log)
                else:
                    obsidian_note.delete_file(change_log=change_log)

            change_log.display_changes()

            tooltip(format_add_on_message("Notes synced successfully."))
        except Exception as e:
            logging.exception("Failed to sync notes.")
            showCritical(
                text=format_add_on_message(f"Obsidian sync error: {str(e)}"),
                title=ADD_ON_NAME,
            )

    @staticmethod
    def _get_all_anki_notes() -> Dict[int, AnkiNote]:
        notes = {}

        for nid in mw.col.find_notes(""):
            note = mw.col.get_note(nid)
            notes[nid] = AnkiNote.from_anki_note(note=note)

        return notes

    def _get_all_obsidian_notes(self) -> Dict[int, ObsidianNote]:
        notes = {}
        templates_folder_path = get_templates_folder_path(obsidian_vault=self._config_handler.vault_path)

        for root, dirs, files in os.walk(self._config_handler.anki_folder):
            if Path(root) == templates_folder_path:
                continue
            for file in files:
                file_path = Path(root) / file
                obsidian_note = ObsidianNote.build_from_file(
                    config_handler=self._config_handler,
                    obsidian_note_parser=self._obsidian_note_parser,
                    obsidian_note_builder=self._obsidian_note_builder,
                    file_path=file_path,
                )
                if obsidian_note is not None:
                    notes[obsidian_note.note_id] = obsidian_note

        return notes

    @staticmethod
    def _store_notes_data_for_testing(notes):
        addon_dir = os.path.dirname(__file__)
        file_path = os.path.join(addon_dir, "anki_notes_data.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
