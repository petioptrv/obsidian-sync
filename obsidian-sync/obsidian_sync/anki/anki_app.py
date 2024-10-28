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
from typing import Dict, List, Tuple, Callable

from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QFileDialog, QApplication
from aqt import mw, gui_hooks, qconnect
from aqt.utils import showInfo, showCritical, tooltip

from obsidian_sync.anki.anki_content import AnkiProperties, AnkiField, AnkiContent
from obsidian_sync.anki.anki_template import AnkiTemplate
from obsidian_sync.constants import ADD_ON_NAME
from obsidian_sync.markup_translator import MarkupTranslator


class AnkiApp:
    @property
    def config(self):
        return mw.addonManager.getConfig(ADD_ON_NAME)

    @property
    def media_directory(self) -> Path:
        return Path(mw.col.media.dir())

    @property
    def addon_config_editor_will_update_json(self) -> List:
        return gui_hooks.addon_config_editor_will_update_json

    @staticmethod
    def get_all_anki_note_templates(markup_translator: MarkupTranslator) -> Dict[int, AnkiTemplate]:
        templates = {}
        all_templates = mw.col.models.all()
        for model in all_templates:
            properties = AnkiProperties(model_id=model["id"])
            fields = [
                AnkiField(name=field["name"], text="", images=[], _markup_translator=markup_translator)
                for field in model["flds"]
            ]
            content = AnkiContent(properties=properties, fields=fields)
            template = AnkiTemplate(content=content, model_name=model["name"])
            templates[model["id"]] = template
        return templates

    @staticmethod
    def show_info(text: str, title: str):
        showInfo(text=text, title=title)

    @staticmethod
    def show_critical(text: str, title: str):
        showCritical(text=text, title=title)

    @staticmethod
    def show_tooltip(tip: str):
        tooltip(tip)

    @staticmethod
    def write_config(config: Dict):
        mw.addonManager.writeConfig(__name__, config)

    @staticmethod
    def prompt_for_path(starting_path: Path) -> Tuple[Path, bool]:
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setDirectory(str(starting_path))

        selected_path = starting_path
        canceled = False

        if dialog.exec():
            selected_paths = dialog.selectedFiles()
            if selected_paths:
                selected_path = Path(selected_paths[0])
        else:
            canceled = True

        return selected_path, canceled

    @staticmethod
    def add_menu_item(title: str, key_sequence: str, callback: Callable):
        action = QAction(title, mw)
        shortcut = QKeySequence(key_sequence)
        action.setShortcut(shortcut)
        qconnect(action.triggered, callback)
        mw.form.menuTools.addAction(action)

    def get_open_editing_anki_windows(self):
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
