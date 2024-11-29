import time
import urllib.parse
from pathlib import Path
from typing import List

from PIL import Image as PILImage

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.constants import SRS_NOTE_IDENTIFIER_COMMENT, \
    SRS_NOTE_FIELD_IDENTIFIER_COMMENT, SRS_HEADER_TITLE_LEVEL, \
    DEFAULT_NOTE_ID_FOR_NEW_NOTES, CONF_ADD_OBSIDIAN_URL_IN_ANKI, OBSIDIAN_LINK_URL_FIELD_NAME
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.content.field.obsidian_note_field import ObsidianNoteFieldFactory
from obsidian_sync.obsidian.content.obsidian_properties import ObsidianNoteProperties
from obsidian_sync.obsidian.obsidian_file import ObsidianNoteFile
from obsidian_sync.obsidian.obsidian_notes_manager import ObsidianNotesManager
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.synchronizers.notes_synchronizer import NotesSynchronizer
from obsidian_sync.synchronizers.templates_synchronizer import TemplatesSynchronizer
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
        note_id=DEFAULT_NOTE_ID_FOR_NEW_NOTES,
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
    obsidian_vault_folder: Path,
):
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
    )
    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(obsidian_notes_result.existing_obsidian_notes) == 0
    assert len(obsidian_notes_result.new_obsidian_notes) == 1
    assert len(anki_test_app.get_all_notes()) == 0

    notes_synchronizer.synchronize_notes()

    assert len(anki_test_app.get_all_notes()) == 1

    anki_note = list(anki_test_app.get_all_notes().values())[0]
    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()
    obsidian_note = obsidian_notes_result.existing_obsidian_notes[anki_note.id]

    vault_url_string = urllib.parse.quote(string=obsidian_vault_folder.name)
    note_path_string_relative_to_vault = urllib.parse.quote(
        string=str(obsidian_note.file.path.relative_to(obsidian_vault_folder))
    )
    expected_obsidian_url = f"obsidian://open?vault={vault_url_string}&file={note_path_string_relative_to_vault}"

    assert anki_note.id != DEFAULT_NOTE_ID_FOR_NEW_NOTES
    assert anki_note.content.fields[0].text == "<p>Some front</p>"
    assert anki_note.content.fields[1].text == "<p>Some back</p>"
    assert obsidian_note.id == anki_note.id
    assert obsidian_note.content.properties.date_modified_in_anki == anki_note.content.properties.date_modified_in_anki
    assert obsidian_note.content.properties.date_synced >= anki_note.content.properties.date_modified_in_anki
    assert obsidian_note.obsidian_url == expected_obsidian_url


def test_ignore_non_srs_notes_in_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    addon_config: AddonConfig,
    obsidian_config: ObsidianConfig,
    markup_translator: MarkupTranslator,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    obsidian_vault_folder: Path,
):
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
    )
    non_srs_note_path = srs_folder_in_obsidian / "non-srs.md"
    non_srs_note_path.write_text(data="Some note content")

    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(obsidian_notes_result.existing_obsidian_notes) == 0
    assert len(obsidian_notes_result.new_obsidian_notes) == 1
    assert non_srs_note_path.exists()

    notes_synchronizer.synchronize_notes()
    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(obsidian_notes_result.existing_obsidian_notes) == 1
    assert len(obsidian_notes_result.new_obsidian_notes) == 0
    assert non_srs_note_path.exists()


def test_sync_new_obsidian_note_with_obsidian_url_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    templates_synchronizer: TemplatesSynchronizer,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault_folder: Path,
):
    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=True)

    note_file_path = srs_folder_in_obsidian / "test note.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=note_file_path,
    )

    templates_synchronizer.synchronize_templates()
    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert len(anki_note.content.fields) == 3

    vault_url_string = urllib.parse.quote(string=obsidian_vault_folder.name)
    obsidian_id_field = anki_note.content.fields[-1]
    note_path_string_relative_to_vault = urllib.parse.quote(
        string=str(note_file_path.relative_to(obsidian_vault_folder))
    )
    expected_obsidian_url = f"obsidian://open?vault={vault_url_string}&amp;file={note_path_string_relative_to_vault}"

    assert obsidian_id_field.name == OBSIDIAN_LINK_URL_FIELD_NAME
    assert obsidian_id_field.text == f"<p><a href=\"{expected_obsidian_url}\">{OBSIDIAN_LINK_URL_FIELD_NAME}</a></p>"


