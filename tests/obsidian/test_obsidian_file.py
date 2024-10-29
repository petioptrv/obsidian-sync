from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image as PILImage

from obsidian_sync.constants import SRS_NOTE_FIELD_IDENTIFIER_COMMENT, MARKDOWN_FILE_SUFFIX, SRS_NOTE_IDENTIFIER_COMMENT, \
    SRS_HEADER_TITLE_LEVEL, TEMPLATE_DATE_FORMAT, TEMPLATE_TIME_FORMAT
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_content import ObsidianTemplateProperties, \
    ObsidianNoteProperties
from obsidian_sync.obsidian.obsidian_file import ObsidianNoteFile, ObsidianTemplateFile


def test_parse_template(
    tmp_path: Path,
    obsidian_config_mock: MagicMock,
    addon_config_mock: MagicMock,
):
    file_content = f"""---
mid: 1
nid: 0
tags: 
date modified: "{{{{date:{TEMPLATE_DATE_FORMAT} {TEMPLATE_TIME_FORMAT}}}}}"
date synced: 
---
{SRS_NOTE_IDENTIFIER_COMMENT}

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Front


{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Back


"""
    file_path = tmp_path / f"test_file.{MARKDOWN_FILE_SUFFIX}"
    file_path.write_text(file_content)

    file = ObsidianTemplateFile(
        path=file_path,
        addon_config=addon_config_mock,
        obsidian_config=obsidian_config_mock,
        markup_translator=MarkupTranslator(),
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
    obsidian_config_mock: MagicMock,
    addon_config_mock: MagicMock,
):
    file_content = f"""{
    ObsidianNoteProperties(
        model_id=1,
        note_id=2,
        tags=["one"],
        date_modified=datetime.now(),
        date_synced=datetime.now(),
    ).to_obsidian_file_text()
}
{SRS_NOTE_IDENTIFIER_COMMENT}

"""
    file_path = tmp_path / f"test_file.{MARKDOWN_FILE_SUFFIX}"
    file_path.write_text(file_content)

    file = ObsidianNoteFile(
        path=file_path,
        addon_config=addon_config_mock,
        obsidian_config=obsidian_config_mock,
        markup_translator=MarkupTranslator(),
    )

    assert isinstance(file.properties, ObsidianNoteProperties)
    assert file.properties.note_id == 2
    assert file.properties.tags == ["one"]


def test_parse_note_fields(
    tmp_path: Path,
    some_test_image: PILImage,
    obsidian_config_mock: MagicMock,
    addon_config_mock: MagicMock,
):
    image_file = tmp_path / "img.jpg"
    some_test_image.save(image_file)
    file_content = f"""{
    ObsidianNoteProperties(
        model_id=1,
        note_id=2,
        tags=[],
        date_modified=datetime.now(),
        date_synced=datetime.now(),
    ).to_obsidian_file_text()
}
{SRS_NOTE_IDENTIFIER_COMMENT}

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Front
Some front

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Back
Some back [image link]({image_file})

"""
    file_path = tmp_path / f"test_file.{MARKDOWN_FILE_SUFFIX}"
    file_path.write_text(file_content)

    file = ObsidianNoteFile(
        path=file_path,
        addon_config=addon_config_mock,
        obsidian_config=obsidian_config_mock,
        markup_translator=MarkupTranslator(),
    )

    assert len(file.fields) == 2

    assert file.fields[0].name == "Front"
    assert file.fields[0].text == "Some front"
    assert len(file.fields[0].images) == 0

    assert file.fields[1].name == "Back"
    assert file.fields[1].text == f"Some back [image link]({image_file})"
    assert file.fields[1].images[0].path == image_file
