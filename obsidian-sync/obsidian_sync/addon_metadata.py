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
from typing import Set, Dict

from obsidian_sync.constants import ADD_ON_METADATA_PATH
from obsidian_sync.obsidian.note import ObsidianNote


class AddonMetadata:
    """Used to store metadata across sessions.

    As a rule of thumb, this class should be used as a last resort. The add-on must
    use Obsidian and Anki data as much as possible, and only resort to persisting
    metadata where no other option exists.

    For example, it"s tempting to use persisted metadata to know which note was last
    synced and which was most recently updated, but this information can be persisted
    inside the note itself, and combined with information from the file system.

    An example of useful case is to know which notes were deleted in Obsidian when
    the "none" trash option is configured in the Anki settings (i.e. files are unlinked
    instead of moved to a trash folder.
    """
    def __init__(self):
        self._anki_notes_synced_to_obsidian: Dict[int, str] = {}
        self._sync_started = False

    @property
    def anki_notes_synced_to_obsidian(self) -> Set[int]:
        return set(self._anki_notes_synced_to_obsidian.keys())

    def start_sync(self):
        self._load()
        self._sync_started = True

    def commit_sync(self):
        self._save()
        self._sync_started = False

    def add_synced_note(self, note: ObsidianNote):
        assert self._sync_started
        if not note.is_corrupt() and not note.is_new():
            self._anki_notes_synced_to_obsidian[note.id] = str(note.file.path)

    def remove_synced_note(self, note: ObsidianNote):
        assert self._sync_started
        if not note.is_corrupt():
            self._anki_notes_synced_to_obsidian.pop(note.id, None)
        elif note.file is not None:
            for note_id, path_str in self._anki_notes_synced_to_obsidian.items():
                if Path(path_str) == note.file.path:
                    self._anki_notes_synced_to_obsidian.pop(note_id)
                    break

    def _load(self):
        file_path = self._get_file_path()
        if file_path.exists():
            string = file_path.read_text()
            metadata_json = json.loads(s=string)
            self._anki_notes_synced_to_obsidian = {
                int(note_id_str): path_str
                for note_id_str, path_str in metadata_json["anki_notes_synced_to_obsidian"].items()
            }

    def _save(self):
        file_path = self._get_file_path()
        with open(file_path, "w") as f:
            dict_ = {
                "anki_notes_synced_to_obsidian": self._anki_notes_synced_to_obsidian,
            }
            json.dump(obj=dict_, fp=f)

    @staticmethod
    def _get_file_path() -> Path:
        ADD_ON_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        return ADD_ON_METADATA_PATH