def test_sync_unchanged_existing_obsidian_note_after_enabling_obsidian_url_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    templates_synchronizer: TemplatesSynchronizer,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault_folder: Path,
):
    note_file_path = srs_folder_in_obsidian / "test note.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=note_file_path,
    )

    templates_synchronizer.synchronize_templates()
    notes_synchronizer.synchronize_notes()

    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=True)

    templates_synchronizer.synchronize_templates()
    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert len(anki_note.content.fields) == 3

    vault_url_string = urllib.parse.quote(string=obsidian_vault_folder.name)
    obsidian_id_field = anki_note.content.fields[-1]
    note_path_string_relative_to_vault = urllib.parse.quote(
        string=str(note_file_path.relative_to(obsidian_vault_folder))
    )
    expected_obsidian_url = f"obsidian://open?vault={vault_url_string}&amp;file={note_path_string_relative_to_vault}"

    assert obsidian_id_field.name == OBSIDIAN_LINK_URL_FIELD_NAME
    assert obsidian_id_field.text == f"<p><a href=\"{expected_obsidian_url}\">{OBSIDIAN_LINK_URL_FIELD_NAME}</a></p>"


def test_sync_moved_existing_obsidian_note_obsidian_url_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    templates_synchronizer: TemplatesSynchronizer,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault_folder: Path,
):
    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=True)

    note_file_path = srs_folder_in_obsidian / "test note.md"
    new_file_path = srs_folder_in_obsidian / "folder" / "test note.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=note_file_path,
    )

    templates_synchronizer.synchronize_templates()
    notes_synchronizer.synchronize_notes()

    new_file_path.parent.mkdir()
    note_file_path.rename(target=new_file_path)

    templates_synchronizer.synchronize_templates()
    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert len(anki_note.content.fields) == 3

    vault_name = urllib.parse.quote(string=obsidian_vault_folder.name)
    obsidian_id_field = anki_note.content.fields[-1]
    new_note_path_string_relative_to_vault = urllib.parse.quote(
        string=str(new_file_path.relative_to(obsidian_vault_folder))
    )
    expected_obsidian_url = (
        f"obsidian://open?vault={vault_name}&amp;file={new_note_path_string_relative_to_vault}"
    )

    assert obsidian_id_field.name == OBSIDIAN_LINK_URL_FIELD_NAME
    assert obsidian_id_field.text == f"<p><a href=\"{expected_obsidian_url}\">{OBSIDIAN_LINK_URL_FIELD_NAME}</a></p>"


