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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Set, Optional, List

from aqt import mw
from anki.notes import Note as ANote
from aqt.utils import showCritical

from .obsidian.obsidian_file import ObsidianFile
from .addon_config import AddonConfig
from .constants import DEFAULT_NODE_ID_FOR_NEW_OBSIDIAN_NOTES
from .builders.obsidian_note_builder import ObsidianNoteBuilder
from .constants import ADD_ON_NAME, DATETIME_FORMAT, MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH
from .change_log import ChangeLogBase
from .markdown import markdown
from .markdownify.markdownify import markdownify as md
from .parsers.obsidian_note_parser import ObsidianNoteParser
from .utils import is_markdown_file, format_add_on_message, delete_obsidian_note, clean_string_for_file_name


@dataclass
class NoteImage:
    anki_path: Optional[Path]
    obsidian_path: Optional[Path]

    # def sync_image(self, ):


@dataclass
class NoteField:
    name: str
    text: str
    images: [NoteImage]


@dataclass
class Note:
    note_id: int
    model_id: int
    fields: [NoteField]
    tags: Set[str]
    deck: str
    modified_dt: datetime


@dataclass
class AnkiNote(Note):
    @classmethod
    def from_anki_note(cls, note: ANote) -> "AnkiNote":
        field_names = cls.get_field_names(model_id=note.mid)
        fields = [
            NoteField(
                name=name,
                text=text,
                images=cls._extract_anki_image_paths_from_field_text(field_text=text),
            ) for name, text in zip(field_names, note.fields)
        ]
        note = AnkiNote(
            note_id=note.id,
            model_id=note.mid,
            fields=fields,
            tags=set(note.tags),
            deck=mw.col.decks.name(note.cards()[0].did),
            modified_dt=datetime.fromtimestamp(note.mod),
        )
        return note

    @classmethod
    def _extract_anki_image_paths_from_field_text(cls, field_text: str) -> List[Path]:
        return []

    @classmethod
    def get_field_names(cls, model_id: int) -> [str]:
        model = mw.col.models.get(id=model_id)
        field_names = mw.col.models.field_names(model)
        return field_names

    @classmethod
    def create_in_anki_from_obsidian(cls, obsidian_note: "ObsidianNote", change_log: ChangeLogBase) -> "AnkiNote":
        deck_id = mw.col.decks.id(name=obsidian_note.deck)
        field_names = cls.get_field_names(model_id=obsidian_note.model_id)
        model = mw.col.models.get(id=obsidian_note.model_id)

        note = ANote(col=mw.col, model=model)
        note.note_type()["did"] = deck_id

        for field_name, field_value in zip(field_names, obsidian_note.fields):
            note[field_name] = field_value

        mw.col.add_note(note=note, deck_id=deck_id)
        mw.col.update_note(note=note)

        anki_note = AnkiNote.from_anki_note(note=note)
        anki_note.modified_dt = datetime.now()

        obsidian_note.update_with_anki_note(  # update note ID in Obsidian
            anki_note=anki_note, change_log=change_log, print_to_log=False
        )

        change_log.log_change(change=f"Created Anki note from obsidian note {obsidian_note.note_path.file_name}.")

        return anki_note

    def update_with_obsidian_note(self, obsidian_note: "ObsidianNote", changes_log: ChangeLogBase, print_to_log: bool):
        if obsidian_note.updated_since_last_sync:
            self.deck = obsidian_note.deck
            self.fields = obsidian_note.fields
            self._update_anki_note()
            self.modified_dt = datetime.now()
            obsidian_note.update_with_anki_note(anki_note=self, change_log=changes_log, print_to_log=False)
            if print_to_log:
                changes_log.log_change(
                    change=f"Updated Anki note {self.note_id} with change in {obsidian_note.note_path.file_name}."
                )

    def delete(self, change_log: ChangeLogBase):
        mw.col.remove_notes(note_ids=[self.note_id])
        change_log.log_change(change=f"Deleted Anki note {self.note_id}.")

    def _update_anki_note(self):
        note = mw.col.get_note(id=self.note_id)
        deck_name = mw.col.decks.name(note.cards()[0].did)

        if self.deck != deck_name:
            new_deck = mw.col.decks.add_normal_deck_with_name(name=self.deck)
            mw.col.set_deck(card_ids=[card.id for card in note.cards()], deck_id=new_deck.id)

        for field in self.fields:
            note[field.name] = field.text

        note.flush()


