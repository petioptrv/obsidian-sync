from dataclasses import field
from pathlib import Path
from typing import List
from unittest.mock import patch

from attr import dataclass, asdict


@dataclass
class MockAnkiField:
    name: str


@dataclass
class MockAnkiTemplate:
    id: int
    name: str
    flds: [MockAnkiField] = field(default_factory=list)


class AnkiMocker:
    def __init__(self):
        self._mw_patcher = patch("obsidian_sync.anki.anki_app.mw")
        self._mw_mock = self._mw_patcher.start()
        self._tooltip_patcher = patch("obsidian_sync.anki.anki_app.tooltip")
        self._tooltip_mock = self._tooltip_patcher.start()
        self._media_files_patcher = patch("obsidian_sync.anki.anki_app.AnkiApp.get_all_media_files")
        self._media_files_mock = self._media_files_patcher.start()

        self._added_media_files = []

        self._mw_mock.col.media.add_file.side_effect = self._add_file

    def __del__(self):
        self._mw_patcher.stop()
        self._tooltip_patcher.stop()
        self._media_files_patcher.stop()

    def set_mock_templates(self, mock_templates: [MockAnkiTemplate]):
        self._mw_mock.col.models.all.return_value = [
            asdict(mock_template) for mock_template in mock_templates
        ]

    def set_media_files(self, files: List[Path]):
        self._media_files_mock.return_value = [
            f for f in files
        ]

    def get_added_media_files(self):
        return self._added_media_files

    def _add_file(self, path: Path):
        self._added_media_files.append(path)
