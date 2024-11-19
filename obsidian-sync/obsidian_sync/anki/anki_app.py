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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Callable

from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QFileDialog, QApplication
import aqt
from anki.consts import QUEUE_TYPE_SUSPENDED

from obsidian_sync.anki.anki_content import AnkiField, AnkiTemplateContent, \
    AnkiTemplateProperties, AnkiNoteProperties, AnkiLinkedAttachment, AnkiNoteContent
from obsidian_sync.anki.anki_note import AnkiNote
from obsidian_sync.anki.anki_template import AnkiTemplate
from obsidian_sync.base_types.content import LinkedAttachment
from obsidian_sync.constants import ADD_ON_NAME
from obsidian_sync.file_utils import check_is_attachment_file
from obsidian_sync.markup_translator import MarkupTranslator


class AnkiApp:
    def __init__(self, markup_translator: MarkupTranslator):
        self._markup_translator = markup_translator

    @property
    def config(self):
        return aqt.mw.addonManager.getConfig(module=ADD_ON_NAME)

    @property
    def media_directory(self) -> Path:
        return Path(aqt.mw.col.media.dir())

    @property
    def addon_config_editor_will_update_json(self) -> List:
        return aqt.gui_hooks.addon_config_editor_will_update_json

    def get_all_anki_note_templates(self) -> Dict[int, AnkiTemplate]:
        templates = {}
        all_templates = aqt.mw.col.models.all()

        for model in all_templates:
            properties = AnkiTemplateProperties(model_id=model["id"], model_name=model["name"])
            fields = [
                AnkiField(
                    name=field["name"],
                    text="",
                    attachments=[],
                    _markup_translator=self._markup_translator,
                )
                for field in model["flds"]
            ]
            content = AnkiTemplateContent(properties=properties, fields=fields)
            template = AnkiTemplate(content=content)
            templates[model["id"]] = template

        return templates

    def create_new_empty_note_in_anki(self, model_id: int, deck_name: str) -> AnkiNote:
        col = aqt.mw.col

        deck_id = col.decks.add_normal_deck_with_name(name=deck_name).id
        note_type = col.models.get(id=model_id)
        note = col.new_note(notetype=note_type)

        col.add_note(note=note, deck_id=deck_id)

        anki_note = self.get_note_by_id(note_id=note.id)

        return anki_note

    @staticmethod
    def update_note_in_anki(anki_note: AnkiNote):
        col = aqt.mw.col

        note = col.get_note(id=anki_note.id)

        note.tags = anki_note.content.properties.tags
        note.fields = [
            field.to_html()
            for field in anki_note.content.fields
        ]

        col.update_note(note=note)

    def ensure_attachment_is_in_anki(self, attachment: LinkedAttachment) -> Path:
        media = aqt.mw.col.media
        if not media.have(fname=attachment.path.name):
            media.add_file(path=attachment.path)
        attachment_path = self.media_directory / attachment.path.name
        return attachment_path

    def get_all_notes(self) -> Dict[int, AnkiNote]:
        col = aqt.mw.col
        notes = {}

        for nid in col.find_notes(""):
            note = self.get_note_by_id(note_id=nid)
            notes[note.id] = note

        return notes

    def get_note_by_id(self, note_id: int) -> AnkiNote:
        col = aqt.mw.col
        note = col.get_note(note_id)
        cards = note.cards()

        maximum_card_difficulty = max(
            card.memory_state.difficulty
            if card.memory_state is not None else 0
            for card in cards
        )
        suspended = all(card.queue == QUEUE_TYPE_SUSPENDED for card in cards)

        properties = AnkiNoteProperties(
            model_id=note.mid,
            model_name=note.note_type()["name"],
            note_id=note.id,
            tags=note.tags,
            suspended=suspended,
            maximum_card_difficulty=maximum_card_difficulty,
            date_modified_in_anki=datetime.fromtimestamp(note.mod or note.id / 1000),
        )
        fields = []
        model_id = note.mid

        note_refactored = False
        for field_name, field_text in note.items():
            sanitized_field_text = self._markup_translator.sanitize_html(html=field_text)
            if sanitized_field_text != field_text:
                note_refactored = True
                note[field_name] = sanitized_field_text
                field_text = sanitized_field_text
            attachments = []
            adapted_field_text = field_text
            for file_name in col.media.files_in_str(mid=model_id, string=field_text):
                file_path = self.media_directory / file_name
                if check_is_attachment_file(path=file_path):
                    adapted_field_text = adapted_field_text.replace(file_name, str(file_path))
                    attachments.append(AnkiLinkedAttachment(path=file_path))

            fields.append(
                AnkiField(
                    name=field_name,
                    text=adapted_field_text,
                    attachments=attachments,
                    _markup_translator=self._markup_translator,
                )
            )

        if note_refactored:
            col.update_note(note=note)

        content = AnkiNoteContent(properties=properties, fields=fields)
        note = AnkiNote(anki_app=self, content=content, markup_translator=self._markup_translator)

        return note

    @staticmethod
    def delete_note_in_anki(note: AnkiNote):
        aqt.mw.col.remove_notes(note_ids=[note.content.properties.note_id])

    @staticmethod
    def show_info(text: str, title: str):
        aqt.utils.showInfo(text=text, title=title)

    @staticmethod
    def show_critical(text: str, title: str):
        aqt.utils.showCritical(text=text, title=title)

    @staticmethod
    def show_tooltip(tip: str):
        aqt.utils.tooltip(tip)

    @staticmethod
    def write_config(config: Dict):
        aqt.mw.addonManager.writeConfig(__name__, config)

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
        action = QAction(title, aqt.mw)
        shortcut = QKeySequence(key_sequence)
        action.setShortcut(shortcut)
        aqt.qconnect(action.triggered, callback)
        aqt.mw.form.menuTools.addAction(action)

    @staticmethod
    def add_sync_hook(hook: Callable):
        aqt.gui_hooks.sync_will_start.append(hook)

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
