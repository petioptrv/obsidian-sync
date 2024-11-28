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

from dataclasses import dataclass
from typing import List

from obsidian_sync.base_types.content import TemplateField
from obsidian_sync.constants import OBSIDIAN_LINK_URL_FIELD_NAME
from obsidian_sync.obsidian.content.field.field import ObsidianFieldFactory, ObsidianField


class ObsidianTemplateFieldFactory(ObsidianFieldFactory):
    @staticmethod
    def from_fields(fields: List[TemplateField]) -> List["ObsidianTemplateField"]:
        fields = [
            ObsidianTemplateField.from_field(field=field)
            if field.name != OBSIDIAN_LINK_URL_FIELD_NAME
            else ObsidianLinkURLTemplateField.from_field(field=field)
            for field in fields
        ]
        return fields

    def from_obsidian_file_text(self, file_text: str) -> List["ObsidianTemplateField"]:
        headers_and_paragraphs = self._get_headers_and_paragraphs_from_file_text(file_text=file_text)

        fields = [
            ObsidianTemplateField(name=header.strip(), text=paragraph.strip())
            for header, paragraph in headers_and_paragraphs
        ]

        if self._addon_config.add_obsidian_url_in_anki:
            fields.append(
                ObsidianLinkURLTemplateField(name=OBSIDIAN_LINK_URL_FIELD_NAME, text="")
            )

        return fields


@dataclass
class ObsidianTemplateField(TemplateField, ObsidianField):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_field(cls, field: TemplateField) -> "ObsidianTemplateField":
        markdown_text = field.to_markdown()
        return cls(name=field.name, text=markdown_text)

    def to_obsidian_file_text(self) -> str:
        field_title = self._build_field_title()
        field_text = f"{field_title}\n\n{self.text}\n\n"
        return field_text


@dataclass
class ObsidianLinkURLTemplateField(ObsidianTemplateField):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def to_obsidian_file_text(self) -> str:
        return ""
