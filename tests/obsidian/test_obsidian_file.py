import json
import urllib.parse
from datetime import datetime
from pathlib import Path

from PIL import Image as PILImage

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.constants import SRS_NOTE_FIELD_IDENTIFIER_COMMENT, MARKDOWN_FILE_SUFFIX, \
    SRS_NOTE_IDENTIFIER_COMMENT, \
    SRS_HEADER_TITLE_LEVEL, MODEL_ID_PROPERTY_NAME, \
    MODEL_NAME_PROPERTY_NAME, NOTE_ID_PROPERTY_NAME, TAGS_PROPERTY_NAME, \
    DEFAULT_NOTE_ID_FOR_NEW_NOTES, DATE_MODIFIED_PROPERTY_NAME, DATETIME_FORMAT
from obsidian_sync.obsidian.content.field.obsidian_note_field import ObsidianNoteFieldFactory
from obsidian_sync.obsidian.content.field.obsidian_template_field import ObsidianTemplateFieldFactory
from obsidian_sync.obsidian.content.obsidian_properties import ObsidianTemplateProperties, ObsidianNoteProperties
from obsidian_sync.obsidian.content.obsidian_reference import ObsidianMediaReference
from obsidian_sync.obsidian.obsidian_file import ObsidianNoteFile, ObsidianTemplateFile


def test_parse_template(
    tmp_path: Path,
    addon_config: AddonConfig,
    obsidian_template_field_factory: ObsidianTemplateFieldFactory,
):
    file_content = f"""---
{MODEL_ID_PROPERTY_NAME}: 1
{MODEL_NAME_PROPERTY_NAME}: Basic
{NOTE_ID_PROPERTY_NAME}: {DEFAULT_NOTE_ID_FOR_NEW_NOTES}
{TAGS_PROPERTY_NAME}: []
{DATE_MODIFIED_PROPERTY_NAME}: {json.dumps(None)}
---
{SRS_NOTE_IDENTIFIER_COMMENT}

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Front


{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Back


"""
    file_path = tmp_path / f"test_file{MARKDOWN_FILE_SUFFIX}"
    file_path.write_text(file_content)

    file = ObsidianTemplateFile(
        path=file_path, addon_config=addon_config, field_factory=obsidian_template_field_factory
    )

    assert isinstance(file.properties, ObsidianTemplateProperties)
    assert file.properties.model_id == 1
    assert file.properties.note_id == 0
    assert len(file.properties.tags) == 0
    assert len(file.fields) == 2
    assert file.fields[0].name == "Front"
    assert file.fields[0].text == ""
    assert file.fields[1].name == "Back"
    assert file.fields[1].text == ""


def test_parse_note_properties(
    tmp_path: Path,
    addon_config: AddonConfig,
    obsidian_note_field_factory: ObsidianNoteFieldFactory,
):
    file_content = f"""---
{MODEL_ID_PROPERTY_NAME}: 1
{MODEL_NAME_PROPERTY_NAME}: Basic
{NOTE_ID_PROPERTY_NAME}: 2
{TAGS_PROPERTY_NAME}:
  - one
{DATE_MODIFIED_PROPERTY_NAME}: {datetime.now().strftime(DATETIME_FORMAT)}
---
{SRS_NOTE_IDENTIFIER_COMMENT}

"""
    file_path = tmp_path / f"test_file{MARKDOWN_FILE_SUFFIX}"
    file_path.write_text(file_content)

    file = ObsidianNoteFile(
        path=file_path, addon_config=addon_config, field_factory=obsidian_note_field_factory
    )

    assert isinstance(file.properties, ObsidianNoteProperties)
    assert file.properties.note_id == 2
    assert file.properties.tags == ["one"]


def test_parse_note_fields(
    some_test_image: PILImage,
    obsidian_vault_folder: Path,
    srs_folder_in_obsidian: Path,
    srs_attachments_in_obsidian_folder: Path,
    addon_config: AddonConfig,
    obsidian_note_field_factory: ObsidianNoteFieldFactory,
):
    srs_attachments_in_obsidian_folder.mkdir(parents=True)
    image_file = srs_attachments_in_obsidian_folder / "img.jpg"
    some_test_image.save(image_file)
    file_content = f"""{
    ObsidianNoteProperties(
        model_id=1,
        model_name="Basic",
        note_id=2,
        tags=[],
        date_modified_in_anki=datetime.now(),
    ).to_obsidian_file_text()
}
{SRS_NOTE_IDENTIFIER_COMMENT}

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Front
Some front

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Back
Some back [image link]({urllib.parse.quote(string=str(image_file.relative_to(obsidian_vault_folder)))})

"""
    file_path = srs_folder_in_obsidian / f"test_file{MARKDOWN_FILE_SUFFIX}"
    file_path.write_text(file_content)

    file = ObsidianNoteFile(
        path=file_path, addon_config=addon_config, field_factory=obsidian_note_field_factory
    )

    assert len(file.fields) == 2

    assert file.fields[0].name == "Front"
    assert file.fields[0].text == "Some front"
    assert len(file.fields[0].references) == 0

    assert file.fields[1].name == "Back"
    assert file.fields[1].text == f"Some back [image link]({image_file})"

    media_reference = file.fields[1].references[0]

    assert isinstance(media_reference, ObsidianMediaReference)
    assert media_reference.path == image_file
