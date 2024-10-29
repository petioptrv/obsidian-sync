from dataclasses import dataclass

from obsidian_sync.base_types.note import Note


@dataclass
class AnkiNote(Note):
    # can get cloze numbers with `note.cloze_numbers_in_fields()`

    # can get field-associated files with `mw.col.media.files_in_str(mid=mid, string=field_text)`
    pass
