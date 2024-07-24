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
import re

from .constants import TEMPLATE_PROPERTY_NAME
from .config_handler import ConfigHandler


class ObsidianNoteFinder:
    def __init__(self, config_handler: ConfigHandler):
        self._config_handler = config_handler

    def is_anki_note_in_obsidian(self, note_content: str) -> bool:
        property_value = self._config_handler.anki_note_in_obsidian_property_value
        pattern = (
            rf"^---\s*(?:.*\n)*?{re.escape(TEMPLATE_PROPERTY_NAME)}\s*:\s*{re.escape(property_value)}\s*(?:.*\n)*?---"
        )
        return re.match(pattern, note_content) is not None
