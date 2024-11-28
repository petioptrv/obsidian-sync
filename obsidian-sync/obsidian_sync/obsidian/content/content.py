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
from dataclasses import dataclass
from pathlib import Path
from typing import List

from obsidian_sync.constants import SRS_NOTE_IDENTIFIER_COMMENT
from obsidian_sync.base_types.content import Content, NoteContent, \
    TemplateContent
from obsidian_sync.obsidian.content.field.field import ObsidianField
from obsidian_sync.obsidian.content.field.note_field import ObsidianNoteFieldFactory, ObsidianNoteField
from obsidian_sync.obsidian.content.field.template_field import ObsidianTemplateFieldFactory, ObsidianTemplateField
from obsidian_sync.obsidian.content.properties import ObsidianTemplateProperties, ObsidianNoteProperties, \
    ObsidianProperties
from obsidian_sync.obsidian.content.reference import ObsidianReferenceFactory


@dataclass
class ObsidianContent(Content, ABC):
    properties: ObsidianProperties
    fields: List[ObsidianField]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def to_obsidian_file_text(self) -> str:
        file_text = self.properties.to_obsidian_file_text()
        file_text += f"{SRS_NOTE_IDENTIFIER_COMMENT}\n"

        for field in self.fields:
            file_text += field.to_obsidian_file_text()

        return file_text

    @classmethod
    @abstractmethod
    def _properties_from_obsidian_file_text(cls, file_text: str) -> ObsidianProperties:
        ...


@dataclass
class ObsidianTemplateContent(ObsidianContent):
    properties: ObsidianTemplateProperties
    fields: List[ObsidianTemplateField]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_content(
        cls, content: TemplateContent, field_factory: ObsidianTemplateFieldFactory
    ) -> "ObsidianTemplateContent":
        properties = ObsidianTemplateProperties.from_properties(properties=content.properties)
        fields = field_factory.from_fields(fields=content.fields)
        return cls(properties=properties, fields=fields)

    @classmethod
    def from_obsidian_file_text(
        cls, file_text: str, field_factory: ObsidianTemplateFieldFactory
    ) -> "ObsidianTemplateContent":
        properties = cls._properties_from_obsidian_file_text(file_text=file_text)
        fields = field_factory.from_obsidian_file_text(file_text=file_text)
        content = cls(fields=fields, properties=properties)
        return content

    @classmethod
    def _properties_from_obsidian_file_text(cls, file_text: str) -> ObsidianTemplateProperties:
        return ObsidianTemplateProperties.from_obsidian_file_text(file_text=file_text)


@dataclass
class ObsidianNoteContent(ObsidianContent):
    properties: ObsidianNoteProperties
    fields: List[ObsidianNoteField]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_content(
        cls,
        content: NoteContent,
        obsidian_field_factory: ObsidianNoteFieldFactory,
        note_path: Path,
    ) -> "ObsidianNoteContent":
        properties = ObsidianNoteProperties.from_properties(properties=content.properties)
        fields = obsidian_field_factory.from_fields(fields=content.fields, note_path=note_path)
        return cls(properties=properties, fields=fields)

    @classmethod
    def from_obsidian_file_text(
        cls,
        file_text: str,
        note_path: Path,
        obsidian_field_factory: ObsidianNoteFieldFactory,
    ) -> "ObsidianNoteContent":
        properties = cls._properties_from_obsidian_file_text(file_text=file_text)
        fields = obsidian_field_factory.from_obsidian_file_text(
            file_text=file_text,
            note_path=note_path,
        )
        content = cls(fields=fields, properties=properties)
        return content

    @classmethod
    def _properties_from_obsidian_file_text(cls, file_text: str) -> ObsidianNoteProperties:
        return ObsidianNoteProperties.from_obsidian_file_text(file_text=file_text)
