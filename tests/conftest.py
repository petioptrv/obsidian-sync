import json
import shutil
import time
from pathlib import Path
from typing import Dict

import pytest
from PIL import Image as PILImage
import aqt

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.addon_metadata import AddonMetadata
from obsidian_sync.anki.app.anki_app import AnkiApp
from obsidian_sync.constants import OBSIDIAN_SETTINGS_FOLDER, OBSIDIAN_APP_SETTINGS_FILE, OBSIDIAN_TRASH_OPTION_KEY, \
    OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE, OBSIDIAN_TEMPLATES_SETTINGS_FILE, OBSIDIAN_TEMPLATES_OPTION_KEY, \
    TEMPLATES_FOLDER_JSON_FIELD_NAME, OBSIDIAN_USE_MARKDOWN_LINKS_OPTION_KEY, CONF_VAULT_PATH, ADD_ON_NAME, \
    CONF_SRS_FOLDER_IN_OBSIDIAN, CONF_SYNC_WITH_OBSIDIAN_ON_ANKI_WEB_SYNC, CONF_ANKI_DECK_NAME_FOR_OBSIDIAN_IMPORTS, \
    SRS_ATTACHMENTS_FOLDER, CONF_ADD_OBSIDIAN_URL_IN_ANKI
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.content.field.obsidian_note_field import ObsidianNoteFieldFactory
from obsidian_sync.obsidian.content.field.obsidian_template_field import ObsidianTemplateFieldFactory
from obsidian_sync.obsidian.content.obsidian_reference import ObsidianReferenceFactory
from obsidian_sync.obsidian.obsidian_notes_manager import ObsidianNotesManager
from obsidian_sync.obsidian.reference_manager import ObsidianReferencesManager
from obsidian_sync.obsidian.obsidian_templates_manager import ObsidianTemplatesManager
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.synchronizers.notes_synchronizer import NotesSynchronizer
from obsidian_sync.synchronizers.templates_synchronizer import TemplatesSynchronizer
from obsidian_sync import addon_metadata as addon_metadata_module
from tests.anki_test_app import AnkiTestApp


@pytest.fixture()
def some_test_image() -> PILImage:
    image = PILImage.new(mode="RGB", size=(1, 1))
    return image


@pytest.fixture()
def second_test_image() -> PILImage:
    image = PILImage.new(mode="RGB", size=(2, 2))
    return image


@pytest.fixture(scope="session")
def markup_translator() -> MarkupTranslator:
    return MarkupTranslator()


# ================== PATHS =============================================================


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def session_dir(tmpdir_factory):
    return Path(tmpdir_factory.mktemp("tmp"))


@pytest.fixture(scope="session")
def anki_base_folder(session_dir: Path) -> Path:
    base_folder = session_dir / "anki"
    base_folder.mkdir(parents=True)
    return base_folder


@pytest.fixture(scope="session")
def anki_logs_folder(anki_base_folder: Path) -> Path:
    logs_folder = anki_base_folder / "logs"
    logs_folder.mkdir(parents=True)
    return logs_folder


@pytest.fixture(scope="session")
def anki_addon_folder(anki_base_folder: Path) -> Path:
    addon_folder = anki_base_folder / "addons21" / ADD_ON_NAME
    addon_folder.mkdir(parents=True)
    return addon_folder


@pytest.fixture(scope="session")
def anki_addon_manifest_file(anki_addon_folder: Path) -> Path:
    manifest_file = anki_addon_folder / "manifest.json"
    return manifest_file


@pytest.fixture(scope="session")
def anki_addon_meta_file(anki_addon_folder: Path) -> Path:
    meta_file = anki_addon_folder / "meta.json"
    return meta_file


@pytest.fixture(scope="session")
def obsidian_vault_folder(session_dir: Path) -> Path:
    vault_folder = session_dir / "obsidian-vault"
    vault_folder.mkdir(parents=True)
    return vault_folder


@pytest.fixture(scope="session")
def obsidian_settings_folder(obsidian_vault_folder: Path) -> Path:
    settings_folder = obsidian_vault_folder / OBSIDIAN_SETTINGS_FOLDER
    settings_folder.mkdir()
    return settings_folder


@pytest.fixture(scope="session")
def srs_folder_in_obsidian(obsidian_vault_folder: Path) -> Path:
    srs_folder = obsidian_vault_folder / "srs-in-obsidian"
    return srs_folder


@pytest.fixture(scope="session")
def obsidian_templates_folder(obsidian_vault_folder: Path) -> Path:
    templates_folder = obsidian_vault_folder / "templates"
    return templates_folder


@pytest.fixture(scope="session")
def srs_attachments_in_obsidian_folder(srs_folder_in_obsidian: Path) -> Path:
    srs_attachments_in_obsidian_folder = srs_folder_in_obsidian / SRS_ATTACHMENTS_FOLDER
    return srs_attachments_in_obsidian_folder


