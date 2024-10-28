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
from string import ascii_letters, digits

from ..addon_config import AddonConfig
from ..constants import SRS_NOTE_FIELD_IDENTIFIER_COMMENT, SRS_NOTE_IDENTIFIER_PROPERTY_NAME
from .obsidian_config import ObsidianConfig


class ObsidianFileFormatter:  # todo: delete
    def __init__(
        self,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
    ):
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config

    @staticmethod
    def clean_string_for_file_name(string: str) -> str:
        cloze_pattern = r"\{\{c\d+::(.*?)\}\}"
        string = re.sub(cloze_pattern, r"\1", string)  # remove cloze markers
        valid_chars = "-_.() %s%s" % (ascii_letters, digits)
        return "".join(c for c in string if c in valid_chars)
