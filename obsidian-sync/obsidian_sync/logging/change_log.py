from abc import ABC, abstractmethod

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.anki.anki_app import AnkiApp
from obsidian_sync.logging.change_log_messages import ChangeLogMessage
from obsidian_sync.constants import ADD_ON_NAME


class ChangeLogBase(ABC):
    def __init__(self, anki_app: AnkiApp):
        self._anki_app = anki_app

    @abstractmethod
    def display_changes(self):
        ...

    @abstractmethod
    def log_change(self, change: ChangeLogMessage):
        ...


class PassThroughChangeLog(ChangeLogBase):
    def log_change(self, change: ChangeLogMessage):
        pass

    def display_changes(self):
        pass


class ChangeLog(ChangeLogBase):
    def __init__(self, anki_app: AnkiApp):
        super().__init__(anki_app=anki_app)
        self._change_log = []

    def log_change(self, change: ChangeLogMessage):
        self._change_log.append(change)

    def display_changes(self):
        text = "Change log:\n\n" + "\n\n".join(self._change_log)
        self._anki_app.show_critical(text=text, title=ADD_ON_NAME)