def test_sync_new_obsidian_note_with_obsidian_url_to_anki_after_user_moves_obsidian_url_field_in_anki_model(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    templates_synchronizer: TemplatesSynchronizer,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault_folder: Path,
):
    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=True)

    templates_synchronizer.synchronize_templates()
    new_front_field_index = 2
    new_back_field_index = 0
    new_obsidian_url_model_field_index = 1
    anki_test_app.move_model_field(
        model_name="Basic", field_name="Front", new_field_index=new_front_field_index
    )
    anki_test_app.move_model_field(
        model_name="Basic", field_name="Back", new_field_index=new_back_field_index
    )
    anki_test_app.move_model_field(
        model_name="Basic", field_name=OBSIDIAN_LINK_URL_FIELD_NAME, new_field_index=new_obsidian_url_model_field_index
    )
    templates_synchronizer.synchronize_templates()

    note_file_path = srs_folder_in_obsidian / "test note.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=note_file_path,
    )

    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert len(anki_note.content.fields) == 3

    vault_url_string = urllib.parse.quote(string=obsidian_vault_folder.name)
    front_field = anki_note.content.fields[new_front_field_index]
    back_field = anki_note.content.fields[new_back_field_index]
    obsidian_id_field = anki_note.content.fields[new_obsidian_url_model_field_index]
    note_path_string_relative_to_vault = urllib.parse.quote(
        string=str(note_file_path.relative_to(obsidian_vault_folder))
    )
    expected_obsidian_url = f"obsidian://open?vault={vault_url_string}&amp;file={note_path_string_relative_to_vault}"

    assert front_field.name == "Front"
    assert front_field.text == "<p>Some front</p>"
    assert back_field.name == "Back"
    assert back_field.text == "<p>Some back</p>"
    assert obsidian_id_field.name == OBSIDIAN_LINK_URL_FIELD_NAME
    assert obsidian_id_field.text == f"<p><a href=\"{expected_obsidian_url}\">{OBSIDIAN_LINK_URL_FIELD_NAME}</a></p>"


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
    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(obsidian_notes_result.existing_obsidian_notes) == 0
    assert len(obsidian_notes_result.new_obsidian_notes) == 2
    assert len(anki_test_app.get_all_notes()) == 0

    notes_synchronizer.synchronize_notes()

    anki_notes = anki_test_app.get_all_notes()
    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(anki_notes) == 2
    assert len(obsidian_notes_result.existing_obsidian_notes) == 2

    for note_id, note in anki_notes.items():
        assert note_id in obsidian_notes_result.existing_obsidian_notes


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
    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(obsidian_notes_result.existing_obsidian_notes) == 0
    assert len(obsidian_notes_result.new_obsidian_notes) == 2
    assert len(anki_test_app.get_all_notes()) == 0

    notes_synchronizer.synchronize_notes()

    anki_notes = anki_test_app.get_all_notes()
    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()

    assert len(anki_notes) == 2
    assert len(obsidian_notes_result.existing_obsidian_notes) == 2

    for note_id, note in anki_notes.items():
        assert note_id in obsidian_notes_result.existing_obsidian_notes


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

    assert len(anki_note.content.fields[1].references) == 1
    assert anki_note.content.fields[1].references[0].path == attachment_file
    assert anki_note.content.fields[1].text == f"<p>Some back with <img alt=\"image\" src=\"{attachment_file}\"></p>"


def test_sync_new_obsidian_note_with_web_attachment_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    image_url = "www.some.com/img.png"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text=f"Some back with ![image]({image_url})",
        file_path=srs_folder_in_obsidian / "test.md",
    )

    notes_synchronizer.synchronize_notes()

    assert len(list(anki_test_app.media_manager.media_directory.iterdir())) == 0

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert len(anki_note.content.fields[1].references) == 0
    assert anki_note.content.fields[1].text == f"<p>Some back with <img alt=\"image\" src=\"{image_url}\"></p>"


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

    assert f"\\({in_line_equation}\\)" in anki_note.content.fields[0].text
    assert f"\\[{block_equation}\\]" in anki_note.content.fields[0].text


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


def test_sync_new_obsidian_note_with_links_to_other_notes_to_anki_substituting_with_obsidian_urls(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    obsidian_vault_folder: Path,
    obsidian_notes_manager: ObsidianNotesManager,
    notes_synchronizer: NotesSynchronizer,
):
    linked_note_path = srs_folder_in_obsidian / "linked note.md"
    main_note_path = srs_folder_in_obsidian / "main note.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=linked_note_path,
    )
    linked_note_path_relative_to_vault = urllib.parse.quote(
        string=str(linked_note_path.relative_to(obsidian_vault_folder))
    )
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text=f"Some [linked note]({linked_note_path_relative_to_vault}) here",
        back_text="Another back",
        file_path=main_note_path,
    )

    notes_synchronizer.synchronize_notes()

    vault_url_string = urllib.parse.quote(string=obsidian_vault_folder.name)
    expected_url_html = f"obsidian://open?vault={vault_url_string}&amp;file={linked_note_path_relative_to_vault}"
    expected_front_field_html = f"<p>Some <a href=\"{expected_url_html}\">linked note</a> here</p>"
    anki_notes = list(anki_test_app.get_all_notes().values())

    assert len(anki_notes) == 2
    assert (
        (
            anki_notes[0].content.fields[0].text == expected_front_field_html
            and anki_notes[1].content.fields[0].text != expected_front_field_html
        ) or (
            anki_notes[0].content.fields[0].text != expected_front_field_html
            and anki_notes[1].content.fields[0].text == expected_front_field_html
        )
    )


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
    time.sleep(1)

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


