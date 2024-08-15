from abc import ABC, abstractmethod

from aqt.utils import showCritical

from .constants import ADD_ON_NAME
from .config_handler import ConfigHandler


class ChangeLogBase(ABC):
    @classmethod
    def build_log(cls, config_handler: ConfigHandler) -> "ChangeLogBase":
        return ChangeLog()

    @abstractmethod
    def display_changes(self):
        ...

    @abstractmethod
    def log_change(self, change: str):
        ...


class PassThroughChangeLog(ChangeLogBase):
    def log_change(self, change: str):
        pass

    def display_changes(self):
        pass


class ChangeLog(ChangeLogBase):
    def __init__(self):
        self._change_log = []

    def log_change(self, change: str):
        self._change_log.append(change)

    def display_changes(self):
        text = "Change log:\n\n" + "\n\n".join(self._change_log)
        showCritical(text=text, title=ADD_ON_NAME)
