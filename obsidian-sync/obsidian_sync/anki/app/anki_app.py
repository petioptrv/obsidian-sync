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
from anki.notes import Note as AnkiSystemNote

from obsidian_sync.addon_metadata import AddonMetadata
from obsidian_sync.anki.anki_content import AnkiTemplateContent, \
    AnkiTemplateProperties, AnkiNoteProperties, AnkiNoteContent, AnkiNoteField, AnkiTemplateField, \
    AnkiReferencesFactory
from obsidian_sync.anki.anki_note import AnkiNote
from obsidian_sync.anki.anki_notes_result import AnkiNotesResult
from obsidian_sync.anki.anki_template import AnkiTemplate
from obsidian_sync.anki.app.anki_media_manager import AnkiReferencesManager
from obsidian_sync.base_types.note import Note
from obsidian_sync.constants import ADD_ON_NAME, DEFAULT_NOTE_ID_FOR_NEW_NOTES, ADD_ON_ID


class AnkiApp:
    def __init__(self, metadata: AddonMetadata):
        self._media_manager = AnkiReferencesManager()
        self._references_factory = AnkiReferencesFactory(
            anki_references_manager=self._media_manager,
        )
        self._metadata = metadata

    @property
    def config(self):
        return (
            aqt.mw.addonManager.getConfig(module=ADD_ON_NAME.lower())
            or aqt.mw.addonManager.getConfig(module=__name__)
            or aqt.mw.addonManager.getConfig(module=ADD_ON_ID)
        )

    @property
    def media_manager(self):
        return self._media_manager

    @property
    def anki_user(self) -> str:
        return aqt.mw.pm.name

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

        anki_note = self.update_anki_note_with_note(reference_note=note)

        return anki_note

    def create_new_empty_note_in_anki(self, model_id: int, deck_name: str) -> AnkiNote:
        col = aqt.mw.col

        deck_id = col.decks.add_normal_deck_with_name(name=deck_name).id
        note_type = col.models.get(id=model_id)
        note = col.new_note(notetype=note_type)

        col.add_note(note=note, deck_id=deck_id)

        anki_note = self.get_note_by_id(note_id=note.id)

        return anki_note

    def update_anki_note_with_note(self, reference_note: Note) -> AnkiNote:
        col = aqt.mw.col

        anki_system_note = col.get_note(id=reference_note.content.properties.note_id)
        content_from_note = AnkiNoteContent.from_content(
            content=reference_note.content,
            references_factory=self._references_factory,
        )

        anki_system_note.tags = content_from_note.properties.tags

        note_fields = {
            field.name: field
            for field in content_from_note.fields
        }
        model = col.models.get(id=content_from_note.properties.model_id)
        anki_system_note.fields = [
            note_fields[fld["name"]].to_anki_field_text()
            for fld in model["flds"]
        ]

        col.update_note(note=anki_system_note)

        return self.get_note_by_id(note_id=anki_system_note.id)

    def get_all_notes(self) -> Dict[int, AnkiNote]:
        categorized_notes = self.get_all_notes_categorized()
        anki_notes = {
            note.id: note for note in categorized_notes.new_notes
        }
        anki_notes.update(categorized_notes.updated_notes)
        anki_notes.update(categorized_notes.unchanged_notes)
        return anki_notes

    def get_all_notes_categorized(self) -> AnkiNotesResult:
        col = aqt.mw.col

        new_notes = []
        updated_notes = {}
        unchanged_notes = {}

        last_sync_timestamp = self._metadata.last_sync_timestamp
        note_ids_in_anki = col.find_notes("")

        for note_id in note_ids_in_anki:
            anki_system_note = col.get_note(note_id)
            anki_note = self.get_note_by_id(note_id=note_id)
            if self._get_anki_system_note_creation_timestamp(note=anki_system_note) > last_sync_timestamp:
                new_notes.append(anki_note)
            else:
                modified_timestamp = self._get_anki_system_note_modified_timestamp(note=anki_system_note)
                if modified_timestamp > last_sync_timestamp:
                    updated_notes[anki_note.id] = anki_note
                else:
                    unchanged_notes[anki_note.id] = anki_note

        return AnkiNotesResult(
            new_notes=new_notes, updated_notes=updated_notes, unchanged_notes=unchanged_notes
        )

    def get_note_by_id(self, note_id: int) -> AnkiNote:
        col = aqt.mw.col
        anki_system_note = col.get_note(note_id)

        properties = AnkiNoteProperties(
            model_id=anki_system_note.mid,
            model_name=anki_system_note.note_type()["name"],
            note_id=anki_system_note.id,
            tags=anki_system_note.tags,
            date_modified_in_anki=(
                datetime.fromtimestamp(self._get_anki_system_note_modified_timestamp(note=anki_system_note))
            ),
        )
        fields = []
        model_id = anki_system_note.mid

        note_refactored = False
        for field_name, field_text in anki_system_note.items():
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
            col.update_note(note=anki_system_note)

        content = AnkiNoteContent(properties=properties, fields=fields)
        note = AnkiNote(content=content)

        return note

    def delete_note_in_anki(self, note: AnkiNote):
        self.delete_note_by_id(note_id=note.id)

    @staticmethod
    def delete_note_by_id(note_id: int):
        aqt.mw.col.remove_notes(note_ids=[note_id])

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

    @staticmethod
    def add_profile_opened_hook(hook: Callable):
        aqt.gui_hooks.profile_did_open.append(hook)

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

    def _get_anki_system_note_modified_timestamp(self, note: AnkiSystemNote) -> int:
        return note.mod or self._get_anki_system_note_creation_timestamp(note=note)

    @staticmethod
    def _get_anki_system_note_creation_timestamp(note: AnkiSystemNote) -> int:
        return int(note.id / 1000)
