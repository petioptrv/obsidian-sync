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
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Set

from obsidian_sync.constants import ADD_ON_METADATA_PATH


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            ret = list(obj)
        else:
            ret = json.JSONEncoder.default(self, obj)
        return ret


@dataclass
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
    anki_notes_synced_to_obsidian: Set[int] = field(default_factory=set)

    def load(self):
        file_path = self._get_file_path()
        if file_path.exists():
            string = file_path.read_text()
            metadata_json = json.loads(s=string)
            self.anki_notes_synced_to_obsidian = set(
                metadata_json["anki_notes_synced_to_obsidian"]
            )

    def save(self):
        file_path = self._get_file_path()
        with open(file_path, "w") as f:
            dict_ = asdict(self)
            json.dump(obj=dict_, fp=f, cls=SetEncoder)

    @staticmethod
    def _get_file_path() -> Path:
        ADD_ON_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        return ADD_ON_METADATA_PATH
