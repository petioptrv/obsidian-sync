import time
import urllib.parse
from pathlib import Path

from PIL import Image as PILImage

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.anki.anki_content import AnkiMediaReference
from obsidian_sync.constants import MARKDOWN_FILE_SUFFIX, SRS_NOTE_IDENTIFIER_COMMENT, \
    MODEL_ID_PROPERTY_NAME, MODEL_NAME_PROPERTY_NAME, NOTE_ID_PROPERTY_NAME, TAGS_PROPERTY_NAME, \
    SRS_NOTE_FIELD_IDENTIFIER_COMMENT, SRS_HEADER_TITLE_LEVEL, \
    CONF_ADD_OBSIDIAN_URL_IN_ANKI, OBSIDIAN_LINK_URL_FIELD_NAME, DATE_MODIFIED_PROPERTY_NAME, DATETIME_FORMAT
from obsidian_sync.file_utils import check_files_are_identical
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.content.obsidian_reference import ObsidianMediaReference
from obsidian_sync.obsidian.obsidian_notes_manager import ObsidianNotesManager
from obsidian_sync.synchronizers.notes_synchronizer import NotesSynchronizer
from obsidian_sync.synchronizers.templates_synchronizer import TemplatesSynchronizer
from tests.anki_test_app import AnkiTestApp
from tests.utils import build_basic_anki_note


def test_sync_new_anki_note_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    obsidian_notes_manager: ObsidianNotesManager,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    front_field_html = "Some front"
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )
    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()

    assert len(obsidian_notes_result.unchanged_notes) == 0
    assert len(obsidian_notes_result.new_notes) == 0
    assert not srs_folder_in_obsidian.exists()

    notes_synchronizer.synchronize_notes()
    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()

    assert len(obsidian_notes_result.unchanged_notes) == 1
    assert srs_folder_in_obsidian.exists()
    assert len(list(srs_folder_in_obsidian.iterdir())) == 1

    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    obsidian_note_file = list(srs_folder_in_obsidian.iterdir())[0]

    assert obsidian_note_file.suffix == f"{MARKDOWN_FILE_SUFFIX}"

    sanitized_front_field_html = markup_translator.sanitize_html(html=front_field_html)
    sanitized_back_field_html = markup_translator.sanitize_html(html=back_field_html)

    expected_text = f"""---
{MODEL_ID_PROPERTY_NAME}: {note.model_id}
{MODEL_NAME_PROPERTY_NAME}: Basic
{NOTE_ID_PROPERTY_NAME}: {anki_note.id}
{TAGS_PROPERTY_NAME}: []
{DATE_MODIFIED_PROPERTY_NAME}: '{obsidian_note.properties.date_modified_in_anki.strftime(DATETIME_FORMAT)}'
---
{SRS_NOTE_IDENTIFIER_COMMENT}
{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Front

{markup_translator.translate_html_to_markdown(html=sanitized_front_field_html)}

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Back

{markup_translator.translate_html_to_markdown(html=sanitized_back_field_html)}

"""
    note_text = obsidian_note_file.read_text()

    assert note_text == expected_text


def test_sync_two_new_anki_notes_with_the_same_front_field_to_obsidian_without_causing_a_file_name_collision(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    srs_folder_in_obsidian: Path,
):
    first_note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    second_note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Another back",
    )
    first_anki_note = anki_test_app.add_note(
        note=first_note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )
    second_anki_note = anki_test_app.add_note(
        note=second_note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    first_obsidian_note = obsidian_notes_result.unchanged_notes[first_anki_note.id]
    second_obsidian_note = obsidian_notes_result.unchanged_notes[second_anki_note.id]

    assert first_obsidian_note.file.path != second_obsidian_note.file.path
    assert (  # one of the two notes is renamed
        (
            first_obsidian_note.file.path.name == "Some front.md"
            and second_obsidian_note.file.path.name == f"Some front-{second_anki_note.id}.md"
        ) or (
            first_obsidian_note.file.path.name == f"Some front-{first_anki_note.id}.md"
            and second_obsidian_note.file.path.name == "Some front.md"
        )
    )
    assert first_obsidian_note.file.path.exists()
    assert second_obsidian_note.file.path.exists()
    assert "Some back" in first_obsidian_note.file.path.read_text()
    assert "Another back" in second_obsidian_note.file.path.read_text()


def test_sync_new_anki_note_to_obsidian_with_obsidian_url_field_enabled_but_not_shown_in_obsidian_file(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    srs_folder_in_obsidian: Path,
):
    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=True)

    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]

    assert len(obsidian_note.content.fields) == 3
    assert obsidian_note.content.fields[-1].name == OBSIDIAN_LINK_URL_FIELD_NAME

    obsidian_note_file = list(srs_folder_in_obsidian.iterdir())[0]
    note_text = obsidian_note_file.read_text()

    assert OBSIDIAN_LINK_URL_FIELD_NAME not in note_text


