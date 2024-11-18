from pathlib import Path
from typing import List

from PIL import Image as PILImage

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.anki.anki_content import AnkiNoteContent, AnkiNoteProperties, AnkiField, AnkiLinkedAttachment
from obsidian_sync.anki.anki_note import AnkiNote
from obsidian_sync.constants import MARKDOWN_FILE_SUFFIX, SRS_NOTE_IDENTIFIER_COMMENT, DATETIME_FORMAT, \
    MODEL_ID_PROPERTY_NAME, MODEL_NAME_PROPERTY_NAME, NOTE_ID_PROPERTY_NAME, TAGS_PROPERTY_NAME, \
    DATE_MODIFIED_PROPERTY_NAME, DATE_SYNCED_PROPERTY_NAME, SRS_NOTE_FIELD_IDENTIFIER_COMMENT, SRS_HEADER_TITLE_LEVEL, \
    DEFAULT_NODE_ID_FOR_NEW_NOTES
from obsidian_sync.file_utils import check_files_are_identical
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.synchronizers.notes_synchronizer import NotesSynchronizer
from tests.anki_test_app import AnkiTestApp


def build_basic_anki_note(
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    front_text: str,
    back_text: str,
    front_attachments: List[AnkiLinkedAttachment] = None,
    back_attachments: List[AnkiLinkedAttachment] = None,
    tags: List[str] = None,
) -> AnkiNote:
    model_name = "Basic"
    model_id = anki_test_app.get_model_id(model_name=model_name)
    note = AnkiNote(
        anki_app=anki_test_app,
        markup_translator=markup_translator,
        content=AnkiNoteContent(
            properties=AnkiNoteProperties(
                model_id=model_id,
                model_name=model_name,
                note_id=DEFAULT_NODE_ID_FOR_NEW_NOTES,
                tags=tags or [],
                date_modified_in_anki=None,
            ),
            fields=[
                AnkiField(
                    name="Front",
                    text=front_text,
                    attachments=front_attachments or [],
                    _markup_translator=markup_translator,
                ),
                AnkiField(
                    name="Back",
                    text=back_text,
                    attachments=back_attachments or [],
                    _markup_translator=markup_translator,
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
):
    model_name = "Basic"
    model_id = anki_test_app.get_model_id(model_name=model_name)
    note_text = f"""---
{MODEL_ID_PROPERTY_NAME}: {model_id}
{MODEL_NAME_PROPERTY_NAME}: Basic
{NOTE_ID_PROPERTY_NAME}: {DEFAULT_NODE_ID_FOR_NEW_NOTES}
{TAGS_PROPERTY_NAME}: []
{DATE_MODIFIED_PROPERTY_NAME}:
{DATE_SYNCED_PROPERTY_NAME}:
---
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


def test_sync_new_anki_note_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    obsidian_vault: ObsidianVault,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    front_field_html = "Some front"
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        markup_translator=markup_translator,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )
    existing_notes, new_notes = obsidian_vault.get_all_obsidian_notes()

    assert len(existing_notes) == 0
    assert len(new_notes) == 0
    assert not srs_folder_in_obsidian.exists()

    notes_synchronizer.synchronize_notes()
    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()

    assert len(existing_obsidian_notes) == 1
    assert srs_folder_in_obsidian.exists()
    assert len(list(srs_folder_in_obsidian.iterdir())) == 1

    obsidian_note = existing_obsidian_notes[anki_note.id]
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
{DATE_SYNCED_PROPERTY_NAME}: '{obsidian_note.properties.date_synced.strftime(DATETIME_FORMAT)}'
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


def test_sync_new_anki_note_with_attachment_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    tmp_path: Path,
    some_test_image: PILImage,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    srs_attachments_in_obsidian_folder: Path,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault: ObsidianVault,
):
    image_file_name = "img.png"
    temp_file_path = tmp_path / image_file_name
    some_test_image.save(temp_file_path)
    front_field_html = f"Some front with <img src=\"{image_file_name}\">"
    back_field_html = "Some back"
    anki_attachment = AnkiLinkedAttachment(path=temp_file_path)
    anki_attachment.path = anki_test_app.ensure_attachment_is_in_anki(attachment=anki_attachment)
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        markup_translator=markup_translator,
        front_text=front_field_html,
        back_text=back_field_html,
        front_attachments=[anki_attachment],
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

    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()
    obsidian_note = existing_obsidian_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert first_field.to_markdown() == f"Some front with ![]({attachments[image_file_name]})"
    assert len(first_field.attachments) == 1

    obsidian_attachment = obsidian_note.content.fields[0].attachments[0]

    assert check_files_are_identical(first=temp_file_path, second=obsidian_attachment.path)


def test_sync_new_anki_note_with_tag_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault: ObsidianVault,
):
    front_field_html = f"Some front"
    back_field_html = "Some back"
    tag = "test"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        markup_translator=markup_translator,
        front_text=front_field_html,
        back_text=back_field_html,
        tags=[tag],
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()
    obsidian_note = existing_obsidian_notes[anki_note.id]

    assert tag in obsidian_note.content.properties.tags


def test_sync_new_anki_note_with_external_link_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault: ObsidianVault,
):
    external_url = "http://www.example.com"
    front_field_html = f"Some front with <a href=\"{external_url}\">external site</a>"
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        markup_translator=markup_translator,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()
    obsidian_note = existing_obsidian_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert f"[external site]({external_url})" in first_field.to_markdown()


def test_sync_new_anki_note_with_math_equations_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault: ObsidianVault,
):
    in_line_equation = "x = 1"
    block_equation = "x = 2"
    front_field_html = f"""Some front with an in-line math equation <anki-mathjax>{in_line_equation}</anki-mathjax>
and a block equation:&nbsp;<anki-mathjax block="true">{block_equation}</anki-mathjax>"""
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        markup_translator=markup_translator,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()
    obsidian_note = existing_obsidian_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert f"${in_line_equation}$" in first_field.to_markdown()
    assert f"$${block_equation}$$" in first_field.to_markdown()


def test_sync_new_anki_note_with_code_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault: ObsidianVault,
):
    in_line_code = "code variable"
    block_code = "block code"
    front_field_html = f"""Some front with an in-line <code>{in_line_code}</code> and a <pre>{block_code}</pre>"""
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        markup_translator=markup_translator,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()
    obsidian_note = existing_obsidian_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert f"`{in_line_code}`" in first_field.to_markdown()
    assert f"```\n{block_code}\n```" in first_field.to_markdown()


def test_anki_note_in_obsidian_remains_the_same_on_subsequent_sync(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    markup_translator: MarkupTranslator,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault: ObsidianVault,
):
    front_field_html = "Some front"
    back_field_html = "Some back"
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        markup_translator=markup_translator,
        front_text=front_field_html,
        back_text=back_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    first_sync_obsidian_note = obsidian_vault.get_all_obsidian_notes()[0][anki_note.id]

    notes_synchronizer.synchronize_notes()

    second_sync_obsidian_note = obsidian_vault.get_all_obsidian_notes()[0][anki_note.id]

    assert first_sync_obsidian_note == second_sync_obsidian_note


def test_sync_new_obsidian_note_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    addon_config: AddonConfig,
    obsidian_config: ObsidianConfig,
    markup_translator: MarkupTranslator,
    notes_synchronizer: NotesSynchronizer,
    obsidian_vault: ObsidianVault,
):
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
    )
    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()

    assert len(existing_obsidian_notes) == 0
    assert len(new_obsidian_notes) == 1
    assert len(anki_test_app.get_all_notes()) == 0

    notes_synchronizer.synchronize_notes()

    assert len(anki_test_app.get_all_notes()) == 1

    anki_note = list(anki_test_app.get_all_notes().values())[0]
    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()
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
    obsidian_vault: ObsidianVault,
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
    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()

    assert len(existing_obsidian_notes) == 0
    assert len(new_obsidian_notes) == 2
    assert len(anki_test_app.get_all_notes()) == 0

    notes_synchronizer.synchronize_notes()

    anki_notes = anki_test_app.get_all_notes()
    existing_obsidian_notes, new_obsidian_notes = obsidian_vault.get_all_obsidian_notes()

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
    image_file_name = "img.png"
    srs_attachments_in_obsidian_folder.mkdir(parents=True)
    image_file_path = srs_attachments_in_obsidian_folder / image_file_name
    some_test_image.save(image_file_path)
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back with ![image](img.png)",
        file_path=srs_folder_in_obsidian / "test.md",
    )

    assert len(list(anki_test_app.media_directory.iterdir())) == 0

    notes_synchronizer.synchronize_notes()

    assert len(list(anki_test_app.media_directory.iterdir())) == 1

    anki_note = list(anki_test_app.get_all_notes().values())[0]
    attachment_file = Path(list(anki_test_app.media_directory.iterdir())[0])

    assert len(anki_note.content.fields[1].attachments) == 1
    assert anki_note.content.fields[1].attachments[0].path == attachment_file
    assert anki_note.content.fields[1].text == f"<p>Some back with <img alt=\"image\" src=\"{attachment_file}\" /></p>"







# def test_update_anki_note_field_in_obsidian():
#     raise NotImplementedError
#
#
# def test_update_anki_media_in_obsidian(
#     tmp_path: Path,
#     srs_attachments_in_obsidian_folder_mock: Path,
#     anki_mocker: AnkiMocker,
#     some_test_image: PILImage,
#     second_test_image: PILImage,
# ):
#     srs_attachments_in_obsidian_folder_mock.mkdir(parents=True)
#     obsidian_image_file = srs_attachments_in_obsidian_folder_mock / "img.jpg"
#     obsidian_image_file_duplicat = tmp_path / "img-back.jpg"
#     some_test_image.save(obsidian_image_file)
#     shutil.copy(src=obsidian_image_file, dst=obsidian_image_file_duplicat)
#
#     anki_image_file = tmp_path / "img.jpg"
#     second_test_image.save(anki_image_file)
#     anki_mocker.set_media_files(files=[anki_image_file])
#
#     assert obsidian_image_file != obsidian_image_file_duplicat
#     assert filecmp.cmp(f1=obsidian_image_file, f2=obsidian_image_file_duplicat, shallow=False)
#     assert not filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file, shallow=False)
#     assert not filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file_duplicat, shallow=False)
#
#     media_synchronizer.synchronize_media()
#
#     assert len(anki_mocker.get_added_media_files()) == 0
#     assert not filecmp.cmp(f1=obsidian_image_file, f2=obsidian_image_file_duplicat, shallow=False)
#     assert filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file, shallow=False)
#
#
# def test_update_obsidian_note_field_in_anki():
#     raise NotImplementedError
#
#
# def test_update_obsidian_media_in_anki(
#     tmp_path: Path,
#     srs_attachments_in_obsidian_folder_mock: Path,
#     anki_mocker: AnkiMocker,
#     some_test_image: PILImage,
#     second_test_image: PILImage,
# ):
#     anki_image_file = tmp_path / "img.jpg"
#     second_test_image.save(anki_image_file)
#     anki_mocker.set_media_files(files=[anki_image_file])
#
#     srs_attachments_in_obsidian_folder_mock.mkdir(parents=True)
#     obsidian_image_file = srs_attachments_in_obsidian_folder_mock / "img.jpg"
#     obsidian_image_file_duplicat = tmp_path / "img-back.jpg"
#     some_test_image.save(obsidian_image_file)
#     shutil.copy(src=obsidian_image_file, dst=obsidian_image_file_duplicat)
#
#     assert obsidian_image_file != obsidian_image_file_duplicat
#     assert filecmp.cmp(f1=obsidian_image_file, f2=obsidian_image_file_duplicat, shallow=False)
#     assert not filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file, shallow=False)
#     assert not filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file_duplicat, shallow=False)
#
#     media_synchronizer.synchronize_media()
#
#     assert len(anki_mocker.get_added_media_files()) == 1
#     assert anki_mocker.get_added_media_files()[0] == obsidian_image_file
#     assert filecmp.cmp(f1=obsidian_image_file, f2=obsidian_image_file_duplicat, shallow=False)


# def test_remove_deleted_anki_note_from_obsidian():
#     raise NotImplementedError
#
#
# def test_remove_deleted_obsidian_note_from_anki():
#     raise NotImplementedError
