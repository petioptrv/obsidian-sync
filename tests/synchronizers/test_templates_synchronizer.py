from pathlib import Path

from obsidian_sync.constants import MARKDOWN_FILE_SUFFIX, \
    MODEL_NAME_PROPERTY_NAME, NOTE_ID_PROPERTY_NAME, TAGS_PROPERTY_NAME, \
    DATE_MODIFIED_PROPERTY_NAME, DATE_SYNCED_PROPERTY_NAME, \
    SRS_NOTE_IDENTIFIER_COMMENT, SRS_NOTE_FIELD_IDENTIFIER_COMMENT, SRS_HEADER_TITLE_LEVEL
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
    anki_test_app.remove_all_note_models()

    model_name = "Basic"  # Basic always added as default

    assert len(obsidian_templates_manager.get_all_obsidian_templates()) == 0

    templates_synchronizer.synchronize_templates()

    obsidian_templates = obsidian_templates_manager.get_all_obsidian_templates()

    assert len(obsidian_templates) == 1
    assert len(list(obsidian_templates_folder.iterdir())) == 1

    obsidian_template = list(obsidian_templates.values())[0]

    assert obsidian_template.model_name == model_name
    assert obsidian_template.file.path.name == f"{model_name}{MARKDOWN_FILE_SUFFIX}"
    assert len(obsidian_template.fields) == 2
    assert obsidian_template.fields[0].name == "Front"
    assert obsidian_template.fields[1].name == "Back"


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
{NOTE_ID_PROPERTY_NAME}: 0
{TAGS_PROPERTY_NAME}: 
{DATE_MODIFIED_PROPERTY_NAME}:
{DATE_SYNCED_PROPERTY_NAME}: 
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