# ================== ANKI ==============================================================


@pytest.fixture(scope="session")
def anki_profile_name() -> str:
    return "test-profile"


@pytest.fixture(scope="session")
def anki_addon_manifest_default_data() -> Dict:
    manifest = {
        "package": "obsidian-sync",
        "name": "Obsidian-Sync",
        "version": "0.0.1"
    }
    return manifest


@pytest.fixture(scope="session")
def anki_addon_meta_default_data(
    obsidian_vault_folder: Path,
    srs_folder_in_obsidian: Path,
    obsidian_settings_folder: Path,
) -> Dict:
    meta = {
        "disabled": False,
        "mod": 0,
        "conflicts": [],
        "max_point_version": 0,
        "min_point_version": 0,
        "branch_index": 0,
        "update_enabled": True,
        "config": {
            CONF_VAULT_PATH: str(obsidian_vault_folder),
            CONF_SRS_FOLDER_IN_OBSIDIAN: str(srs_folder_in_obsidian),
            CONF_SYNC_WITH_OBSIDIAN_ON_ANKI_WEB_SYNC: False,
            CONF_ANKI_DECK_NAME_FOR_OBSIDIAN_IMPORTS: "",
            CONF_ADD_OBSIDIAN_URL_IN_ANKI: False,
        },
    }
    return meta


@pytest.fixture(scope="session")
def aqt_run(
    project_root: Path,
    anki_base_folder: Path,
    anki_logs_folder: Path,
    anki_addon_folder: Path,
    anki_addon_manifest_file: Path,
    anki_addon_manifest_default_data: Dict,
    anki_addon_meta_file: Path,
    anki_addon_meta_default_data: Dict,
    anki_profile_name: str,
) -> aqt.AnkiApp:
    anki_initial_data = project_root / "tests" / "anki-initial-data"
    shutil.copytree(src=anki_initial_data, dst=anki_base_folder, dirs_exist_ok=True)
    shutil.copy(src=project_root / ADD_ON_NAME / "config.json", dst=anki_addon_folder / "config.json")

    anki_addon_manifest_file.write_text(data=json.dumps(obj=anki_addon_manifest_default_data))
    anki_addon_meta_file.write_text(data=json.dumps(obj=anki_addon_meta_default_data))

    argv = [
        "",
        "--base", str(anki_base_folder),
        "--profile", anki_profile_name,
        "--lang", "en",
    ]
    app = aqt._run(argv=argv, exec=False)
    aqt.mw.setupProfile()
    yield app
    app.quit()


@pytest.fixture(scope="session")
def anki_test_app(aqt_run: aqt.AnkiApp, addon_metadata: addon_metadata_module.AddonMetadata) -> AnkiTestApp:
    test_app = AnkiTestApp(metadata=addon_metadata)
    return test_app


@pytest.fixture(scope="session")
def anki_app(anki_test_app: AnkiApp) -> AnkiApp:
    return anki_test_app


@pytest.fixture(scope="session")
def addon_config(anki_app: AnkiApp) -> AddonConfig:
    return AddonConfig(anki_app=anki_app)


@pytest.fixture()
def anki_setup_and_teardown(
    tmp_path: Path,
    anki_base_folder: Path,
    anki_logs_folder: Path,
    anki_addon_manifest_file: Path,
    anki_addon_manifest_default_data: Dict,
    anki_addon_meta_file: Path,
    anki_addon_meta_default_data: Dict,
    anki_test_app: AnkiTestApp,
    addon_metadata: addon_metadata_module.AddonMetadata,
):
    anki_test_app.setup_performed = True

    addon_metadata_module.ADD_ON_METADATA_PATH = tmp_path / addon_metadata_module.ADD_ON_METADATA_PATH.name
    shutil.rmtree(anki_logs_folder)
    anki_logs_folder.mkdir()
    anki_addon_manifest_file.write_text(data=json.dumps(obj=anki_addon_manifest_default_data))
    anki_addon_meta_file.write_text(data=json.dumps(obj=anki_addon_meta_default_data))

    models_backup = anki_test_app.get_all_models()

    addon_metadata._last_sync_timestamp = 0

    yield

    anki_test_app.remove_all_notes()
    anki_test_app.remove_all_attachments()
    anki_test_app.remove_all_note_models()
    anki_test_app.add_backed_up_note_models(models=models_backup)
    if addon_metadata_module.ADD_ON_METADATA_PATH.exists():
        addon_metadata_module.ADD_ON_METADATA_PATH.unlink()

    anki_test_app.setup_performed = False


# ================== OBSIDIAN ==========================================================


