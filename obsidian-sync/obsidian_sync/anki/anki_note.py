from dataclasses import dataclass
from typing import TYPE_CHECKING


from obsidian_sync.anki.anki_content import AnkiNoteContent
from obsidian_sync.base_types.note import Note
from obsidian_sync.constants import DEFAULT_NODE_ID_FOR_NEW_NOTES
from obsidian_sync.markup_translator import MarkupTranslator

if TYPE_CHECKING:  # avoids circular import
    from obsidian_sync.addon_config import AddonConfig
    from obsidian_sync.anki.app.anki_app import AnkiApp


@dataclass
class AnkiNote(Note):
    # can get cloze numbers with `note.cloze_numbers_in_fields()`

    content: AnkiNoteContent

    def __init__(
        self,
        anki_app: "AnkiApp",
        markup_translator: MarkupTranslator,
        content: AnkiNoteContent,
    ):
        self._anki_app = anki_app
        self._markup_translator = markup_translator
        self.content = content

    @property
    def id(self) -> int:
        return self.content.properties.note_id

    @property
    def model_id(self) -> int:
        return self.content.properties.model_id

    @classmethod
    def from_note(cls, note: Note, anki_app: "AnkiApp", addon_config: "AddonConfig") -> "AnkiNote":
        assert note.content.properties.note_id == DEFAULT_NODE_ID_FOR_NEW_NOTES

        deck_name = addon_config.anki_deck_name_for_obsidian_imports
        anki_note = anki_app.create_new_empty_note_in_anki(model_id=note.content.properties.model_id, deck_name=deck_name)
        note.content.properties.note_id = anki_note.id

        anki_note.update_with_note(note=note)

        return anki_note

    def update_with_note(self, note: Note):
        content_from_note = AnkiNoteContent.from_content(
            content=note.content,
            anki_media_manager=self._anki_app.media_manager,
            markup_translator=self._markup_translator,
        )
        if self.content != content_from_note:
            self.content = content_from_note
            self._anki_app.update_note_in_anki(anki_note=self)
            anki_note = self._anki_app.get_note_by_id(note_id=self.id)
            self.content = anki_note.content  # to update the timestamps

    def delete(self):
        self._anki_app.delete_note_in_anki(note=self)
