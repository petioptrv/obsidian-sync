import time
import urllib.parse
from pathlib import Path
from typing import List

from PIL import Image as PILImage

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.constants import SRS_NOTE_IDENTIFIER_COMMENT, \
    SRS_NOTE_FIELD_IDENTIFIER_COMMENT, SRS_HEADER_TITLE_LEVEL, \
    DEFAULT_NODE_ID_FOR_NEW_NOTES
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_content import ObsidianNoteProperties
from obsidian_sync.obsidian.obsidian_file import ObsidianNoteFile
from obsidian_sync.obsidian.obsidian_notes_manager import ObsidianNotesManager
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.synchronizers.notes_synchronizer import NotesSynchronizer
from tests.anki_test_app import AnkiTestApp


def build_basic_obsidian_note(
    anki_test_app: AnkiTestApp,
    front_text: str,
    back_text: str,
    file_path: Path,
    tags: List[str] = None,
):
    model_name = "Basic"
    model_id = anki_test_app.get_model_id(model_name=model_name)
    note_text = f"""{
    ObsidianNoteProperties(
        model_id=model_id,
        model_name="Basic",
        note_id=DEFAULT_NODE_ID_FOR_NEW_NOTES,
        tags=tags or [],
        suspended=False,
        maximum_card_difficulty=0,
        date_modified_in_anki=None,
        date_synced=None,
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


def test_sync_new_obsidian_note_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    addon_config: AddonConfig,
    obsidian_config: ObsidianConfig,
    markup_translator: MarkupTranslator,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
    )
    existing_obsidian_notes, new_obsidian_notes = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(existing_obsidian_notes) == 0
    assert len(new_obsidian_notes) == 1
    assert len(anki_test_app.get_all_notes()) == 0

    notes_synchronizer.synchronize_notes()

    assert len(anki_test_app.get_all_notes()) == 1

    anki_note = list(anki_test_app.get_all_notes().values())[0]
    existing_obsidian_notes, new_obsidian_notes = obsidian_notes_manager.get_all_obsidian_notes()
    obsidian_note = existing_obsidian_notes[anki_note.id]

    assert anki_note.id != DEFAULT_NODE_ID_FOR_NEW_NOTES
    assert anki_note.content.fields[0].text == "<p>Some front</p>"
    assert anki_note.content.fields[1].text == "<p>Some back</p>"
    assert obsidian_note.id == anki_note.id
    assert obsidian_note.content.properties.date_modified_in_anki == anki_note.content.properties.date_modified_in_anki
    assert obsidian_note.content.properties.date_synced >= anki_note.content.properties.date_modified_in_anki


def test_sync_two_new_obsidian_notes_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    addon_config: AddonConfig,
    obsidian_config: ObsidianConfig,
    markup_translator: MarkupTranslator,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "some_test.md",
    )
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Another front",
        back_text="Another back",
        file_path=srs_folder_in_obsidian / "another_test.md",
    )
    existing_obsidian_notes, new_obsidian_notes = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(existing_obsidian_notes) == 0
    assert len(new_obsidian_notes) == 2
    assert len(anki_test_app.get_all_notes()) == 0

    notes_synchronizer.synchronize_notes()

    anki_notes = anki_test_app.get_all_notes()
    existing_obsidian_notes, new_obsidian_notes = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(anki_notes) == 2
    assert len(existing_obsidian_notes) == 2

    for note_id, note in anki_notes.items():
        assert note_id in existing_obsidian_notes


def test_sync_new_obsidian_note_with_attachment_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    srs_attachments_in_obsidian_folder: Path,
    some_test_image: PILImage,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    image_file_name = "some img.png"
    srs_attachments_in_obsidian_folder.mkdir(parents=True)
    image_file_path = srs_attachments_in_obsidian_folder / image_file_name
    some_test_image.save(image_file_path)
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text=f"Some back with ![image]({urllib.parse.quote(string=image_file_name)})",
        file_path=srs_folder_in_obsidian / "test.md",
    )

    assert len(list(anki_test_app.media_manager.media_directory.iterdir())) == 0

    notes_synchronizer.synchronize_notes()

    assert len(list(anki_test_app.media_manager.media_directory.iterdir())) == 1

    anki_note = list(anki_test_app.get_all_notes().values())[0]
    attachment_file = Path(list(anki_test_app.media_manager.media_directory.iterdir())[0])

    assert len(anki_note.content.fields[1].attachments) == 1
    assert anki_note.content.fields[1].attachments[0].path == attachment_file
    assert anki_note.content.fields[1].text == f"<p>Some back with <img alt=\"image\" src=\"{attachment_file}\" /></p>"


def test_sync_new_obsidian_note_with_tag_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    tag = "test"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
        tags=[tag]
    )

    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert len(anki_note.content.properties.tags) == 1
    assert anki_note.content.properties.tags[0] == tag


def test_sync_new_obsidian_note_with_external_link_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    external_url = "http://www.example.com"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text=f"Some front with [external site]({external_url})",
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
    )

    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert anki_note.content.fields[0].text == (
        f"<p>Some front with <a href=\"{external_url}\">external site</a></p>"
    )


def test_sync_new_obsidian_note_with_math_equations_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    in_line_equation = "x = 1"
    block_equation = "x = 2"
    front_field_markdown = f"""Some front with an in-line math equation ${in_line_equation}$
