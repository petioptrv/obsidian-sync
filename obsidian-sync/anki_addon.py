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

from aqt import mw
from aqt.qt import QAction, QKeySequence, QApplication
from aqt.utils import showCritical, qconnect

from .constants import ADD_ON_NAME
from .note_builders.obsidian_note_builder import ObsidianNoteBuilder
from .markup_converter import MarkupConverter
from .utils import format_add_on_message
from .obsidian_note_parser import ObsidianNoteParser
from .synchronizers.notes_synchronizer import NotesSynchronizer
from .synchronizers.templates_synchronizer import TemplatesSynchronizer
from .config_handler import ConfigHandler


class AnkiAddon:
    """Anki add-on composition root."""

    def __init__(self):
        self._config_handler = ConfigHandler()
        markup_converter = MarkupConverter()
        obsidian_note_builder = ObsidianNoteBuilder(
            config_handler=self._config_handler, markup_converter=markup_converter
        )
        obsidian_note_parser = ObsidianNoteParser(
            config_handler=self._config_handler,
            note_converter=markup_converter,
        )
        self._templates_synchronizer = TemplatesSynchronizer(
            config_handler=self._config_handler,
            obsidian_note_builder=obsidian_note_builder,
            obsidian_note_parser=obsidian_note_parser,
        )
        self._notes_synchronizer = NotesSynchronizer(
            config_handler=self._config_handler,
            obsidian_note_builder=obsidian_note_builder,
            obsidian_note_parser=obsidian_note_parser,
        )
        self._add_menu_items()

    def _add_menu_items(self):
        action = QAction("Obsidian Sync", mw)
        shortcut = QKeySequence("Ctrl+Y")
        action.setShortcut(shortcut)
        qconnect(action.triggered, self._sync_with_obsidian)
        mw.form.menuTools.addAction(action)
        # todo: add option to open Obsidian note from selected Anki note (both shown on the review screen and if selected in the browse window)

    def _sync_with_obsidian(self):
        # todo: maybe add option to specify the Obsidian vault folder in which to use for Anki syncing (?)

        # todo: make note linking be configurable via regex
        # todo: it should default to "[Link Title|nidxxxxxxxxxxxxx]" in Anki to `LinkTitle: [[note-path]]` in Obsidian

        # todo: ensure changing note path is reflected in the other app

        # ENHANCEMENTS

        # todo: for conflicting notes
        #     todo: explore git-style diff conflict resolver in Python
        #     todo: else, interactive choice of which one to keep, with option to apply to all remaining: keep most recent/keep Anki/keep Obsidian

        # todo: add option to only transfer cards from Obsidian to Anki if their parents are already learned to a configurable level

        if self._check_can_sync():
            self._templates_synchronizer.sync_note_templates()
            self._notes_synchronizer.sync_notes()

    def _check_can_sync(self):
        open_editing_windows = self._get_open_editing_anki_windows()
        can_sync = True
        if open_editing_windows:
            message = "Please close the following windows before syncing:\n\n" + "\n".join(open_editing_windows)
            showCritical(
                text=format_add_on_message(message=message),
                title=ADD_ON_NAME
            )
            can_sync = False
        return can_sync

    def _get_open_editing_anki_windows(self):
        open_editing_windows = []

        for window in QApplication.topLevelWidgets():
            if window.isVisible():
                window_name = self._get_editing_window_name(window)
                if window_name:
                    open_editing_windows.append(window_name)

        return open_editing_windows

    @staticmethod
    def _get_editing_window_name(window):
        window_name = window.windowTitle()

        if not window_name.startswith("Browse") and not window_name in ["Add", "Edit Current"]:
            window_name = None   # For other windows we don't care about

        return window_name
