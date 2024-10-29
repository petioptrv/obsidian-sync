# -*- coding: utf-8 -*-
# Obsidian Sync Add-on for Anki
#
# Copyright (C)  2024 Petrov P.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <mailto:petioptrv@icloud.com>.
#
# Any modifications to this file must keep this entire header intact.
from abc import ABC, abstractmethod

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