and a block equation $${block_equation}$$"""
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text=front_field_markdown,
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
    )

    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert f"<anki-mathjax>{in_line_equation}</anki-mathjax>" in anki_note.content.fields[0].text
    assert f"<anki-mathjax block=\"true\">{block_equation}</anki-mathjax>" in anki_note.content.fields[0].text


def test_sync_new_obsidian_note_with_code_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    in_line_code = "code variable"
    block_code = "block code"
    front_field_markdown = f"""Some front with an in-line math equation `{in_line_code}`
and a\n```\n{block_code}\n```"""
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text=front_field_markdown,
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
    )

    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert f"<code>{in_line_code}</code>" in anki_note.content.fields[0].text
    assert f"<pre><code>{block_code}\n</code></pre>" in anki_note.content.fields[0].text


def test_obsidian_note_in_anki_remains_the_same_on_subsequent_sync(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
    )

    notes_synchronizer.synchronize_notes()

    first_sync_anki_note = list(anki_test_app.get_all_notes().values())[0]

    notes_synchronizer.synchronize_notes()

    anki_notes = anki_test_app.get_all_notes()

    assert len(anki_notes) == 1

    second_sync_anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert first_sync_anki_note == second_sync_anki_note


def test_sync_existing_obsidian_note_with_updated_field_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    initial_front_field = "Some front"
    updated_front_field = "Some back alt"
    obsidian_file_path = srs_folder_in_obsidian / "test.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text=initial_front_field,
        back_text="Some back",
        file_path=obsidian_file_path,
    )

    notes_synchronizer.synchronize_notes()

    time.sleep(1)

    obsidian_file_text = obsidian_file_path.read_text()
    updated_obsidian_file_text = obsidian_file_text.replace(initial_front_field, updated_front_field)
    obsidian_file_path.write_text(updated_obsidian_file_text)

    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert anki_note.content.fields[0].text == f"<p>{updated_front_field}</p>"


def test_remove_deleted_obsidian_note_from_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault: ObsidianVault,
):
    obsidian_file_path = srs_folder_in_obsidian / "test.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=obsidian_file_path,
    )

    notes_synchronizer.synchronize_notes()

    assert len(anki_test_app.get_all_notes()) == 1

    obsidian_vault.delete_file(
        file=ObsidianNoteFile(
            path=obsidian_file_path,
            attachment_manager=obsidian_vault.attachments_manager
        ),
    )

    notes_synchronizer.synchronize_notes()

    assert len(anki_test_app.get_all_notes()) == 0
