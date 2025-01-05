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
import time
from dataclasses import dataclass
from itertools import chain
from typing import Set, Optional

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.addon_metadata import AddonMetadata
from obsidian_sync.anki.anki_notes_result import AnkiNotesResult
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


@dataclass
class SyncCount:
    new: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0


class NotesSynchronizer:
    def __init__(
        self,
        anki_app: AnkiApp,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
        metadata: AddonMetadata,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        obsidian_vault = ObsidianVault(addon_config=addon_config, obsidian_config=obsidian_config)
        self._metadata = metadata
        self._obsidian_notes_manager = ObsidianNotesManager(
            anki_app=anki_app,
            addon_config=addon_config,
            obsidian_config=obsidian_config,
            obsidian_vault=obsidian_vault,
            metadata=self._metadata,
        )
        self._markup_translator = MarkupTranslator()

    def synchronize_notes(self):
        try:
            self._metadata.start_sync()
            if time.time() < self._metadata.last_sync_timestamp:
                time.sleep(1)
            sync_count = SyncCount()
            obsidian_notes = self._obsidian_notes_manager.get_all_notes_categorized()
            anki_notes = self._anki_app.get_all_notes_categorized()

            unchanged_obsidian_note_ids = set(obsidian_notes.unchanged_notes.keys())
            non_new_obsidian_note_ids = unchanged_obsidian_note_ids.union(obsidian_notes.updated_notes.keys())
            unchanged_anki_note_ids = set(anki_notes.unchanged_notes.keys())
            non_new_anki_note_ids = unchanged_anki_note_ids.union(anki_notes.updated_notes.keys())
            
            notes_deleted_in_anki = (  # keep notes that have been deleted in one system but updated in the another
                unchanged_obsidian_note_ids - non_new_anki_note_ids
            )
            notes_deleted_in_obsidian = (  # keep notes that have been deleted in one system but changed in the another
                unchanged_anki_note_ids - non_new_obsidian_note_ids
            )

            self._add_new_anki_notes(anki_notes=anki_notes, obsidian_notes=obsidian_notes, sync_count=sync_count)
            self._add_new_obsidian_notes(obsidian_notes=obsidian_notes, sync_count=sync_count)
            self._remove_deleted_notes(
                obsidian_notes=obsidian_notes,
                notes_deleted_in_anki=notes_deleted_in_anki,
                notes_deleted_in_obsidian=notes_deleted_in_obsidian,
                sync_count=sync_count,
            )
            self._synchronize_changed_notes(
                anki_notes=anki_notes, obsidian_notes=obsidian_notes, sync_count=sync_count
            )

            if self._addon_config.add_obsidian_url_in_anki:
                self._ensure_anki_notes_have_obsidian_uri(obsidian_notes=obsidian_notes, anki_notes=anki_notes)

            self._anki_app.show_tooltip(
                tip=format_add_on_message(
                    f"Synced {sync_count.new} new,"
                    f" {sync_count.updated} updated,"
                    f" {sync_count.deleted} deleted,"
                    f" and {sync_count.unchanged} unchanged notes successfully."
                )
            )
            self._metadata.commit_sync()
        except Exception as e:
            logging.exception("Failed to sync notes.")
            self._anki_app.show_critical(
                text=format_add_on_message(f"Obsidian sync error: {str(e)}"),
                title=ADD_ON_NAME,
            )

    def _add_new_anki_notes(
        self, anki_notes: AnkiNotesResult, obsidian_notes: ObsidianNotesResult, sync_count: SyncCount
    ):
        for anki_note in anki_notes.new_notes:
            obsidian_note = (
                obsidian_notes.unchanged_notes.pop(anki_note.id, None)
                or obsidian_notes.updated_notes.pop(anki_note.id, None)
            )
            if obsidian_note is not None:  # This can happen after a backup recovery in Anki, so we replace the existing note in Obsidian from previous syncs with the newly recovered version.
                self._obsidian_notes_manager.delete_note(note=obsidian_note)
            anki_note = self._sanitize_anki_note(anki_note=anki_note)
            obsidian_note = self._obsidian_notes_manager.create_new_obsidian_note_from_note(
                reference_note=anki_note
            )
            if self._addon_config.add_obsidian_url_in_anki:
                self._update_anki_note_with_obsidian_notes(obsidian_note=obsidian_note, sanitize=False)
            sync_count.new += 1

    def _add_new_obsidian_notes(self, obsidian_notes: ObsidianNotesResult, sync_count: SyncCount):
        for obsidian_note in obsidian_notes.new_notes:
            obsidian_note = self._sanitize_obsidian_note(obsidian_note=obsidian_note)
            if obsidian_note is not None:
                anki_note = self._anki_app.create_new_note_in_anki_from_note(
                    note=obsidian_note, deck_name=self._addon_config.anki_deck_name_for_obsidian_imports
                )
                self._obsidian_notes_manager.update_obsidian_note_with_note(  # update note ID and timestamps
                    obsidian_note=obsidian_note, reference_note=anki_note
                )
                sync_count.new += 1

    def _remove_deleted_notes(
        self,
        obsidian_notes: ObsidianNotesResult,
        notes_deleted_in_anki: Set[int],
        notes_deleted_in_obsidian: Set[int],
        sync_count: SyncCount,
    ):
        for note_id in notes_deleted_in_anki:
            obsidian_note = (
                obsidian_notes.unchanged_notes.pop(note_id, None)
                or obsidian_notes.updated_notes.pop(note_id)
            )
            self._obsidian_notes_manager.delete_note(note=obsidian_note)
            sync_count.deleted += 1
        for note_id in notes_deleted_in_obsidian:
            self._anki_app.delete_note_by_id(note_id=note_id)
            sync_count.deleted += 1

    def _synchronize_changed_notes(
        self, anki_notes: AnkiNotesResult, obsidian_notes: ObsidianNotesResult, sync_count: SyncCount
    ):
        changes_in_anki = set(anki_notes.updated_notes.keys())
        changes_in_obsidian = set(obsidian_notes.updated_notes.keys())
        changes_in_both_systems = changes_in_anki.intersection(changes_in_obsidian)

        for note_id in changes_in_both_systems:
            anki_note = anki_notes.updated_notes[note_id]
            obsidian_note = obsidian_notes.updated_notes[note_id]
            if obsidian_note.is_corrupt():
                obsidian_note = self._fix_corrupted_obsidian_note(obsidian_note=obsidian_note, anki_note=anki_note)
            self._synchronize_note_pair(obsidian_note=obsidian_note, anki_note=anki_note)
            sync_count.updated += 1

        changes_in_anki_only = changes_in_anki - changes_in_both_systems
        for note_id in changes_in_anki_only:
            anki_note = anki_notes.updated_notes[note_id]
            obsidian_note = obsidian_notes.unchanged_notes[note_id]
            if obsidian_note.is_corrupt():
                obsidian_note = self._fix_corrupted_obsidian_note(obsidian_note=obsidian_note, anki_note=anki_note)
            self._obsidian_notes_manager.update_obsidian_note_with_note(
                obsidian_note=obsidian_note,
                reference_note=anki_notes.updated_notes[note_id],
            )
            sync_count.updated += 1

        changes_in_obsidian_only = changes_in_obsidian - changes_in_both_systems
        for note_id in changes_in_obsidian_only:
            anki_note = anki_notes.unchanged_notes.get(note_id, None)
            obsidian_note = obsidian_notes.updated_notes[note_id]
            if anki_note is None:
                relative_obsidian_note_path = self._obsidian_notes_manager.get_relative_note_path(
                    note=obsidian_note
                )
                self._anki_app.show_critical(
                    text=(
                        f"The Obsidian note {relative_obsidian_note_path} is no longer found in Anki but"
                        f" has been updated in Obsidian since the last sync. Once the sync is over, review the note and"
                        f" manually resolve the discrepancy."
                    ),
                    title=ADD_ON_NAME,
                )
            else:
                if obsidian_note.is_corrupt():
                    obsidian_note = self._fix_corrupted_obsidian_note(obsidian_note=obsidian_note, anki_note=anki_note)
                self._update_anki_note_with_obsidian_notes(obsidian_note=obsidian_note)
                sync_count.updated += 1

    def _synchronize_note_pair(self, anki_note: AnkiNote, obsidian_note: ObsidianNote):
        self._obsidian_notes_manager.update_obsidian_note_with_note(  # Anki takes precedence because off-loading and re-downloading Obsidian files synced with iCloud updates their last-modified timestamp
            obsidian_note=obsidian_note, reference_note=anki_note,
        )

    def _update_anki_note_with_obsidian_notes(self, obsidian_note: ObsidianNote, sanitize: bool = True):
        if sanitize:
            obsidian_note = self._sanitize_obsidian_note(obsidian_note=obsidian_note)
        if obsidian_note is not None:
            anki_note = self._anki_app.update_anki_note_with_note(reference_note=obsidian_note)
            self._obsidian_notes_manager.update_obsidian_note_with_note(  # update timestamps
                obsidian_note=obsidian_note, reference_note=anki_note
            )

    def _sanitize_anki_note(self, anki_note: AnkiNote) -> AnkiNote:
        refactored = False

        for field in anki_note.content.fields:
            original_field_html = field.to_html()
            sanitized_field_html = self._markup_translator.sanitize_html(html=original_field_html)
            if sanitized_field_html != original_field_html:
                field.set_from_html(html=sanitized_field_html)
                refactored = True

        if refactored:
            anki_note = self._anki_app.update_anki_note_with_note(reference_note=anki_note)

        return anki_note

    def _sanitize_obsidian_note(self, obsidian_note: ObsidianNote) -> Optional[ObsidianNote]:
        refactored = False

        try:
            for field in obsidian_note.content.fields:
                sanitized_field_markdown = self._markup_translator.sanitize_markdown(markdown=field.to_markdown())
                if field.to_markdown() != sanitized_field_markdown:
                    field.set_from_markdown(markdown=sanitized_field_markdown)
                    refactored = True
        except Exception as e:
            relative_path = self._obsidian_notes_manager.get_relative_note_path(note=obsidian_note)
            self._anki_app.show_critical(
                text=f"The newly created Obsidian note {relative_path} failed parsing with error: {str(e)}.",
                title=ADD_ON_NAME,
            )
            obsidian_note = None
        else:
            if refactored:
                obsidian_note = self._obsidian_notes_manager.update_obsidian_note_with_note(
                    obsidian_note=obsidian_note, reference_note=obsidian_note
                )

        return obsidian_note

    def _ensure_anki_notes_have_obsidian_uri(self, anki_notes: AnkiNotesResult, obsidian_notes: ObsidianNotesResult):
        for note_id, anki_note in chain(anki_notes.updated_notes.items(), anki_notes.unchanged_notes.items()):
            has_obsidian_uri = any(
                field.name == OBSIDIAN_LINK_URL_FIELD_NAME
                and not len(field.text) == 0
                for field in anki_note.content.fields
            )
            if not has_obsidian_uri:
                obsidian_note = (
                    obsidian_notes.unchanged_notes.get(note_id, None)
                    or obsidian_notes.updated_notes[note_id]
                )
                if obsidian_note.is_corrupt():
                    obsidian_note = self._fix_corrupted_obsidian_note(obsidian_note=obsidian_note, anki_note=anki_note)
                self._anki_app.update_anki_note_with_note(reference_note=obsidian_note)

    def _fix_corrupted_obsidian_note(self, obsidian_note: ObsidianNote, anki_note: AnkiNote) -> ObsidianNote:
        self._obsidian_notes_manager.delete_note(note=obsidian_note)
        obsidian_note = self._obsidian_notes_manager.create_new_obsidian_note_from_note(
            reference_note=anki_note,
        )
        return obsidian_note