def test_sync_new_anki_note_to_obsidian_with_obsidian_url_field_enabled_updated_in_anki_on_sync(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    templates_synchronizer: TemplatesSynchronizer,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    srs_folder_in_obsidian: Path,
    obsidian_vault_folder: Path,
):
    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=True)

    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    templates_synchronizer.synchronize_templates()
    notes_synchronizer.synchronize_notes()

    anki_notes = anki_test_app.get_all_notes_categorized()
    anki_note = anki_notes.unchanged_notes[anki_note.id]
    vault_url_string = urllib.parse.quote(string=obsidian_vault_folder.name)
    obsidian_file_path = srs_folder_in_obsidian / "Some front.md"
    note_path_string_relative_to_vault = urllib.parse.quote(
        string=str(obsidian_file_path.relative_to(obsidian_vault_folder))
    )
    expected_obsidian_url = f"obsidian://open?vault={vault_url_string}&amp;file={note_path_string_relative_to_vault}"

    assert len(anki_note.content.fields) == 3
    assert anki_note.content.fields[-1].name == OBSIDIAN_LINK_URL_FIELD_NAME
    assert anki_note.content.fields[-1].text == f"<p><a href=\"{expected_obsidian_url}\">{OBSIDIAN_LINK_URL_FIELD_NAME}</a></p>"


def test_sync_new_anki_note_with_local_image_reference_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    tmp_path: Path,
    some_test_image: PILImage,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    srs_attachments_in_obsidian_folder: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    srs_folder_in_obsidian: Path,
):
    image_file_name = "some img.png"
    temp_file_path = tmp_path / image_file_name
    some_test_image.save(temp_file_path)
    front_field_html = f"Some front with <img src=\"{image_file_name}\">"
    back_field_html = "Some back"
    anki_reference = AnkiMediaReference(path=temp_file_path)
    anki_reference.path = anki_test_app.media_manager.ensure_media_is_in_anki(
        reference=anki_reference
    )
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
        front_references=[anki_reference],
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    assert not srs_attachments_in_obsidian_folder.exists()

    notes_synchronizer.synchronize_notes()

    assert srs_attachments_in_obsidian_folder.exists()

    attachments = {a.name: a for a in srs_attachments_in_obsidian_folder.iterdir()}

    assert len(attachments) == 1
    assert image_file_name in attachments

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]
    obsidian_note_file = [f for f in srs_folder_in_obsidian.iterdir() if f.is_file()][0]

    assert first_field.to_markdown() == f"Some front with ![]({attachments[image_file_name]})"
    assert (  # Obsidian makes path ULR-safe
        f"{urllib.parse.quote(string=attachments[image_file_name].name)}" in obsidian_note_file.read_text()
    )
    assert len(first_field.references) == 1

    obsidian_reference = obsidian_note.content.fields[0].references[0]

    assert isinstance(obsidian_reference, ObsidianMediaReference)
    assert check_files_are_identical(first=temp_file_path, second=obsidian_reference.path)


def test_sync_new_anki_note_with_local_image_reference_with_capitalized_extension_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    tmp_path: Path,
    some_test_image: PILImage,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    srs_attachments_in_obsidian_folder: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    srs_folder_in_obsidian: Path,
):
    image_file_name = "some img.PNG"
    temp_file_path = tmp_path / image_file_name
    some_test_image.save(temp_file_path)
    front_field_html = f"Some front with <img src=\"{image_file_name}\">"
    back_field_html = "Some back"
    anki_reference = AnkiMediaReference(path=temp_file_path)
    anki_reference.path = anki_test_app.media_manager.ensure_media_is_in_anki(
        reference=anki_reference
    )
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
        front_references=[anki_reference],
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    assert not srs_attachments_in_obsidian_folder.exists()

    notes_synchronizer.synchronize_notes()

    assert srs_attachments_in_obsidian_folder.exists()

    attachments = {a.name: a for a in srs_attachments_in_obsidian_folder.iterdir()}

    assert len(attachments) == 1
    assert image_file_name in attachments

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]
    obsidian_note_file = [f for f in srs_folder_in_obsidian.iterdir() if f.is_file()][0]

    assert first_field.to_markdown() == f"Some front with ![]({attachments[image_file_name]})"
    assert (  # Obsidian makes path ULR-safe
        f"{urllib.parse.quote(string=attachments[image_file_name].name)}" in obsidian_note_file.read_text()
    )
    assert len(first_field.references) == 1

    obsidian_reference = obsidian_note.content.fields[0].references[0]

    assert isinstance(obsidian_reference, ObsidianMediaReference)
    assert check_files_are_identical(first=temp_file_path, second=obsidian_reference.path)


