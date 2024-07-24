# -*- coding: utf-8 -*-
from pathlib import Path

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

from aqt import gui_hooks, mw
from aqt.qt import QAction, QKeySequence
from aqt.utils import showCritical, showInfo, qconnect, tooltip

from .obsidian_note_finder import ObsidianNoteFinder
from .notes_synchronizer import NotesSynchronizer
from .templates_synchronizer import TemplatesSynchronizer
from .config_handler import ConfigHandler


class AnkiAddon:
    """Anki add-on composition root."""

    # todo: add button to open note in Obsidian

    def __init__(self):
        self._config_handler = ConfigHandler()
        obsidian_note_finder = ObsidianNoteFinder(config_handler=self._config_handler)
        self._templates_synchronizer = TemplatesSynchronizer(
            config_handler=self._config_handler, obsidian_note_finder=obsidian_note_finder
        )
        self._notes_synchronizer = NotesSynchronizer(config_handler=self._config_handler)
        self._add_menu_item()

    def _add_menu_item(self):
        action = QAction("Obsidian Sync", mw)
        shortcut = QKeySequence("Ctrl+Shift+Y")
        action.setShortcut(shortcut)
        qconnect(action.triggered, self._sync_with_obsidian)
        mw.form.menuTools.addAction(action)

    def _sync_with_obsidian(self):
        # todo: ensure that cards and notes that do not need to be updated are not updated (this will affect the last update ts)

        # todo: make note linking be configurable via regex
        # todo: it should default to `\[ontocapturegrp|nid.d+]\` in Anki to `ontocapturegrp: [[note-path]]` in Obsidian

        # todo: get {nid: path} dict of all obsidian files with the "anki" tag (make it configurable)
        # todo: get all Obsidian notes created from templates but that do not yet have associated nid
        # todo: get {nid: note} dict of all Anki notes
        # todo: for the superset of notes
        #     todo: if it does not exist in Anki, create it
        #         todo: convert Anki card links based on nid into Obsidian links between notes
        #     todo: if it does not exist in Obsidian, create it
        #         todo: convert Obsidian links between notes into Anki card links based on nid
        #     todo: if it exists in both, check to see if they have the same content AND the same path (deck)
        #     todo: if not
        #         todo: add to list of conflicts
        # todo: for conflicting notes
        #     todo: explore git-style diff conflict resolver in Python
        #     todo: else, interactive choice of which one to keep, with option to apply to all remaining: keep most recent/keep Anki/keep Obsidian
        # todo: output visual, collapsible report on the changes

        self._templates_synchronizer.sync_note_templates()
        # self._notes_synchronizer.sync_notes()

