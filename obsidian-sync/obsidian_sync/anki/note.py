from dataclasses import dataclass

from obsidian_sync.anki.content import AnkiNoteContent
from obsidian_sync.base_types.note import Note


@dataclass
class AnkiNote(Note):  # todo: remove the use of AnkiNote in favour of directly using AnkiNoteContent
    # can get cloze numbers with `note.cloze_numbers_in_fields()`

    content: AnkiNoteContent

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @property
    def id(self) -> int:
        return self.content.properties.note_id

    @property
    def model_id(self) -> int:
        return self.content.properties.model_id
