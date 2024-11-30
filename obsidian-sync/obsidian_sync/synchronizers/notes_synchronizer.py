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

import logging
from typing import Dict

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.addon_metadata import AddonMetadata
from obsidian_sync.anki.anki_note_changes import AnkiNoteChanges
from obsidian_sync.anki.app.anki_app import AnkiApp
from obsidian_sync.anki.anki_note import AnkiNote
from obsidian_sync.constants import ADD_ON_NAME, OBSIDIAN_LINK_URL_FIELD_NAME
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_note import ObsidianNote
from obsidian_sync.obsidian.obsidian_notes_manager import ObsidianNotesManager
from obsidian_sync.obsidian.obsidian_notes_result import ObsidianNotesResult
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.utils import format_add_on_message


class NotesSynchronizer:
    def __init__(
        self,
        anki_app: AnkiApp,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        obsidian_vault = ObsidianVault(addon_config=addon_config, obsidian_config=obsidian_config)
        self._metadata = AddonMetadata()
        self._obsidian_notes_manager = ObsidianNotesManager(
            anki_app=anki_app,
            addon_config=addon_config,
            obsidian_config=obsidian_config,
            obsidian_vault=obsidian_vault,
            metadata=self._metadata,
        )
        self._markup_translator = MarkupTranslator()

        self._anki_app.set_metadata(metadata=self._metadata)

    def synchronize_notes(self):
        self._metadata.start_sync()
        try:
            anki_note_changes = self._anki_app.get_note_changes()
            updated_and_new_notes_only = True
            if self._addon_config.add_obsidian_url_in_anki and not self._check_obsidian_urls_are_synced_to_anki():
                updated_and_new_notes_only = False  # Obsidian URI need to be synced
            obsidian_note_changes = self._obsidian_notes_manager.get_all_obsidian_notes(
                updated_and_new_notes_only=updated_and_new_notes_only
            )

            self._add_new_anki_notes(anki_note_changes=anki_note_changes)
            self._add_new_obsidian_notes(obsidian_note_changes=obsidian_note_changes)
            self._remove_deleted_notes(anki_note_changes=anki_note_changes, obsidian_note_changes=obsidian_note_changes)
            self._synchronize_changed_notes(
                anki_note_changes=anki_note_changes, obsidian_note_changes=obsidian_note_changes
            )
            self._fix_corrupted_obsidian_notes(obsidian_note_changes=obsidian_note_changes)

            self._anki_app.show_tooltip(tip=format_add_on_message("Notes synced successfully."))
        except Exception as e:
            logging.exception("Failed to sync notes.")
            self._anki_app.show_critical(
                text=format_add_on_message(f"Obsidian sync error: {str(e)}"),
                title=ADD_ON_NAME,
            )

        self._metadata.obsidian_urls_are_synced = self._addon_config.add_obsidian_url_in_anki
        self._metadata.commit_sync()

    def _add_new_anki_notes(self, anki_note_changes: AnkiNoteChanges):
        for anki_note in anki_note_changes.new_notes:
            anki_note = self._sanitize_anki_note(anki_note=anki_note)
            obsidian_note = self._obsidian_notes_manager.create_new_obsidian_note_from_note(
                reference_note=anki_note
            )
            if self._addon_config.add_obsidian_url_in_anki:
                self._update_anki_note_with_obsidian_notes(obsidian_note=obsidian_note)

    def _add_new_obsidian_notes(self, obsidian_note_changes: ObsidianNotesResult):
        for obsidian_note in obsidian_note_changes.new_notes:
            obsidian_note = self._sanitize_obsidian_note(obsidian_note=obsidian_note)
            anki_note = self._anki_app.create_new_note_in_anki_from_note(
                note=obsidian_note, deck_name=self._addon_config.anki_deck_name_for_obsidian_imports
            )
            self._obsidian_notes_manager.update_obsidian_note_with_note(  # update note ID and timestamps
                obsidian_note=obsidian_note, reference_note=anki_note
            )

    def _remove_deleted_notes(self, anki_note_changes: AnkiNoteChanges, obsidian_note_changes: ObsidianNotesResult):
        for deleted_note_id in anki_note_changes.deleted_note_ids:
            obsidian_note_changes.existing_notes.pop(deleted_note_id, None)
            self._obsidian_notes_manager.delete_note_by_id(note_id=deleted_note_id)

        for deleted_note_id in obsidian_note_changes.deleted_note_ids:
            anki_note_changes.updated_notes.pop(deleted_note_id, None)
            self._anki_app.delete_note_by_id(note_id=deleted_note_id)
            self._metadata.remove_synced_note(note_id=deleted_note_id, note_path=None)

    def _synchronize_changed_notes(self, anki_note_changes: AnkiNoteChanges, obsidian_note_changes: ObsidianNotesResult):
        changes_in_anki = set(anki_note_changes.updated_notes.keys())
        changes_in_obsidian = set(obsidian_note_changes.existing_notes.keys())
        changes_in_both_systems = changes_in_anki.intersection(changes_in_obsidian)

        for note_id in changes_in_both_systems:
            self._synchronize_note_pair(
                anki_note=anki_note_changes.updated_notes[note_id],
                obsidian_note=obsidian_note_changes.existing_notes[note_id],
            )

        changes_in_anki_only = changes_in_anki - changes_in_both_systems
        for note_id in changes_in_anki_only:
            self._obsidian_notes_manager.update_obsidian_note_with_note(
                obsidian_note=self._obsidian_notes_manager.get_note_by_id(note_id=note_id),
                reference_note=anki_note_changes.updated_notes[note_id],
            )

        changes_in_obsidian_only = changes_in_obsidian - changes_in_both_systems
        for note_id in changes_in_obsidian_only:
            obsidian_note = obsidian_note_changes.existing_notes[note_id]
            self._update_anki_note_with_obsidian_notes(obsidian_note=obsidian_note)

    def _fix_corrupted_obsidian_notes(self, obsidian_note_changes: ObsidianNotesResult):
        for note_id in obsidian_note_changes.corrupted_notes:
            self._obsidian_notes_manager.delete_note_by_id(note_id=note_id)
            self._obsidian_notes_manager.create_new_obsidian_note_from_note(
                reference_note=self._anki_app.get_note_by_id(note_id=note_id),
            )

    def _synchronize_note_pair(self, anki_note: AnkiNote, obsidian_note: ObsidianNote):
        anki_note_date_modified = anki_note.content.properties.date_modified_in_anki.timestamp()
        obsidian_note_date_modified_in_anki = obsidian_note.content.properties.date_modified_in_anki.timestamp()
        last_sync = obsidian_note.content.properties.date_synced.timestamp()
        obsidian_note_file_date_modified = obsidian_note.file.path.stat().st_mtime

        if anki_note_date_modified != obsidian_note_date_modified_in_anki:
            if anki_note_date_modified > obsidian_note_file_date_modified:
                anki_note = self._sanitize_anki_note(anki_note=anki_note)
                self._obsidian_notes_manager.update_obsidian_note_with_note(
                    obsidian_note=obsidian_note, reference_note=anki_note
                )
            else:
                self._update_anki_note_with_obsidian_notes(obsidian_note=obsidian_note)
        elif obsidian_note_file_date_modified > last_sync + 1:  # this also covers Obsidian properties updates
            self._update_anki_note_with_obsidian_notes(obsidian_note=obsidian_note)
        elif anki_note.content.properties != obsidian_note.content.properties:  # for props like max difficulty
            anki_note = self._sanitize_anki_note(anki_note=anki_note)
            self._obsidian_notes_manager.update_obsidian_note_with_note(
                obsidian_note=obsidian_note, reference_note=anki_note
            )
        if self._addon_config.add_obsidian_url_in_anki:
            anki_note_obsidian_url_field = next(
                f for f in anki_note.content.fields if f.name == OBSIDIAN_LINK_URL_FIELD_NAME
            )
            obsidian_note_obsidian_url_field = next(
                f for f in obsidian_note.content.fields if f.name == OBSIDIAN_LINK_URL_FIELD_NAME
            )
            if anki_note_obsidian_url_field.to_markdown() != obsidian_note_obsidian_url_field.to_markdown():
                self._update_anki_note_with_obsidian_notes(obsidian_note=obsidian_note)

    def _update_anki_note_with_obsidian_notes(self, obsidian_note: ObsidianNote):
        obsidian_note = self._sanitize_obsidian_note(obsidian_note=obsidian_note)
        anki_note = self._anki_app.update_anki_note_with_note(note=obsidian_note)
        self._obsidian_notes_manager.update_obsidian_note_with_note(  # update timestamps
            obsidian_note=obsidian_note, reference_note=anki_note
        )

    def _sanitize_anki_notes(self, anki_notes: Dict[int, AnkiNote]) -> Dict[int, AnkiNote]:
        for note_id in list(anki_notes.keys()):
            anki_note = anki_notes[note_id]
            anki_notes[note_id] = self._sanitize_anki_note(anki_note=anki_note)

        return anki_notes

    def _sanitize_anki_note(self, anki_note: AnkiNote) -> AnkiNote:
        refactored = False

        for field in anki_note.content.fields:
            original_field_html = field.to_html()
            sanitized_field_html = self._markup_translator.sanitize_html(html=original_field_html)
            if sanitized_field_html != original_field_html:
                field.set_from_html(html=sanitized_field_html)
                refactored = True

        if refactored:
            anki_note = self._anki_app.update_anki_note_with_note(note=anki_note)

        return anki_note

    def _sanitize_obsidian_note(self, obsidian_note: ObsidianNote) -> ObsidianNote:
        refactored = False

        for field in obsidian_note.content.fields:
            sanitized_field_markdown = self._markup_translator.sanitize_markdown(markdown=field.to_markdown())
            if field.to_markdown() != sanitized_field_markdown:
                field.set_from_markdown(markdown=sanitized_field_markdown)
                refactored = True

        if refactored:
            obsidian_note = self._obsidian_notes_manager.update_obsidian_note_with_note(
                obsidian_note=obsidian_note, reference_note=obsidian_note
            )

        return obsidian_note

    def _check_obsidian_urls_are_synced_to_anki(self) -> bool:
        urls_are_synced = False
        synced_notes = self._metadata.anki_notes_synced_to_obsidian
        notes_checked = 0

        while not urls_are_synced and len(synced_notes) > 0 and notes_checked != 10:
            note_id = synced_notes.pop()
            anki_note = self._anki_app.get_note_by_id(note_id=note_id)
            obsidian_uri_field = next(
                field
                for field in anki_note.content.fields
                if field.name == OBSIDIAN_LINK_URL_FIELD_NAME
            )
            urls_are_synced = len(obsidian_uri_field.references[0].to_field_text()) != 0

        return urls_are_synced
