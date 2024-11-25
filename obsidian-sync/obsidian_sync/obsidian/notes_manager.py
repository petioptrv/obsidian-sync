import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Dict, List, Set

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.addon_metadata import AddonMetadata
from obsidian_sync.anki.app.app import AnkiApp
from obsidian_sync.base_types.note import Note
from obsidian_sync.constants import MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH, DEFAULT_NOTE_ID_FOR_NEW_NOTES
from obsidian_sync.file_utils import clean_string_for_file_name, check_is_srs_file
from obsidian_sync.obsidian.config import ObsidianConfig
from obsidian_sync.obsidian.content.content import ObsidianNoteContent
from obsidian_sync.obsidian.file import ObsidianNoteFile
from obsidian_sync.obsidian.note import ObsidianNote
from obsidian_sync.obsidian.vault import ObsidianVault
from obsidian_sync.utils import format_add_on_message


class ObsidianNotesManager:
    def __init__(
        self,
        anki_app: AnkiApp,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
        obsidian_vault: ObsidianVault,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        self._obsidian_vault = obsidian_vault
        self._metadata = AddonMetadata()

    def __enter__(self) -> "ObsidianNotesManager":
        self.start_sync()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit_sync()

    def start_sync(self):
        self._metadata.start_sync()

    def commit_sync(self):
        self._metadata.commit_sync()

    def create_new_obsidian_note_from_note(self, reference_note: Note) -> ObsidianNote:
        obsidian_note = ObsidianNote()
        obsidian_note = self.update_obsidian_note_with_note(obsidian_note=obsidian_note, reference_note=reference_note)
        self._metadata.add_synced_note(note=obsidian_note)
        return obsidian_note

    def update_obsidian_note_with_note(self, obsidian_note: ObsidianNote, reference_note: Note) -> ObsidianNote:
        if (
            not obsidian_note.is_new()
            and obsidian_note.id in self._metadata.anki_notes_synced_to_obsidian
        ):
            self._metadata.remove_synced_note(note=obsidian_note)

        file = obsidian_note.file
        if file is None or file.is_corrupt():
            if file is not None:
                self._obsidian_vault.delete_file(file=file)
            note_path = self._build_obsidian_note_path_from_note(note=reference_note)
            file = ObsidianNoteFile(
                path=note_path,
                attachment_manager=self._obsidian_vault.attachments_manager,
                addon_config=self._addon_config,
            )
            if file.exists:
                self._obsidian_vault.delete_file(file=file)

        content_from_note = ObsidianNoteContent.from_content(
            content=reference_note.content,
            obsidian_attachments_manager=self._obsidian_vault.attachments_manager,
            note_path=file.path,
        )
        if file.content != content_from_note:
            file.content = content_from_note
            self._obsidian_vault.save_file(file=file)

        obsidian_note.file = file

        self._metadata.add_synced_note(note=obsidian_note)

        return obsidian_note

    def get_all_obsidian_notes(self) -> "ObsidianNotesResult":
        existing_notes: Dict[int, ObsidianNote] = {}
        new_notes: List[ObsidianNote] = []

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
                if note.is_corrupt():
                    logging.error(f"Failed to load corrupted note file {note_file.path}.")
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
                        existing_notes[note.properties.note_id] = note

        deleted_note_ids = self._metadata.anki_notes_synced_to_obsidian.difference(
            set(existing_notes.keys())
        )
        return ObsidianNotesResult(
            existing_obsidian_notes=existing_notes,
            new_obsidian_notes=new_notes,
            deleted_note_ids=deleted_note_ids,
        )

    def delete_note(self, note: ObsidianNote):
        self._metadata.remove_synced_note(note=note)
        self._obsidian_vault.delete_file(file=note.file)

    def _build_obsidian_note_path_from_note(self, note: Note) -> Path:
        note_file_name = self._build_obsidian_note_file_name_from_note(note=note)
        note_path = self._addon_config.srs_folder / note_file_name
        return note_path

    @staticmethod
    def _build_obsidian_note_file_name_from_note(note: Note) -> str:
        suffix = ".md"
        max_file_name = MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH - len(suffix)
        file_name = note.content.fields[0].to_markdown() or note.content.properties.note_id
        file_name = clean_string_for_file_name(string=file_name)
        file_name = file_name[:max_file_name]
        file_name = f"{file_name}{suffix}"
        return file_name

    def _get_srs_note_files_in_obsidian(self) -> Generator[ObsidianNoteFile, None, None]:
        templates_folder_path = self._obsidian_config.templates_folder
        trash_path = self._obsidian_config.trash_folder

        for root, dirs, files in os.walk(self._addon_config.srs_folder):
            if Path(root) in [templates_folder_path, trash_path]:
                continue
            for file in files:
                file_path = Path(root) / file
                if check_is_srs_file(path=file_path):
                    obsidian_file = ObsidianNoteFile(
                        path=file_path,
                        attachment_manager=self._obsidian_vault.attachments_manager,
                        addon_config=self._addon_config,
                    )
                    yield obsidian_file


@dataclass
class ObsidianNotesResult:
    existing_obsidian_notes: Dict[int, ObsidianNote]
    new_obsidian_notes: List[ObsidianNote]
    deleted_note_ids: Set[int]
