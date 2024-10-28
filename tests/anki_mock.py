from dataclasses import field
from unittest.mock import patch, MagicMock

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

    def __del__(self):
        self._mw_patcher.stop()
        self._tooltip_patcher.stop()

    def add_mock_templates(self, mock_templates: [MockAnkiTemplate]):
        self._mw_mock.col.models.all.return_value = [
            asdict(mock_template) for mock_template in mock_templates
        ]