@dataclass
class ObsidianNotePath:
    file_name: str
    absolute_path: Path
    relative_path: Path

    @classmethod
    def build_from_file_path(
        cls, file_path: Path, addon_config: AddonConfig
    ) -> "ObsidianNotePath":
        note_path = ObsidianNotePath(
            file_name=file_path.name,
            absolute_path=file_path,
            relative_path=Path(os.path.relpath(path=file_path, start=addon_config.srs_folder)),
        )
        return note_path


@dataclass
class ObsidianNote(Note):
    synced_dt: datetime
    note_path: ObsidianNotePath
    _obsidian_note_builder: ObsidianNoteBuilder
    _addon_config: AddonConfig

    @property
    def updated_since_last_sync(self) -> bool:
        return self.note_path.absolute_path.stat().st_mtime > self.synced_dt.timestamp() + 1

    @property
    def new_note(self) -> bool:
        return self.note_id == DEFAULT_NODE_ID_FOR_NEW_OBSIDIAN_NOTES

    @classmethod
    def build_from_file(
        cls,
        addon_config: AddonConfig,
        obsidian_file: ObsidianFile,
    ) -> Optional["ObsidianNote"]:
        note = None

        if is_markdown_file(path=file_path):
            with open(file_path, "r") as f:
                note_content = f.read()
            if obsidian_file.is_anki_file_in_obsidian:
                try:
                    note_path = ObsidianNotePath.build_from_file_path(
                        file_path=file_path, addon_config=addon_config
                    )
                    note = cls._parse_obsidian_note(
                        addon_config=addon_config,
                        obsidian_note_parser=obsidian_note_parser,
                        obsidian_note_builder=obsidian_note_builder,
                        note_path=note_path,
                        note_content=note_content,
                    )
                    note._validate_fields_are_html()
                except Exception:
                    logging.exception("Failed to parse note")
                    showCritical(
                        text=format_add_on_message(
                            f"Failed to parse Obsidian note {file_path.name}."
                            f" If the note exists in Anki, the file will be updated."
                            f" Otherwise, it will be ignored."
                        ),
                        title=ADD_ON_NAME,
                    )

        return note

    @classmethod
    def create_note_file_from_anki_note(
        cls,
        addon_config: AddonConfig,
        obsidian_note_builder: ObsidianNoteBuilder,
        anki_note: AnkiNote,
        change_log: ChangeLogBase,
    ):
        folder_path = obsidian_note_builder.build_obsidian_note_folder_path_from_deck(deck=anki_note.deck)
        file_name = cls.build_obsidian_note_file_name_from_anki_note(anki_note=anki_note)
        note_path = ObsidianNotePath.build_from_file_path(
            file_path=folder_path / file_name, addon_config=addon_config
        )
        obsidian_note = ObsidianNote(
            note_id=anki_note.note_id,
            model_id=anki_note.model_id,
            fields=anki_note.fields,
            tags=anki_note.tags,
            deck=anki_note.deck,
            modified_dt=anki_note.modified_dt,
            synced_dt=datetime.now(),
            note_path=note_path,
            _obsidian_note_builder=obsidian_note_builder,
            _addon_config=addon_config,
        )
        obsidian_note._store_to_file()
        change_log.log_change(change=f"{note_path.file_name} was created.")

    @classmethod
    def build_obsidian_note_file_name_from_anki_note(cls, anki_note: AnkiNote) -> str:
        first_field = anki_note.fields[0].text[:MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH]
        first_field_clean = md(html=first_field)
        first_field_clean = clean_string_for_file_name(string=first_field_clean)
        max_file_name_length = MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH
        suffix = ".md"
        name = first_field_clean[:(max_file_name_length - len(suffix))] + suffix
        return name

    def update_with_anki_note(self, anki_note: AnkiNote, change_log: ChangeLogBase, print_to_log: bool):
        if (
            (
                anki_note.modified_dt > datetime.fromtimestamp(0)
                and anki_note.modified_dt > self.modified_dt
            ) or self.new_note  # not yet associated to an Anki note
        ):
            if self.updated_since_last_sync:
                self._perform_update_with_anki_note(
                    anki_note=anki_note, change_log=change_log, print_to_log=print_to_log
                )
            else:
                self._perform_update_with_anki_note(
                    anki_note=anki_note, change_log=change_log, print_to_log=print_to_log
                )

    def delete_file(self, change_log: ChangeLogBase):
        delete_obsidian_note(
            obsidian_vault=self._config_handler.obsidian_vault_path, obsidian_note_path=self.note_path.absolute_path
        )
        change_log.log_change(change=f"{self.note_path.relative_path} was deleted.")

    @classmethod
    def _parse_obsidian_note(
        cls,
        addon_config: AddonConfig,
        obsidian_note_parser: ObsidianNoteParser,
        obsidian_note_builder: ObsidianNoteBuilder,
        note_path: ObsidianNotePath,
        note_content: str,
    ) -> "ObsidianNote":
        deck = obsidian_note_parser.parse_deck_from_obsidian_note_path(file_path=note_path.absolute_path)
        fields = [
            NoteField(
                name=name,
                text=text,
                images=[
                    NoteImage(anki_path=None, obsidian_path=image_path)
                    for image_path in image_paths
                ]
            ) for name, text, image_paths in obsidian_note_parser.get_field_names_text_and_images_from_obsidian_note_content(
                content=note_content
            )
        ]
        note = ObsidianNote(
            note_id=obsidian_note_parser.get_note_id_from_obsidian_note_content(content=note_content),
            model_id=obsidian_note_parser.get_model_id_from_obsidian_note_content(content=note_content),
            fields=fields,
            tags=obsidian_note_parser.get_tags_from_obsidian_note_content(content=note_content),
            deck=deck,
            modified_dt=obsidian_note_parser.get_modified_dt(content=note_content),
            synced_dt=obsidian_note_parser.get_synced_dt(content=note_content),
            note_path=note_path,
            _obsidian_note_builder=obsidian_note_builder,
            _addon_config=addon_config,
        )
        return note

    def _validate_fields_are_html(self):
        updated = False

        for i, field in enumerate(self.fields):
            field_html = markdown.markdown(field)
            if field_html != field:
                self.fields[i] = field_html
                updated = True

        if updated:
            self._store_to_file()

    def _perform_update_with_anki_note(self, anki_note: AnkiNote, change_log: ChangeLogBase, print_to_log: bool):
        self.note_id = anki_note.note_id
        self.model_id = anki_note.model_id
        self.fields = anki_note.fields
        self.tags = anki_note.tags
        self.deck = anki_note.deck
        self.modified_dt = anki_note.modified_dt

        note_folder_path = self._obsidian_note_builder.build_obsidian_note_folder_path_from_deck(deck=self.deck)

        if note_folder_path != self.note_path.absolute_path.parent:
            new_path = note_folder_path / self.note_path.file_name
            self.delete_file(change_log=change_log)
            if print_to_log:
                change_log.log_change(
                    change=f"Removed {self.note_path.absolute_path} to move it to {new_path}."
                )
            self.note_path = ObsidianNotePath.build_from_file_path(
                file_path=note_folder_path / self.note_path.file_name,
                addon_config=self._addon_config,
            )

        self.synced_dt = datetime.now()
        self._store_to_file()

        if print_to_log:
            change_log.log_change(
                change=f"Updated {self.note_path.file_name} with change in Anki note {anki_note.note_id}."
            )

    def _build_note_path_from_deck(self) -> ObsidianNotePath:
        note_folder_path = self._obsidian_note_builder.build_obsidian_note_folder_path_from_deck(deck=self.deck)
        note_path_from_deck = note_folder_path / self.note_path.file_name
        return note_path_from_deck

    def _store_to_file(self):
        field_names = AnkiNote.get_field_names(model_id=self.model_id)
        obsidian_note_content = NOTE_PROPERTIES_BASE_STRING.format(
            model_id=self.model_id,
            note_id=self.note_id,
            tags=",".join(self.tags),
            date_modified=self.modified_dt.strftime(format=DATETIME_FORMAT),
            date_synced=datetime.now().strftime(format=DATETIME_FORMAT),
        ) + "".join(
            [
                f"{self._obsidian_note_builder.build_field_title(field_name=field_name)}\n{field_content}\n\n"
                for field_name, field_content in zip(field_names, self.fields)
            ]
        )

        self.note_path.absolute_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.note_path.absolute_path, "w", encoding="utf-8") as f:
            f.write(obsidian_note_content)

    @staticmethod
    def _update_obsidian_note_mode_id(
        anki_note: AnkiNote, obsidian_note: "ObsidianNote", changes_log: ChangeLogBase
    ) -> bool:
        obsidian_note_updated = False

        if obsidian_note.model_id != anki_note.model_id:
            changes_log.log_change(
                change=(
                    f"Obsidian note {obsidian_note.note_id} model ID changed"
                    f" from {obsidian_note.model_id} to {anki_note.model_id}"
                ),
            )
            obsidian_note.model_id = anki_note.model_id
            obsidian_note_updated = True

        return obsidian_note_updated