@pytest.fixture(scope="session")
def addon_metadata() -> addon_metadata_module.AddonMetadata:
    def commit_sync(self):
        self._last_sync_timestamp = int(time.time())
        self._save()

    addon_metadata_module.AddonMetadata.commit_sync = commit_sync
    metadata = addon_metadata_module.AddonMetadata()
    metadata._sync_started = True

    return metadata


@pytest.fixture(scope="session")
def obsidian_config(addon_config: AddonConfig) -> ObsidianConfig:
    return ObsidianConfig(addon_config=addon_config)


@pytest.fixture(scope="session")
def obsidian_vault(addon_config, obsidian_config) -> ObsidianVault:
    return ObsidianVault(
        addon_config=addon_config,
        obsidian_config=obsidian_config,
    )


@pytest.fixture(scope="session")
def obsidian_template_field_factory(addon_config: AddonConfig) -> ObsidianTemplateFieldFactory:
    return ObsidianTemplateFieldFactory(addon_config=addon_config)


@pytest.fixture()
def obsidian_templates_manager(
    anki_app: AnkiApp,
    obsidian_config: ObsidianConfig,
    obsidian_vault: ObsidianVault,
    addon_config: AddonConfig,
) -> ObsidianTemplatesManager:
    return ObsidianTemplatesManager(
        anki_app=anki_app,
        obsidian_config=obsidian_config,
        obsidian_vault=obsidian_vault,
        addon_config=addon_config,
    )


@pytest.fixture(scope="session")
def obsidian_references_manager(addon_config: AddonConfig, obsidian_config: ObsidianConfig) -> ObsidianReferencesManager:
    return ObsidianReferencesManager(addon_config=addon_config, obsidian_config=obsidian_config)


@pytest.fixture(scope="session")
def obsidian_reference_factory(obsidian_references_manager: ObsidianReferencesManager) -> ObsidianReferenceFactory:
    return ObsidianReferenceFactory(obsidian_references_manager=obsidian_references_manager)


@pytest.fixture(scope="session")
def obsidian_note_field_factory(
    addon_config: AddonConfig, obsidian_reference_factory: ObsidianReferenceFactory
) -> ObsidianNoteFieldFactory:
    return ObsidianNoteFieldFactory(addon_config=addon_config, references_factory=obsidian_reference_factory)


@pytest.fixture()
def obsidian_notes_manager(
    anki_app: AnkiApp,
    addon_config: AddonConfig,
    obsidian_config: ObsidianConfig,
    obsidian_vault: ObsidianVault,
    addon_metadata: AddonMetadata,
) -> ObsidianNotesManager:
    return ObsidianNotesManager(
        anki_app=anki_app,
        addon_config=addon_config,
        obsidian_config=obsidian_config,
        obsidian_vault=obsidian_vault,
        metadata=addon_metadata,
    )


@pytest.fixture()
def obsidian_setup_and_teardown(
    srs_folder_in_obsidian: Path,
    obsidian_templates_folder: Path,
    srs_attachments_in_obsidian_folder: Path,
    obsidian_config: ObsidianConfig,
    obsidian_settings_folder: Path,
    addon_metadata: addon_metadata_module.AddonMetadata,
):
    if srs_folder_in_obsidian.exists():
        shutil.rmtree(srs_folder_in_obsidian)
    if obsidian_templates_folder.exists():
        shutil.rmtree(obsidian_templates_folder)
    if srs_attachments_in_obsidian_folder.exists():
        shutil.rmtree(srs_attachments_in_obsidian_folder)

    settings = {
        OBSIDIAN_TEMPLATES_OPTION_KEY: True,
        OBSIDIAN_TRASH_OPTION_KEY: OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE,
        OBSIDIAN_USE_MARKDOWN_LINKS_OPTION_KEY: True,
    }
    with open(file=obsidian_settings_folder / OBSIDIAN_APP_SETTINGS_FILE, mode="w") as f:
        json.dump(settings, f)

    template_settings = {
        TEMPLATES_FOLDER_JSON_FIELD_NAME: obsidian_templates_folder.name,
    }
    with open(file=obsidian_settings_folder / OBSIDIAN_TEMPLATES_SETTINGS_FILE, mode="w") as f:
        json.dump(template_settings, f)

    addon_metadata._last_sync_timestamp = 0

    yield


# ================== OTHER =============================================================


@pytest.fixture()
def templates_synchronizer(
    anki_app, obsidian_config, addon_config
) -> TemplatesSynchronizer:
    return TemplatesSynchronizer(
        anki_app=anki_app,
        obsidian_config=obsidian_config,
        addon_config=addon_config,
    )


@pytest.fixture()
def notes_synchronizer(
    anki_app, obsidian_config, addon_config: AddonConfig, addon_metadata: addon_metadata_module.AddonMetadata
) -> NotesSynchronizer:
    return NotesSynchronizer(
        anki_app=anki_app,
        obsidian_config=obsidian_config,
        addon_config=addon_config,
        metadata=addon_metadata,
    )
