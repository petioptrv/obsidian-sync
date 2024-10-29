import random
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image as PILImage, ImageDraw

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.anki.anki_app import AnkiApp
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.synchronizers.media_synchronizer import MediaSynchronizer
from obsidian_sync.synchronizers.templates_synchronizer import TemplatesSynchronizer
from tests.anki_mock import AnkiMocker


@pytest.fixture()
def some_test_image() -> PILImage:
    image = PILImage.new(mode="RGB", size=(1, 1))
    return image


@pytest.fixture()
def second_test_image() -> PILImage:
    image = PILImage.new(mode="RGB", size=(2, 2))
    return image


@pytest.fixture()
@patch("obsidian_sync.addon_config.AddonConfig")
def addon_config_mock(addon_config_: MagicMock) -> AddonConfig:
    return addon_config_


@pytest.fixture()
@patch("obsidian_sync.obsidian.obsidian_config.ObsidianConfig")
def obsidian_config_mock(obsidian_config_: MagicMock) -> ObsidianConfig:
    return obsidian_config_


@pytest.fixture()
def srs_folder_in_obsidian_mock(obsidian_config_mock: MagicMock, tmp_path) -> Path:
    srs_folder = tmp_path / "srs-in-obsidian"
    obsidian_config_mock.srs_folder = srs_folder
    return srs_folder


@pytest.fixture()
def obsidian_templates_folder_mock(obsidian_config_mock: MagicMock, srs_folder_in_obsidian_mock: Path) -> Path:
    templates_folder = srs_folder_in_obsidian_mock / "templates"
    obsidian_config_mock.templates_folder = templates_folder
    return templates_folder


@pytest.fixture()
def srs_attachments_in_obsidian_folder_mock(
    obsidian_config_mock: MagicMock, srs_folder_in_obsidian_mock: Path
) -> Path:
    srs_attachments_in_obsidian_folder = srs_folder_in_obsidian_mock / "srs-attachments"
    obsidian_config_mock.srs_attachments_folder = srs_attachments_in_obsidian_folder
    return srs_attachments_in_obsidian_folder


@pytest.fixture()
def anki_mocker() -> AnkiMocker:
    mocker = AnkiMocker()
    return mocker


@pytest.fixture()
def anki_app() -> AnkiApp:
    return AnkiApp()


@pytest.fixture()
def markup_translator() -> MarkupTranslator:
    return MarkupTranslator()


@pytest.fixture()
def obsidian_vault(anki_app, addon_config_mock, obsidian_config_mock, markup_translator) -> ObsidianVault:
    return ObsidianVault(
        anki_app=anki_app,
        addon_config=addon_config_mock,
        obsidian_config=obsidian_config_mock,
        markup_translator=markup_translator,
    )


@pytest.fixture()
def media_synchronizer(
    anki_app,
    obsidian_vault,
) -> MediaSynchronizer:
    return MediaSynchronizer(
        anki_app=anki_app,
        obsidian_vault=obsidian_vault,
    )


@pytest.fixture()
def templates_synchronizer(
    anki_app, obsidian_vault, obsidian_config_mock, addon_config_mock, markup_translator
) -> TemplatesSynchronizer:
    return TemplatesSynchronizer(
        anki_app=anki_app,
        obsidian_vault=obsidian_vault,
        obsidian_config=obsidian_config_mock,
        addon_config=addon_config_mock,
        markup_translator=markup_translator,
    )