def test_sync_new_anki_note_with_web_reference_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    srs_attachments_in_obsidian_folder: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    srs_folder_in_obsidian: Path,
):
    image_url = "www.some.com/img.png"
    front_field_html = f"<p>Some front with <img alt=\"image\" src=\"{image_url}\" /></p>"
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    assert not srs_attachments_in_obsidian_folder.exists()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert first_field.to_markdown() == f"Some front with ![image]({image_url})"


def test_syncing_references_with_unicode_whitespace_from_anki_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    tmp_path: Path,
    some_test_image: PILImage,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    srs_attachments_in_obsidian_folder: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
    srs_folder_in_obsidian: Path,
):
    """Obsidian cannot handle file names with Unicode whitespace."""

    image_file_name = "Screenshot 2024-11-26 at 11.54.26 AM.png"
    expected_image_file_name_in_obsidian = "Screenshot 2024-11-26 at 11.54.26 AM.png"
    temp_file_path = tmp_path / image_file_name
    some_test_image.save(temp_file_path)
    front_field_html = f"Some front with <img src=\"{image_file_name}\">"
    back_field_html = "Some back"
    anki_reference = AnkiMediaReference(path=temp_file_path)
    anki_reference.path = anki_test_app.media_manager.ensure_media_is_in_anki(
        reference=anki_reference
    )
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
        front_references=[anki_reference],
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    assert not srs_attachments_in_obsidian_folder.exists()

    notes_synchronizer.synchronize_notes()

    assert srs_attachments_in_obsidian_folder.exists()

    attachments = {a.name: a for a in srs_attachments_in_obsidian_folder.iterdir()}

    assert len(attachments) == 1
    assert expected_image_file_name_in_obsidian in attachments

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]
    obsidian_note_file = [f for f in srs_folder_in_obsidian.iterdir() if f.is_file()][0]

    assert first_field.to_markdown() == f"Some front with ![]({attachments[expected_image_file_name_in_obsidian]})"
    assert (  # Obsidian makes path ULR-safe
        f"{urllib.parse.quote(string=attachments[expected_image_file_name_in_obsidian].name)}"
        in obsidian_note_file.read_text()
    )
    assert len(first_field.references) == 1

    obsidian_reference = obsidian_note.content.fields[0].references[0]

    assert isinstance(obsidian_reference, ObsidianMediaReference)
    assert check_files_are_identical(first=temp_file_path, second=obsidian_reference.path)


def test_sync_new_anki_note_with_tag_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    front_field_html = f"Some front"
    back_field_html = "Some back"
    tag = "test"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
        tags=[tag],
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]

    assert tag in obsidian_note.content.properties.tags


def test_sync_new_anki_note_with_external_link_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    external_url = "http://www.example.com"
    front_field_html = f"Some front with <a href=\"{external_url}\">external site</a>"
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert f"[external site]({external_url})" in first_field.to_markdown()


def test_sync_new_anki_note_with_math_equations_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    in_line_equation = "x = 1"
    block_equation = "x = 2"
    front_field_html = f"""Some front with an in-line math equation \({in_line_equation}\)
and a block equation:&nbsp;\[{block_equation}\]"""
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert f"${in_line_equation}$" in first_field.to_markdown()
    assert f"$${block_equation}$$" in first_field.to_markdown()


