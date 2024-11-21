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
from pathlib import Path
from typing import Dict, Generator, List, Tuple, Set

from obsidian_sync.anki.app.anki_app import AnkiApp
from obsidian_sync.file_utils import check_is_srs_file, move_file_to_system_trash
from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_attachments_manager import ObsidianAttachmentsManager
from obsidian_sync.obsidian.obsidian_note import ObsidianNote
from obsidian_sync.obsidian.obsidian_file import ObsidianTemplateFile, ObsidianNoteFile
from obsidian_sync.obsidian.obsidian_template import ObsidianTemplate
from obsidian_sync.constants import DEFAULT_NODE_ID_FOR_NEW_NOTES, MARKDOWN_FILE_SUFFIX, \
    OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE, OBSIDIAN_LOCAL_TRASH_OPTION_VALUE, OBSIDIAN_LOCAL_TRASH_FOLDER, \
    OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE, ATTACHMENT_FILE_SUFFIXES
from obsidian_sync.utils import format_add_on_message
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig


class ObsidianVault:
    def __init__(
        self,
        anki_app: AnkiApp,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
        markup_translator: MarkupTranslator,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        self._attachments_manager = ObsidianAttachmentsManager(
            addon_config=addon_config, obsidian_config=obsidian_config
        )
        self._markup_translator = markup_translator

    @property
    def attachments_manager(self) -> ObsidianAttachmentsManager:
        return self._attachments_manager

    def get_all_obsidian_templates(self) -> Dict[int, ObsidianTemplate]:
        self._obsidian_config.templates_folder.mkdir(parents=True, exist_ok=True)
        templates = {}

        for template_file in self._get_srs_template_files_in_obsidian(markup_translator=self._markup_translator):
            try:
                template = ObsidianTemplate(
                    file=template_file,
                    addon_config=self._addon_config,
                    obsidian_vault=self,
                    markup_translator=self._markup_translator,
                )
            except Exception:
                logging.exception(f"Failed to sync note template {template_file.path}.")
                self._anki_app.show_critical(
                    text=format_add_on_message(f"Failed to sync note template {template_file.path}."),
                    title="Failed to sync template",
                )
            else:
                if template.is_corrupt():
                    logging.error(f"Failed to load corrupted template file {template_file.path}.")
                    template.delete()
                else:
                    if template.properties.model_id in templates:
                        self._anki_app.show_critical(
                            text=format_add_on_message(
                                f"Duplicate Anki note templates found (model ID {template.properties.model_id}) with"
                                f" names {templates[template.properties.model_id].file.name} and {template_file.name}."
                                f" Only synchronizing {template_file.name}."
                            ),
                            title="Duplicate Anki note templates",
                        )
                    templates[template.properties.model_id] = template

        return templates

    def get_all_obsidian_notes(self) -> Tuple[Dict[int, ObsidianNote], List[ObsidianNote]]:
        existing_notes: Dict[int, ObsidianNote] = {}
        new_notes: List[ObsidianNote] = []

        for note_file in self._get_srs_note_files_in_obsidian(markup_translator=self._markup_translator):
            try:
                note = ObsidianNote(
                    file=note_file,
                    addon_config=self._addon_config,
                    obsidian_vault=self,
                    markup_translator=self._markup_translator,
                )
            except Exception:
                logging.exception(f"Failed to sync note {note_file.path}.")
                self._anki_app.show_critical(
                    text=format_add_on_message(f"Failed to sync note {note_file.path}."),
                    title="Failed to sync note",
                )
            else:
                if note.is_corrupt():
                    logging.error(f"Failed to load corrupted note file {note_file.path}.")
                    note.delete()
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
                    elif note.id == DEFAULT_NODE_ID_FOR_NEW_NOTES:
                        new_notes.append(note)
                    else:
                        existing_notes[note.properties.note_id] = note

        return existing_notes, new_notes

    def get_all_obsidian_deleted_notes(self) -> Set[int]:
        deleted_notes = set()

        for deleted_file in self._get_deleted_srs_note_files_in_obsidian(markup_translator=self._markup_translator):
            deleted_note = None
            try:
                deleted_note = ObsidianNote(
                    file=deleted_file,
                    addon_config=self._addon_config,
                    obsidian_vault=self,
                    markup_translator=self._markup_translator,
                )
            except Exception:
                logging.exception(f"Failed to sync deleted note {deleted_file.path}.")
                self._anki_app.show_critical(
                    text=format_add_on_message(f"Failed to sync deleted note {deleted_file.path}."),
                    title="Failed to sync deleted note",
                )
            if deleted_note is not None and not deleted_note.is_corrupt():
                deleted_notes.add(deleted_note.properties.note_id)

        return deleted_notes

    def build_template_file_for_model(self, model_name: str) -> ObsidianTemplateFile:
        template_path = (
            self._obsidian_config.templates_folder / f"{model_name}{MARKDOWN_FILE_SUFFIX}"
        )
        file = ObsidianTemplateFile(
            path=template_path,
            obsidian_vault=self,
            markup_translator=self._markup_translator,
        )
        return file

    def delete_file(self, file_path: Path):
        """No need to delete linked resources (images, etc.). We don't know if the resource
        is linked to by other notes and deleting a file in obsidian does not delete the linked
        resources either."""
        trash_option = self._obsidian_config.trash_option

        if trash_option is None or trash_option == OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE:
            move_file_to_system_trash(file_path=file_path)
        elif trash_option == OBSIDIAN_LOCAL_TRASH_OPTION_VALUE:
            self._move_to_local_trash(file_path=file_path)
        elif trash_option == OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE:
            file_path.unlink()
        else:
            raise NotImplementedError  # unrecognized delete option

    def get_path_relative_to_vault(self, absolute_path: Path) -> Path:
        relative_path = absolute_path.relative_to(self._obsidian_config.vault_folder)
        return relative_path

    def _get_srs_template_files_in_obsidian(
        self, markup_translator: MarkupTranslator
    ) -> Generator[ObsidianTemplateFile, None, None]:
        templates_folder_path = self._obsidian_config.templates_folder
        templates_folder_path.mkdir(parents=True, exist_ok=True)

        for file_path in templates_folder_path.iterdir():
            if check_is_srs_file(path=file_path):
                obsidian_file = ObsidianTemplateFile(
                    path=file_path,
                    obsidian_vault=self,
                    markup_translator=markup_translator,
                )
                yield obsidian_file

    def _get_srs_note_files_in_obsidian(
        self, markup_translator: MarkupTranslator
    ) -> Generator[ObsidianNoteFile, None, None]:
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
                        obsidian_vault=self,
                        markup_translator=markup_translator,
                    )
                    yield obsidian_file

    def _get_deleted_srs_note_files_in_obsidian(
        self, markup_translator: MarkupTranslator
    ) -> Generator[ObsidianNoteFile, None, None]:
        trash_path = self._obsidian_config.trash_folder

        if trash_path is not None and trash_path.exists():
            for root, dirs, deleted_files in os.walk(trash_path):
                for deleted_file in deleted_files:
                    deleted_file_path = Path(root) / deleted_file
                    if check_is_srs_file(path=deleted_file_path):
                        obsidian_deleted_note = ObsidianNoteFile(
                            path=deleted_file_path,
                            obsidian_vault=self,
                            markup_translator=markup_translator,
                        )
                        yield obsidian_deleted_note

    def _move_to_local_trash(self, file_path: Path):
        trash_folder = self._addon_config.obsidian_vault_path / OBSIDIAN_LOCAL_TRASH_FOLDER
        trash_folder.mkdir(parents=True, exist_ok=True)
        new_file_path = trash_folder / file_path.name
        file_path.rename(new_file_path)
