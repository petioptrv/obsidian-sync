from pathlib import Path
from typing import List

from obsidian_sync.anki.anki_content import AnkiReference, AnkiNoteContent, AnkiNoteProperties, AnkiNoteField
from obsidian_sync.anki.anki_note import AnkiNote
from obsidian_sync.constants import DEFAULT_NOTE_ID_FOR_NEW_NOTES, SRS_NOTE_IDENTIFIER_COMMENT, \
    SRS_NOTE_FIELD_IDENTIFIER_COMMENT, SRS_HEADER_TITLE_LEVEL
from obsidian_sync.obsidian.content.obsidian_properties import ObsidianNoteProperties
from tests.anki_test_app import AnkiTestApp


def build_basic_anki_note(
    anki_test_app: AnkiTestApp,
    front_text: str,
    back_text: str,
    front_references: List[AnkiReference] = None,
    back_references: List[AnkiReference] = None,
    tags: List[str] = None,
) -> AnkiNote:
    model_name = "Basic"
    model_id = anki_test_app.get_model_id(model_name=model_name)
    note = AnkiNote(
        content=AnkiNoteContent(
            properties=AnkiNoteProperties(
                model_id=model_id,
                model_name=model_name,
                note_id=DEFAULT_NOTE_ID_FOR_NEW_NOTES,
                tags=tags or [],
                date_modified_in_anki=None,
            ),
            fields=[
                AnkiNoteField(
                    name="Front",
                    text=front_text,
                    references=front_references or [],
                ),
                AnkiNoteField(
                    name="Back",
                    text=back_text,
                    references=back_references or [],
                ),
            ],
        ),
    )
    return note


def build_basic_obsidian_note(
    anki_test_app: AnkiTestApp,
    front_text: str,
    back_text: str,
    file_path: Path,
    tags: List[str] = None,
    mock_note_id: int = DEFAULT_NOTE_ID_FOR_NEW_NOTES,
):
    model_name = "Basic"
    model_id = anki_test_app.get_model_id(model_name=model_name)
    note_text = f"""{
    ObsidianNoteProperties(
        model_id=model_id,
        model_name=model_name,
        note_id=mock_note_id,
        tags=tags or [],
        date_modified_in_anki=None,
    ).to_obsidian_file_text()
}
{SRS_NOTE_IDENTIFIER_COMMENT}
{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Front

{front_text}

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Back

{back_text}

"""

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(data=note_text)


def build_anki_cloze_note(
    anki_test_app: AnkiTestApp,
    text: str,
    references: List[AnkiReference] = None,
    tags: List[str] = None,
) -> AnkiNote:
    model_name = "Cloze"
    model_id = anki_test_app.get_model_id(model_name=model_name)
    note = AnkiNote(
        content=AnkiNoteContent(
            properties=AnkiNoteProperties(
                model_id=model_id,
                model_name=model_name,
                note_id=DEFAULT_NOTE_ID_FOR_NEW_NOTES,
                tags=tags or [],
                date_modified_in_anki=None,
            ),
            fields=[
                AnkiNoteField(
                    name="Text",
                    text=text,
                    references=references or [],
                ),
                AnkiNoteField(
                    name="Back Extra",
                    text="",
                    references=[],
                ),
            ],
        ),
    )
    return note


def build_obsidian_cloze_note(
    anki_test_app: AnkiTestApp,
    text: str,
    file_path: Path,
    tags: List[str] = None,
    mock_note_id: int = DEFAULT_NOTE_ID_FOR_NEW_NOTES,
):
    model_name = "Cloze"
    model_id = anki_test_app.get_model_id(model_name=model_name)
    note_text = f"""{
    ObsidianNoteProperties(
        model_id=model_id,
        model_name=model_name,
        note_id=mock_note_id,
        tags=tags or [],
        date_modified_in_anki=None,
    ).to_obsidian_file_text()
    }
{SRS_NOTE_IDENTIFIER_COMMENT}
{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Text

{text}

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Back Extra


"""

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(data=note_text)
