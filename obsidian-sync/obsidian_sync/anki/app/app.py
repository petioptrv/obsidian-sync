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

from obsidian_sync.anki.content import AnkiTemplateContent, \
    AnkiTemplateProperties, AnkiNoteProperties, AnkiNoteContent, AnkiNoteField, AnkiTemplateField, \
    AnkiReferencesFactory
from obsidian_sync.anki.note import AnkiNote
from obsidian_sync.anki.template import AnkiTemplate
from obsidian_sync.anki.app.media_manager import AnkiReferencesManager
from obsidian_sync.base_types.note import Note
from obsidian_sync.constants import ADD_ON_NAME, DEFAULT_NOTE_ID_FOR_NEW_NOTES


class AnkiApp:
    def __init__(self):
        self._media_manager = AnkiReferencesManager()
        self._references_factory = AnkiReferencesFactory(
            anki_references_manager=self._media_manager,
        )

    @property
    def config(self):
        return aqt.mw.addonManager.getConfig(module=ADD_ON_NAME)

    @property
    def media_manager(self):
        return self._media_manager

    @property
    def addon_config_editor_will_update_json(self) -> List:
        return aqt.gui_hooks.addon_config_editor_will_update_json

    def get_all_anki_templates(self) -> Dict[int, AnkiTemplate]:
        templates = {}
        all_template_ids = [model["id"] for model in aqt.mw.col.models.all()]

        for model_id in all_template_ids:
            template = self.get_anki_template(model_id=model_id)
            templates[model_id] = template

        return templates

    @staticmethod
    def get_anki_template(model_id: int) -> AnkiTemplate:
        model = aqt.mw.col.models.get(id=model_id)
        properties = AnkiTemplateProperties(model_id=model["id"], model_name=model["name"])
        fields = [
            AnkiTemplateField(
                name=field["name"],
                text=field["description"],
            )
            for field in model["flds"]
        ]
        content = AnkiTemplateContent(properties=properties, fields=fields)
        template = AnkiTemplate(content=content)
        return template

    def add_field_to_anki_template(
        self, template: AnkiTemplate, field_name: str, display_on_cards_back_templates: bool
    ) -> AnkiTemplate:
        col = aqt.mw.col
        models = col.models

        new_field = models.new_field(name=field_name)
        model = models.get(id=template.model_id)

        models.add_field(notetype=model, field=new_field)

        if display_on_cards_back_templates:
            for system_template in model["tmpls"]:
                back_template = system_template["afmt"]
                back_template += self._get_back_template_field_entry_string(field_name=field_name)
                system_template["afmt"] = back_template

        models.update_dict(notetype=model)

        updated_template = self.get_anki_template(model_id=template.model_id)
        return updated_template

    def remove_field_from_anki_template(self, template: AnkiTemplate, field_name: str) -> AnkiTemplate:
        col = aqt.mw.col
        models = col.models

        model = models.get(id=template.model_id)

        for system_template in model["tmpls"]:
            back_template = system_template["afmt"]
            back_template_field_entry_string = self._get_back_template_field_entry_string(field_name=field_name)
            if back_template_field_entry_string in back_template:
                system_template["afmt"] = back_template.replace(back_template_field_entry_string, "")

        for field in model["flds"]:
            if field["name"] == field_name:
                models.remove_field(notetype=model, field=field)
                break

        models.update_dict(notetype=model)

        updated_template = self.get_anki_template(model_id=template.model_id)
        return updated_template

    def create_new_note_in_anki_from_note(self, note: Note, deck_name: str) -> AnkiNote:
        assert note.content.properties.note_id == DEFAULT_NOTE_ID_FOR_NEW_NOTES

        anki_note = self.create_new_empty_note_in_anki(model_id=note.content.properties.model_id, deck_name=deck_name)
        note.content.properties.note_id = anki_note.id

        self.update_anki_note_with_note(note=note)

        anki_note = self.get_note_by_id(anki_note.id)

        return anki_note

    def create_new_empty_note_in_anki(self, model_id: int, deck_name: str) -> AnkiNote:
        col = aqt.mw.col

        deck_id = col.decks.add_normal_deck_with_name(name=deck_name).id
        note_type = col.models.get(id=model_id)
        note = col.new_note(notetype=note_type)

        col.add_note(note=note, deck_id=deck_id)

        anki_note = self.get_note_by_id(note_id=note.id)

        return anki_note

    def update_anki_note_with_note(self, note: Note):
        col = aqt.mw.col

        anki_system_note = col.get_note(id=note.content.properties.note_id)
        content_from_note = AnkiNoteContent.from_content(
            content=note.content,
            references_factory=self._references_factory,
        )

        anki_system_note.tags = content_from_note.properties.tags

        cards = anki_system_note.cards()
        anki_system_note_suspended = all(card.queue == QUEUE_TYPE_SUSPENDED for card in cards)
        has_been_suspended = not anki_system_note_suspended and content_from_note.properties.suspended
        has_been_unsuspended = anki_system_note_suspended and not content_from_note.properties.suspended
        if has_been_suspended or has_been_unsuspended:
            for card in anki_system_note.cards():
                card.queue = (
                    QUEUE_TYPE_SUSPENDED
                    if has_been_suspended
                    else card.type
                )
                col.update_card(card=card)

        anki_system_note.fields = [
            field.to_anki_field_text()
            for field in content_from_note.fields
        ]

        col.update_note(note=anki_system_note)

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
            references = self._references_factory.from_card_field_text(
                model_id=model_id, card_field_text=field_text
            )
            adapted_field_text = field_text
            for reference in references:
                adapted_field_text = adapted_field_text.replace(
                    reference.to_anki_field_text(), reference.to_field_text()
                )

            fields.append(
                AnkiNoteField(
                    name=field_name,
                    text=adapted_field_text,
                    references=references,
                )
            )

        if note_refactored:
            col.update_note(note=note)

        content = AnkiNoteContent(properties=properties, fields=fields)
        note = AnkiNote(content=content)

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

    @staticmethod
    def _get_back_template_field_entry_string(field_name: str) -> str:
        return f"\n\n<hr id=\"{field_name}\">\n\n{{{{{field_name}}}}}"
