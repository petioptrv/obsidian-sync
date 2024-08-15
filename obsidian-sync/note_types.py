import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Set, Optional

from aqt import mw
from anki.notes import Note as ANote
from aqt.utils import showCritical

from .note_builders.obsidian_note_builder import ObsidianNoteBuilder
from .config_handler import ConfigHandler
from .constants import ADD_ON_NAME, NOTE_PROPERTIES_BASE_STRING, DATETIME_FORMAT, MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH
from .change_log import ChangeLogBase
from .obsidian_note_parser import ObsidianNoteParser
from .utils import is_markdown_file, format_add_on_message, get_field_names_from_anki_model_id, \
    delete_obsidian_note


@dataclass
class Note:
    note_id: int
    model_id: int
    fields: [str]
    tags: Set[str]
    deck: str
    modified_dt: datetime


@dataclass
class AnkiNote(Note):
    @classmethod
    def from_anki_note(cls, note: ANote) -> "AnkiNote":
        note = AnkiNote(
            note_id=note.id,
            model_id=note.mid,
            fields=note.fields,
            tags=set(note.tags),
            deck=mw.col.decks.name(note.cards()[0].did),
            modified_dt=datetime.fromtimestamp(note.mod),
        )
        return note

    @classmethod
    def create_in_anki_from_obsidian(cls, obsidian_note: "ObsidianNote", change_log: ChangeLogBase) -> "AnkiNote":
        deck_id = mw.col.decks.id(name=obsidian_note.deck)
        field_names = get_field_names_from_anki_model_id(id=obsidian_note.model_id)
        model = mw.col.models.get(id=obsidian_note.model_id)

        note = ANote(col=mw.col, model=model)
        note.note_type()["did"] = deck_id

        for field_name, field_value in zip(field_names, obsidian_note.fields):
            note[field_name] = field_value

        mw.col.add_note(note=note, deck_id=deck_id)

        note = mw.col.get_note(id=note.id)
        anki_note = AnkiNote.from_anki_note(note=note)

        obsidian_note.update_with_anki_note(anki_note=anki_note, change_log=change_log)  # update note ID in Obsidian

        change_log.log_change(change=f"Created Anki note from obsidian note {obsidian_note.file_path}.")

        return anki_note

    def update_with_obsidian_note(self, obsidian_note: "ObsidianNote", changes_log: ChangeLogBase):
        raise NotImplementedError


@dataclass
class ObsidianNote(Note):
    synced_dt: datetime
    file_path: Path
    _obsidian_note_parser: ObsidianNoteParser
    _obsidian_note_builder: ObsidianNoteBuilder
    _config_handler: ConfigHandler

    @property
    def updated_since_last_sync(self) -> bool:
        return self.file_path.stat().st_mtime > self.synced_dt.timestamp() + 1

    @classmethod
    def build_from_file(
        cls,
        config_handler: ConfigHandler,
        obsidian_note_parser: ObsidianNoteParser,
        obsidian_note_builder: ObsidianNoteBuilder,
        file_path: Path,
    ) -> Optional["ObsidianNote"]:
        note = None

        if is_markdown_file(path=file_path):
            with open(file_path, "r") as f:
                note_content = f.read()
            if obsidian_note_parser.is_anki_note_in_obsidian(note_content=note_content):
                try:
                    note = cls._parse_obsidian_note(
                        config_handler=config_handler,
                        obsidian_note_parser=obsidian_note_parser,
                        obsidian_note_builder=obsidian_note_builder,
                        note_path=file_path,
                        note_content=note_content,
                    )
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
    def create_from_anki_note(cls, anki_note: AnkiNote, change_log: ChangeLogBase):
        pass
        # raise NotImplementedError

    def update_with_anki_note(self, anki_note: AnkiNote, change_log: ChangeLogBase):
        if anki_note.modified_dt > self.modified_dt:
            if self.updated_since_last_sync:
                # todo: add git-style diff window
                self._perform_update_with_anki_note(anki_note=anki_note, change_log=change_log)
            else:
                self._perform_update_with_anki_note(anki_note=anki_note, change_log=change_log)

    def delete_file(self, change_log: ChangeLogBase):
        delete_obsidian_note(
            obsidian_vault=self._config_handler.vault_path, obsidian_note_path=self.file_path
        )
        change_log.log_change(change=f"{self.file_path} was deleted.")

    @classmethod
    def _parse_obsidian_note(
        cls,
        config_handler: ConfigHandler,
        obsidian_note_parser: ObsidianNoteParser,
        obsidian_note_builder: ObsidianNoteBuilder,
        note_path: Path, note_content: str,
    ) -> "ObsidianNote":
        deck = obsidian_note_parser.parse_deck_from_obsidian_note_path(note_path=note_path)
        note = ObsidianNote(
            note_id=obsidian_note_parser.get_note_id_from_obsidian_note_content(content=note_content),
            model_id=obsidian_note_parser.get_model_id_from_obsidian_note_content(content=note_content),
            fields=obsidian_note_parser.get_fields_from_obsidian_note_content(content=note_content),
            tags=obsidian_note_parser.get_tags_from_obsidian_note_content(content=note_content),
            deck=deck,
            modified_dt=obsidian_note_parser.get_modified_dt(content=note_content),
            synced_dt=obsidian_note_parser.get_synced_dt(content=note_content),
            file_path=note_path,
            _obsidian_note_parser=obsidian_note_parser,
            _obsidian_note_builder=obsidian_note_builder,
            _config_handler=config_handler,
        )
        return note

    def _perform_update_with_anki_note(self, anki_note: AnkiNote, change_log: ChangeLogBase):
        self.note_id = anki_note.note_id
        self.model_id = anki_note.model_id
        self.fields = anki_note.fields
        self.tags = anki_note.tags
        self.deck = anki_note.deck
        self.modified_dt = anki_note.modified_dt

        note_path_from_deck = self._build_note_path_from_deck()

        if note_path_from_deck != self.file_path:
            self.delete_file(change_log=change_log)
            change_log.log_change(
                change=f"Removed {self.file_path} to move it to {note_path_from_deck}"
            )
            self.file_path = note_path_from_deck

        self._store_to_file()

    def _build_note_path_from_deck(self) -> Path:
        note_folder_path = self._obsidian_note_parser.build_obsidian_note_folder_path_from_deck(deck=self.deck)
        note_path_from_deck = note_folder_path / self.file_path.name
        return note_path_from_deck

    def _build_note_file_name(self) -> str:
        max_file_name_length = MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH
        suffix = ".md"
        name = self.fields[0][:(max_file_name_length - len(suffix))] + suffix
        return name

    def _store_to_file(self):
        field_names = get_field_names_from_anki_model_id(id=self.model_id)
        obsidian_note_content = NOTE_PROPERTIES_BASE_STRING.format(
            model_id=self.model_id,
            note_id=self.note_id,
            tags=",".join(self.tags),
            date_modified=self.modified_dt.strftime(format=DATETIME_FORMAT),
            date_synced=datetime.now().strftime(format=DATETIME_FORMAT),
            anki_note_identifier_property_value=self._config_handler.anki_note_in_obsidian_property_value,
        ) + "".join(
            [
                f"{self._obsidian_note_builder.build_field_title(field_name=field_name)}\n{field_content}\n\n"
                for field_name, field_content in zip(field_names, self.fields)
            ]
        )

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, "w", encoding="utf-8") as f:
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
