import json
from pathlib import Path

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.constants import MARKDOWN_FILE_SUFFIX, \
    MODEL_NAME_PROPERTY_NAME, NOTE_ID_PROPERTY_NAME, TAGS_PROPERTY_NAME, \
    SRS_NOTE_IDENTIFIER_COMMENT, SRS_NOTE_FIELD_IDENTIFIER_COMMENT, SRS_HEADER_TITLE_LEVEL, \
    CONF_ADD_OBSIDIAN_URL_IN_ANKI, OBSIDIAN_LINK_URL_FIELD_NAME, DEFAULT_NOTE_ID_FOR_NEW_NOTES, \
    MODEL_ID_PROPERTY_NAME, DATE_MODIFIED_PROPERTY_NAME
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_templates_manager import ObsidianTemplatesManager
from obsidian_sync.synchronizers.templates_synchronizer import TemplatesSynchronizer
from tests.anki_test_app import AnkiTestApp
from tests.constants import DEFAULT_ANKI_TEMPLATES_COUNT


def test_create_new_anki_template_in_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    obsidian_templates_manager: ObsidianTemplatesManager,
    obsidian_templates_folder: Path,
    templates_synchronizer: TemplatesSynchronizer,
):
    anki_test_app.remove_all_note_models()  # the default Basic model is always kept by Anki

    assert len(obsidian_templates_manager.get_all_obsidian_templates()) == 0

    templates_synchronizer.synchronize_templates()

    anki_templates = anki_test_app.get_all_anki_templates()
    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()

    assert len(obsidian_templates) == 1
    assert len(list(obsidian_templates_folder.iterdir())) == 1

    anki_template = list(anki_templates.values())[0]
    obsidian_template = list(obsidian_templates.values())[0]

    assert obsidian_template.file.path.name == f"{anki_template.model_name}{MARKDOWN_FILE_SUFFIX}"

    # properties
    assert obsidian_template.properties.model_id == anki_template.model_id
    assert obsidian_template.properties.model_name == anki_template.model_name
    assert obsidian_template.properties.note_id == DEFAULT_NOTE_ID_FOR_NEW_NOTES
    assert obsidian_template.properties.tags == []

    # fields
    assert len(obsidian_template.fields) == 2
    assert obsidian_template.fields[0].name == "Front"
    assert obsidian_template.fields[1].name == "Back"

    expected_text = f"""---
{MODEL_ID_PROPERTY_NAME}: {anki_template.model_id}
{MODEL_NAME_PROPERTY_NAME}: {anki_template.model_name}
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

    template_file = list(obsidian_templates_folder.iterdir())[0]

    assert template_file.read_text() == expected_text


def test_create_a_new_anki_template_in_obsidian_after_resolving_a_template_name_collision_with_an_existing_user_template(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    obsidian_config: ObsidianConfig,
    anki_test_app: AnkiTestApp,
    obsidian_templates_manager: ObsidianTemplatesManager,
    obsidian_templates_folder: Path,
    templates_synchronizer: TemplatesSynchronizer,
):
    anki_test_app.remove_all_note_models()  # the default Basic model is always kept by Anki
    already_existing_basic_template = obsidian_templates_folder / "Basic.md"
    obsidian_templates_folder.mkdir(parents=True, exist_ok=True)
    already_existing_basic_template.touch()

    templates_synchronizer.synchronize_templates()

    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()

    assert len(obsidian_templates) == 1

    basic_template = list(obsidian_templates.values())[0]

    assert basic_template.file.path == (
        obsidian_templates_folder / f"Basic-{basic_template.content.properties.model_id}.md"
    )


def test_add_obsidian_url_field_to_anki_templates_on_sync(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    addon_config: AddonConfig,
    templates_synchronizer: TemplatesSynchronizer,
    anki_test_app: AnkiTestApp,
    obsidian_templates_manager: ObsidianTemplatesManager,
):
    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=True)

    templates_synchronizer.synchronize_templates()

    anki_templates = anki_test_app.get_all_anki_templates()
    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()

    for model_id, anki_template in anki_templates.items():
        obsidian_template = obsidian_templates[model_id]
        assert len(anki_template.content.fields) == len(obsidian_template.content.fields)
        assert anki_template.content.fields[-1].name == OBSIDIAN_LINK_URL_FIELD_NAME
        assert obsidian_template.content.fields[-1].name == OBSIDIAN_LINK_URL_FIELD_NAME


def test_handle_user_repositioning_the_obsidian_url_field_in_anki_model(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    addon_config: AddonConfig,
    templates_synchronizer: TemplatesSynchronizer,
    anki_test_app: AnkiTestApp,
    obsidian_templates_manager: ObsidianTemplatesManager,
):
    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=True)

    templates_synchronizer.synchronize_templates()
    new_obsidian_url_model_field_index = 1
    anki_test_app.move_model_field(
        model_name="Basic", field_name=OBSIDIAN_LINK_URL_FIELD_NAME, new_field_index=new_obsidian_url_model_field_index
    )
    templates_synchronizer.synchronize_templates()

    anki_templates = anki_test_app.get_all_anki_templates()
    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()
    model_id, anki_template = next(
        (mid, at)
        for mid, at in anki_templates.items()
        if at.model_name == "Basic"
    )

    obsidian_template = obsidian_templates[model_id]
    assert len(anki_template.content.fields) == len(obsidian_template.content.fields)
    assert anki_template.content.fields[0].name == obsidian_template.content.fields[0].name  # Front
    assert anki_template.content.fields[1].name == OBSIDIAN_LINK_URL_FIELD_NAME
    assert anki_template.content.fields[1].name == obsidian_template.content.fields[2].name  # Obsidian URL
    assert anki_template.content.fields[2].name == obsidian_template.content.fields[1].name  # Back


def test_remove_obsidian_url_field_from_anki_templates_on_sync(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    addon_config: AddonConfig,
    templates_synchronizer: TemplatesSynchronizer,
    anki_test_app: AnkiTestApp,
    obsidian_templates_manager: ObsidianTemplatesManager,
):
    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=True)

    templates_synchronizer.synchronize_templates()

    anki_test_app.set_config_value(config_name=CONF_ADD_OBSIDIAN_URL_IN_ANKI, value=False)

    templates_synchronizer.synchronize_templates()

    anki_templates = anki_test_app.get_all_anki_templates()
    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()

    for model_id, anki_template in anki_templates.items():
        obsidian_template = obsidian_templates[model_id]
        assert len(anki_template.content.fields) == len(obsidian_template.content.fields)
        assert all(field.name != OBSIDIAN_LINK_URL_FIELD_NAME for field in anki_template.content.fields)
        assert all(field.name != OBSIDIAN_LINK_URL_FIELD_NAME for field in obsidian_template.content.fields)


def test_update_anki_template_in_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    obsidian_templates_manager: ObsidianTemplatesManager,
    obsidian_templates_folder: Path,
    templates_synchronizer: TemplatesSynchronizer,
):
    anki_test_app.remove_all_note_models()

    model_name = "Basic"  # Basic always added as default

    templates_synchronizer.synchronize_templates()

    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()
    obsidian_template = list(obsidian_templates.values())[0]

    assert obsidian_template.fields[0].name == "Front"

    anki_test_app.rename_model_field(model_name=model_name, field_order=0, new_name="Front Alt")

    templates_synchronizer.synchronize_templates()

    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()
    obsidian_template = list(obsidian_templates.values())[0]

    assert obsidian_template.fields[0].name == "Front Alt"


def test_remove_deleted_anki_template_from_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    obsidian_templates_manager: ObsidianTemplatesManager,
    obsidian_templates_folder: Path,
    templates_synchronizer: TemplatesSynchronizer,
):
    templates_synchronizer.synchronize_templates()

    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()

    assert len(obsidian_templates) == DEFAULT_ANKI_TEMPLATES_COUNT
    assert len(list(obsidian_templates_folder.iterdir())) == DEFAULT_ANKI_TEMPLATES_COUNT

    anki_test_app.remove_all_note_models()

    templates_synchronizer.synchronize_templates()

    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()

    assert len(obsidian_templates) == 1  # Anki always add the default front-and-back template
    assert len(list(obsidian_templates_folder.iterdir())) == 1


def test_overwrite_corrupted_template_without_srs_file_identifier_in_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    obsidian_templates_manager: ObsidianTemplatesManager,
    obsidian_templates_folder: Path,
    templates_synchronizer: TemplatesSynchronizer,
):

    corrupt_template_file_content = ""
    obsidian_templates_folder.mkdir(parents=True)
    file_path = obsidian_templates_folder / f"Basic{MARKDOWN_FILE_SUFFIX}"
    file_path.write_text(corrupt_template_file_content)

    anki_test_app.remove_all_note_models()

    model_name = "Basic"  # Basic always added as default

    templates_synchronizer.synchronize_templates()
    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()

    assert len(obsidian_templates) == 1

    obsidian_template = list(obsidian_templates.values())[0]

    assert obsidian_template.properties.model_name == model_name


def test_overwrite_corrupted_template_with_srs_file_identifier_in_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    obsidian_config: ObsidianConfig,
    obsidian_templates_manager: ObsidianTemplatesManager,
    obsidian_templates_folder: Path,
    templates_synchronizer: TemplatesSynchronizer,
):

    # the corrupt file has the model ID field omitted
    corrupt_template_file_content = f"""---
{MODEL_NAME_PROPERTY_NAME}: Basic
---
{SRS_NOTE_IDENTIFIER_COMMENT}

{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Front


{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}
{SRS_HEADER_TITLE_LEVEL} Back


"""
    obsidian_templates_folder.mkdir(parents=True)
    file_path = obsidian_templates_folder / f"Basic{MARKDOWN_FILE_SUFFIX}"
    file_path.write_text(corrupt_template_file_content)

    anki_test_app.remove_all_note_models()

    model_name = "Basic"  # Basic always added as default

    templates_synchronizer.synchronize_templates()
    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()

    assert len(obsidian_templates) == 1

    obsidian_template = list(obsidian_templates.values())[0]

    assert obsidian_template.properties.model_name == model_name
