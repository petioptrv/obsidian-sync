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
import time
from pathlib import Path
from typing import Set, Dict, Optional

from obsidian_sync.constants import ADD_ON_METADATA_PATH


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
        self._last_sync_timestamp: int = 0
        self._anki_notes_synced_to_obsidian_id_set = set()
        self._anki_notes_synced_to_obsidian_dict: Dict[int, str] = {}
        self._reversed_anki_notes_synced_to_obsidian_dict: Dict[str, int] = {}
        self._sync_started = False

    def __enter__(self) -> "AddonMetadata":
        self.start_sync()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit_sync()

    @property
    def last_sync_timestamp(self) -> int:
        assert self._sync_started
        return self._last_sync_timestamp

    @property
    def anki_notes_synced_to_obsidian(self) -> Set[int]:
        assert self._sync_started
        return set(self._anki_notes_synced_to_obsidian_id_set)

    def start_sync(self):
        self._load()
        self._sync_started = True

    def commit_sync(self):
        assert self._sync_started
        self._last_sync_timestamp = int(time.time())
        self._save()
        self._sync_started = False

    def add_synced_note(self, note_id: int, note_path: Path):
        assert self._sync_started
        path_string = str(note_path)
        self._anki_notes_synced_to_obsidian_dict[note_id] = path_string
        self._reversed_anki_notes_synced_to_obsidian_dict[path_string] = note_id
        self._anki_notes_synced_to_obsidian_id_set.add(note_id)

    def remove_synced_note(self, note_id: Optional[int], note_path: Optional[Path]):
        assert self._sync_started
        if note_id is not None:
            self._remove_by_id(note_id=note_id)
        elif note_path is not None:
            for note_id, path_str in self._anki_notes_synced_to_obsidian_dict.items():
                if Path(path_str) == note_path:
                    self._remove_by_id(note_id=note_id)
                    break

    def get_path_from_note_id(self, note_id: int) -> Optional[Path]:
        path_str = self._anki_notes_synced_to_obsidian_dict.get(note_id, None)
        return Path(path_str) if path_str else None

    def get_note_id_from_path(self, path: Path) -> Optional[int]:
        return self._reversed_anki_notes_synced_to_obsidian_dict.get(str(path), None)

    def _remove_by_id(self, note_id: int):
        path_string = self._anki_notes_synced_to_obsidian_dict.pop(note_id, None)
        self._reversed_anki_notes_synced_to_obsidian_dict.pop(path_string, None)
        if note_id in self._anki_notes_synced_to_obsidian_id_set:
            self._anki_notes_synced_to_obsidian_id_set.remove(note_id)

    def _load(self):
        file_path = self._get_file_path()
        if file_path.exists():
            string = file_path.read_text()
            metadata_json = json.loads(s=string)
            self._last_sync_timestamp = int(metadata_json.get("last_sync_timestamp", 0))
            self._anki_notes_synced_to_obsidian_dict = {
                int(note_id_str): path_string
                for note_id_str, path_string in metadata_json.get("anki_notes_synced_to_obsidian", dict()).items()
            }
            self._reversed_anki_notes_synced_to_obsidian_dict = {
                path_string: note_id for note_id, path_string in self._anki_notes_synced_to_obsidian_dict.items()
            }
            self._anki_notes_synced_to_obsidian_id_set = set(self._anki_notes_synced_to_obsidian_dict.keys())

    def _save(self):
        file_path = self._get_file_path()
        with open(file_path, "w") as f:
            dict_ = {
                "last_sync_timestamp": self._last_sync_timestamp,
                "anki_notes_synced_to_obsidian": self._anki_notes_synced_to_obsidian_dict,
            }
            json.dump(obj=dict_, fp=f)

    @staticmethod
    def _get_file_path() -> Path:
        ADD_ON_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        return ADD_ON_METADATA_PATH
