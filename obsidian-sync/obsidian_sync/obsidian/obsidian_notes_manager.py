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
import os
import uuid
from pathlib import Path
from typing import Generator, Dict, List, Set

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.addon_metadata import AddonMetadata
from obsidian_sync.anki.app.anki_app import AnkiApp
from obsidian_sync.base_types.note import Note
from obsidian_sync.constants import MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH, DEFAULT_NOTE_ID_FOR_NEW_NOTES
from obsidian_sync.file_utils import clean_string_for_file_name, check_is_srs_file
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.content.obsidian_content import ObsidianNoteContent
from obsidian_sync.obsidian.content.field.obsidian_note_field import ObsidianNoteFieldFactory
from obsidian_sync.obsidian.content.obsidian_reference import ObsidianReferenceFactory
from obsidian_sync.obsidian.obsidian_file import ObsidianNoteFile
from obsidian_sync.obsidian.obsidian_note import ObsidianNote
from obsidian_sync.obsidian.obsidian_notes_result import ObsidianNotesResult
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.utils import format_add_on_message


class ObsidianNotesManager:
    def __init__(
        self,
        anki_app: AnkiApp,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
        obsidian_vault: ObsidianVault,
        metadata: AddonMetadata,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        self._obsidian_vault = obsidian_vault
        self._metadata = metadata
        self._references_factory = ObsidianReferenceFactory(
            obsidian_references_manager=self._obsidian_vault.attachments_manager
        )
        self._field_factory = ObsidianNoteFieldFactory(
            addon_config=addon_config, references_factory=self._references_factory
        )

    def create_new_obsidian_note_from_note(self, reference_note: Note) -> ObsidianNote:
        obsidian_note = ObsidianNote()
        obsidian_note = self._apply_reference_note_onto_obsidian_note(
            obsidian_note=obsidian_note, reference_note=reference_note, obsidian_note_is_new=True
        )
        self._metadata.add_synced_note(note_id=obsidian_note.id, note_path=obsidian_note.file.path)
        return obsidian_note

    def update_obsidian_note_with_note(self, obsidian_note: ObsidianNote, reference_note: Note) -> ObsidianNote:
        obsidian_note = self._apply_reference_note_onto_obsidian_note(
            obsidian_note=obsidian_note, reference_note=reference_note, obsidian_note_is_new=False
        )
        return obsidian_note

    def get_all_obsidian_notes(self, updated_and_new_notes_only: bool = False) -> ObsidianNotesResult:
        previously_synced_notes_found = set()
        existing_notes: Dict[int, ObsidianNote] = {}
        new_notes: List[ObsidianNote] = []
        corrupted_notes: Set[int] = set()

        for note_file in self._get_srs_note_files_in_obsidian():
            try:
                note = ObsidianNote(file=note_file)
            except Exception:
                logging.exception(f"Failed to sync note {note_file.path}.")
                self._anki_app.show_critical(
                    text=format_add_on_message(f"Failed to sync note {note_file.path}."),
                    title="Failed to sync note",
                )
            else:
                note_id_based_on_file_path = self._metadata.get_note_id_from_path(path=note_file.path)
                if note_id_based_on_file_path is not None:
                    previously_synced_notes_found.add(note_id_based_on_file_path)
                if updated_and_new_notes_only:
                    if note_file.path.stat().st_mtime < self._metadata.last_sync_timestamp:
                        continue
                if note.is_corrupt():
                    logging.error(f"Failed to load corrupted note file {note_file.path}.")
                    if note_id_based_on_file_path is not None:
                        corrupted_notes.add(note_id_based_on_file_path)
                    self.delete_note(note=note)
                else:
                    if note.id in existing_notes:
                        self._anki_app.show_critical(
                            text=format_add_on_message(
                                f"Duplicate Anki notes found (note ID {note.properties.note_id}) with paths"
                                f"\n\n{existing_notes[note.properties.note_id].file.path}"
                                f"\n\nand"
                                f"\n\n{note_file.path}"
                                f"\n\nOnly synchronizing {note_file.path}."
                            ),
                            title="Duplicate Anki note templates",
                        )
                    elif note.id == DEFAULT_NOTE_ID_FOR_NEW_NOTES:
                        new_notes.append(note)
                    else:
                        self._metadata.add_synced_note(note_id=note.id, note_path=note.file.path)
                        existing_notes[note.id] = note
                        previously_synced_notes_found.add(note.id)

        deleted_note_ids = self._metadata.anki_notes_synced_to_obsidian.difference(
            previously_synced_notes_found
        )
        return ObsidianNotesResult(
            existing_notes=existing_notes,
            new_notes=new_notes,
            deleted_note_ids=deleted_note_ids,
            corrupted_notes=corrupted_notes,
        )

    def get_note_by_id(self, note_id: int) -> ObsidianNote:
        note_path = self._metadata.get_path_from_note_id(note_id=note_id)
        assert note_path is not None
        file = ObsidianNoteFile(path=note_path, addon_config=self._addon_config, field_factory=self._field_factory)
        note = ObsidianNote(file=file)
        return note

    def delete_note_by_id(self, note_id: int):
        note_path_string = self._metadata.get_path_from_note_id(note_id=note_id)
        if note_path_string is not None and Path(note_path_string).exists():
            note_path = Path(note_path_string)
            self._obsidian_vault.delete_file(
                file=ObsidianNoteFile(
                    path=Path(note_path), addon_config=self._addon_config, field_factory=self._field_factory
                ),
            )
            self._metadata.remove_synced_note(note_id=note_id, note_path=Path(note_path))

    def delete_note(self, note: ObsidianNote):
        note_id = None if note.is_corrupt() else note.id
        note_path = None if note.file is None else note.file.path
        self._metadata.remove_synced_note(note_id=note_id, note_path=note_path)
        self._obsidian_vault.delete_file(file=note.file)

    def _apply_reference_note_onto_obsidian_note(
        self, obsidian_note: ObsidianNote, reference_note: Note, obsidian_note_is_new: bool
    ) -> ObsidianNote:
        if (
            not obsidian_note.is_new()
            and obsidian_note.id in self._metadata.anki_notes_synced_to_obsidian
        ):
            note_id = None if obsidian_note.is_corrupt() else obsidian_note.id
            note_path = None if obsidian_note.file is None else obsidian_note.file.path
            self._metadata.remove_synced_note(note_id=note_id, note_path=note_path)

        file = obsidian_note.file
        if file is None or file.is_corrupt():
            if file is not None:
                self._obsidian_vault.delete_file(file=file)
            note_path = self._build_obsidian_note_path_from_note(
                note=reference_note, new_note=obsidian_note_is_new
            )
            file = ObsidianNoteFile(
                path=note_path,
                addon_config=self._addon_config,
                field_factory=self._field_factory,
            )
            if file.exists:
                self._obsidian_vault.delete_file(file=file)

        content_from_note = ObsidianNoteContent.from_content(
            content=reference_note.content,
            note_path=file.path,
            obsidian_field_factory=self._field_factory,
        )
        if file.content != content_from_note:
            file.content = content_from_note
            self._obsidian_vault.save_file(file=file)

        obsidian_note.file = file

        if not obsidian_note.is_corrupt() and not obsidian_note.is_new():
            self._metadata.add_synced_note(note_id=obsidian_note.id, note_path=obsidian_note.file.path)

        return obsidian_note

    def _build_obsidian_note_path_from_note(self, note: Note, new_note: bool) -> Path:
        note_file_name = self._build_obsidian_note_file_name_from_note_front_field(
            note=note, name_suffix=""
        )
        note_path = self._addon_config.srs_folder / note_file_name

        if new_note and note_path.exists():  # the name is already taken
            note_file_name = self._build_obsidian_note_file_name_from_note_front_field(
                note=note, name_suffix=str(note.content.properties.note_id)
            )
            note_path = self._addon_config.srs_folder / note_file_name

        if new_note and note_path.exists():
            random_name = uuid.uuid4().hex
            note_file_name = self._build_obsidian_note_file_name_from_note_front_field(
                note=note, name_suffix=random_name
            )
            note_path = self._addon_config.srs_folder / note_file_name

        if new_note and note_path.exists():
            raise NotImplementedError

        return note_path

    @staticmethod
    def _build_obsidian_note_file_name_from_note_front_field(note: Note, name_suffix: str) -> str:
        file_extension = ".md"
        name_suffix = f"-{name_suffix}" if name_suffix else ""
        max_file_name = MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH - len(file_extension) - len(name_suffix)
        file_name = note.content.fields[0].to_markdown() or note.content.properties.note_id
        file_name = clean_string_for_file_name(string=file_name)
        file_name = file_name[:max_file_name]
        file_name += name_suffix
        file_name = f"{file_name}{file_extension}"
        return file_name

    def _get_srs_note_files_in_obsidian(
        self, must_exist: bool = False, with_modification_timestamp_past: int = 0
    ) -> Generator[ObsidianNoteFile, None, None]:
        templates_folder_path = self._obsidian_config.templates_folder
        trash_path = self._obsidian_config.trash_folder

        for root, dirs, files in os.walk(self._addon_config.srs_folder):
            if Path(root) in [templates_folder_path, trash_path]:
                continue
            for file in files:
                file_path = Path(root) / file
                if (
                    check_is_srs_file(path=file_path)
                    and (not must_exist or file_path.exists())
                    and (not file_path.exists() or file_path.stat().st_mtime > with_modification_timestamp_past)
                ):
                    obsidian_file = ObsidianNoteFile(
                        path=file_path,
                        addon_config=self._addon_config,
                        field_factory=self._field_factory,
                    )
                    yield obsidian_file