def test_sync_new_anki_note_with_math_equation_underscores_to_obsidian_without_treating_underscores_as_italics(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    """The translator treated underscores as italicization even if it's in an equation."""
    equation = "\sum_{i \in C^+j}y_i + \sum{i \in C^-_j}(1 - y_i)"
    front_field_html = f"""
Some front with an in-line math equation \({equation}\) and a block equation:&nbsp;\[{equation}\]
"""
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert f"${equation}$" in first_field.to_markdown()
    assert f"$${equation}$$" in first_field.to_markdown()

    anki_note = anki_test_app.get_note_by_id(note_id=anki_note.id)

    assert f"\({equation}\)" in anki_note.content.fields[0].text
    assert f"\[{equation}\]" in anki_note.content.fields[0].text


def test_sync_new_anki_note_with_plain_text_equal_sign_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    front_field = "Some front with plain-text equation x = 2 and one more x=2"
    back_field = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field,
        back_text=back_field,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert front_field in first_field.to_markdown()

    anki_note = anki_test_app.get_note_by_id(note_id=anki_note.id)

    assert front_field in anki_note.content.fields[0].text


def test_sync_new_anki_note_with_code_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    in_line_code = "code variable"
    block_code = "block code"
    front_field_html = f"""<p>Some front with an in-line <code>{in_line_code}</code>&nbsp;</p>
<pre><code>{block_code}
</code></pre>
<p>and a final line</p>"""
    expected_front_field_markdown = f"""Some front with an in-line `{in_line_code}`\xa0


```
{block_code}
```


and a final line"""
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert first_field.to_markdown() == expected_front_field_markdown


def test_sync_new_anki_note_with_list_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    front_field_html = """<p>Elements are the following</p>
<ul>
<li><strong>e1</strong> first element,</li>
<li><strong>e2</strong> second element</li>
</ul>"""
    expected_front_field_markdown = """Elements are the following

* **e1** first element,
* **e2** second element"""
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert first_field.to_markdown() == expected_front_field_markdown


def test_anki_note_in_obsidian_remains_the_same_on_subsequent_sync(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    front_field_html = "Some front"
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    first_sync_obsidian_note = obsidian_notes_manager.get_all_notes_categorized().unchanged_notes[anki_note.id]
    time.sleep(1)

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()

    assert len(obsidian_notes_result.unchanged_notes) == 1
    assert len(obsidian_notes_result.new_notes) == 0

    second_sync_obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]

    assert first_sync_obsidian_note == second_sync_obsidian_note


def test_corrupted_note_in_obsidian_gets_replaced_on_sync(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    srs_folder_in_obsidian: Path,
    obsidian_notes_manager: ObsidianNotesManager,
):
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    time.sleep(1)

    obsidian_note_file = list(srs_folder_in_obsidian.iterdir())[0]
    obsidian_note_file_lines = obsidian_note_file.read_text().splitlines()
    obsidian_note_file_lines.pop(2)  # corrupts file by removing the model name property
    obsidian_note_file.write_text("\n".join(obsidian_note_file_lines))

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()

    assert len(obsidian_notes_result.unchanged_notes) == 1

    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]

    assert obsidian_note.properties.model_name == "Basic"


def test_sync_existing_anki_note_with_updated_field_in_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    initial_front_field = "Some front"
    updated_front_field = "Some back alt"
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text=initial_front_field,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    time.sleep(1)  # shouldn't do many of those or the test time will stack up quick

    anki_note.content.fields[0].text = updated_front_field
    anki_test_app.update_anki_note_with_note(reference_note=anki_note)

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()

    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]

    assert obsidian_note.content.fields[0].text == updated_front_field


def test_remove_deleted_anki_note_from_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()

    assert len(obsidian_notes_result.unchanged_notes) == 1
    assert len(obsidian_notes_result.new_notes) == 0

    anki_test_app.delete_note_in_anki(note=anki_note)

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()

    assert len(obsidian_notes_result.unchanged_notes) == 0
    assert len(obsidian_notes_result.new_notes) == 0


def test_syncing_note_deleted_in_both_systems(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    first_anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some other front",
        back_text="Some back",
    )
    second_anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()

    assert len(obsidian_notes_result.unchanged_notes) == 2
    assert len(anki_test_app.get_all_notes()) == 2

    anki_test_app.delete_note_in_anki(note=first_anki_note)
    obsidian_notes = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_notes_manager.delete_note(note=obsidian_notes.unchanged_notes[first_anki_note.id])

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()

    assert len(obsidian_notes_result.unchanged_notes) == 1
    assert second_anki_note.id in obsidian_notes_result.unchanged_notes
    assert len(anki_test_app.get_all_notes()) == 1
    assert second_anki_note.id in anki_test_app.get_all_notes()
