from pathlib import Path
from unittest.mock import MagicMock

from obsidian_sync.constants import OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE, MARKDOWN_FILE_SUFFIX
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.synchronizers.templates_synchronizer import TemplatesSynchronizer
from tests.anki_mock import AnkiMocker, MockAnkiTemplate, MockAnkiField


def test_create_new_anki_template_in_obsidian(
    anki_mocker: AnkiMocker,
    obsidian_vault: ObsidianVault,
    obsidian_templates_folder_mock: Path,
    templates_synchronizer: TemplatesSynchronizer,
):
    template_id = 1
    template_name = "Basic"
    templates = [
        MockAnkiTemplate(
            id=template_id,
            name=template_name,
            flds=[
                MockAnkiField(name="Front"),
                MockAnkiField(name="Back"),
            ]
        )
    ]
    anki_mocker.set_mock_templates(mock_templates=templates)

    assert len(obsidian_vault.get_all_obsidian_templates()) == 0

    templates_synchronizer.synchronize_templates()

    obsidian_templates = obsidian_vault.get_all_obsidian_templates()

    assert len(obsidian_templates) == 1
    assert len(list(obsidian_templates_folder_mock.iterdir())) == 1

    obsidian_template = obsidian_templates[1]

    assert obsidian_template.properties.model_id == template_id
    assert obsidian_template.model_name == template_name
    assert obsidian_template.file.path.name == f"{template_name}.{MARKDOWN_FILE_SUFFIX}"
    assert len(obsidian_template.fields) == 2
    assert obsidian_template.fields[0].name == "Front"
    assert obsidian_template.fields[1].name == "Back"


def test_update_anki_template_in_obsidian(
    obsidian_config_mock: MagicMock,
    anki_mocker: AnkiMocker,
    templates_synchronizer: TemplatesSynchronizer,
    obsidian_vault: ObsidianVault,
    obsidian_templates_folder_mock: Path,
):
    obsidian_config_mock.trash_option = OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE

    template_id = 1
    template_name = "Basic"
    anki_template = MockAnkiTemplate(
        id=template_id,
        name=template_name,
        flds=[
            MockAnkiField(name="Front"),
            MockAnkiField(name="Back"),
        ]
    )
    templates = [anki_template]
    anki_mocker.set_mock_templates(mock_templates=templates)

    templates_synchronizer.synchronize_templates()

    anki_template.name = template_name + "Alt"
    anki_template.flds[0].name = "Front Alt"
    anki_mocker.set_mock_templates(mock_templates=templates)

    templates_synchronizer.synchronize_templates()

    obsidian_templates = obsidian_vault.get_all_obsidian_templates()

    assert len(obsidian_templates) == 1
    assert len(list(obsidian_templates_folder_mock.iterdir())) == 1

    obsidian_template = obsidian_templates[1]

    assert obsidian_template.properties.model_id == template_id
    assert obsidian_template.model_name == template_name + "Alt"
    assert len(obsidian_template.fields) == 2
    assert obsidian_template.fields[0].name == "Front Alt"
    assert obsidian_template.fields[1].name == "Back"


def test_remove_deleted_anki_template_from_obsidian(
    obsidian_config_mock: MagicMock,
    anki_mocker: AnkiMocker,
    templates_synchronizer: TemplatesSynchronizer,
    obsidian_vault: ObsidianVault,
    obsidian_templates_folder_mock: Path,
):
    obsidian_config_mock.trash_option = OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE

    template_id = 1
    template_name = "Basic"
    anki_template = MockAnkiTemplate(
        id=template_id,
        name=template_name,
        flds=[
            MockAnkiField(name="Front"),
            MockAnkiField(name="Back"),
        ]
    )
    templates = [anki_template]
    anki_mocker.set_mock_templates(mock_templates=templates)

    templates_synchronizer.synchronize_templates()

    anki_mocker.set_mock_templates(mock_templates=[])

    templates_synchronizer.synchronize_templates()

    obsidian_templates = obsidian_vault.get_all_obsidian_templates()

    assert len(obsidian_templates) == 0
    assert len(list(obsidian_templates_folder_mock.iterdir())) == 0