def test_sync_existing_obsidian_note_with_updated_field_with_code_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    initial_front_field = "Some front"
    updated_front_field = "Some front with ```\npython=3\n```"
    expected_front_field = "<p>Some front with <code>python=3</code></p>"
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

    assert anki_note.content.fields[0].text == expected_front_field


def test_sync_existing_obsidian_note_with_updated_tag_property_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    obsidian_vault: ObsidianVault,
):
    test_tag = "test"
    obsidian_file_path = srs_folder_in_obsidian / "test.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=obsidian_file_path,
    )

    notes_synchronizer.synchronize_notes()

    time.sleep(1)

    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()
    obsidian_note = list(obsidian_notes_result.existing_obsidian_notes.values())[0]
    obsidian_note.properties.tags.append(test_tag)
    obsidian_vault.save_file(file=obsidian_note.file)

    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert anki_note.content.properties.tags == [test_tag]


def test_sync_existing_obsidian_note_with_updated_suspended_property_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
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

    time.sleep(1)

    obsidian_notes_result = obsidian_notes_manager.get_all_obsidian_notes()
    obsidian_note = list(obsidian_notes_result.existing_obsidian_notes.values())[0]
    obsidian_note.properties.suspended = True
    obsidian_vault.save_file(file=obsidian_note.file)

    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert anki_note.content.properties.suspended is True


def test_sync_existing_obsidian_note_with_updated_link_to_another_note_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    obsidian_vault: ObsidianVault,
    obsidian_vault_folder: Path,
):
    linked_note_path = srs_folder_in_obsidian / "linked note.md"
    updated_linked_note_path = srs_folder_in_obsidian / "updated linked note.md"
    main_note_path = srs_folder_in_obsidian / "main note.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=linked_note_path,
    )
    linked_note_path_relative_to_vault = urllib.parse.quote(
        string=str(linked_note_path.relative_to(obsidian_vault_folder))
    )
    updated_linked_note_path_relative_to_vault = urllib.parse.quote(
        string=str(updated_linked_note_path.relative_to(obsidian_vault_folder))
    )
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text=f"Some [linked note]({linked_note_path_relative_to_vault}) here",
        back_text="Another back",
        file_path=main_note_path,
    )

    notes_synchronizer.synchronize_notes()

    time.sleep(1)

    linked_note_path.rename(updated_linked_note_path)
    obsidian_note_text = main_note_path.read_text()
    obsidian_note_text = obsidian_note_text.replace(
        linked_note_path_relative_to_vault, updated_linked_note_path_relative_to_vault
    )
    main_note_path.write_text(obsidian_note_text)

    notes_synchronizer.synchronize_notes()

    vault_url_string = urllib.parse.quote(string=obsidian_vault_folder.name)
    expected_url_html = f"obsidian://open?vault={vault_url_string}&amp;file={updated_linked_note_path_relative_to_vault}"
    expected_front_field_html = f"<p>Some <a href=\"{expected_url_html}\">linked note</a> here</p>"
    anki_notes = list(anki_test_app.get_all_notes().values())

    assert len(anki_notes) == 2
    assert (
        (
            anki_notes[0].content.fields[0].text == expected_front_field_html
            and anki_notes[1].content.fields[0].text != expected_front_field_html
        ) or (
            anki_notes[0].content.fields[0].text != expected_front_field_html
            and anki_notes[1].content.fields[0].text == expected_front_field_html
        )
    )


def test_remove_deleted_obsidian_note_from_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault: ObsidianVault,
    addon_config: AddonConfig,
    obsidian_note_field_factory: ObsidianNoteFieldFactory,
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
            addon_config=addon_config,
            field_factory=obsidian_note_field_factory,
        ),
    )

    notes_synchronizer.synchronize_notes()

    assert len(anki_test_app.get_all_notes()) == 0
