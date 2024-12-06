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
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class Content(ABC):
    properties: "Properties"
    fields: List["Field"]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Content)
            and self.properties == other.properties
            and len(self.fields) == len(other.fields)
            and all(sf == of for sf, of in zip(self.fields, other.fields))
        )


@dataclass
class TemplateContent(Content):
    properties: "TemplateProperties"
    fields: List["TemplateField"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class NoteContent(Content):
    properties: "NoteProperties"
    fields: List["NoteField"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class Properties:
    model_id: int
    model_name: str

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Properties)
            and self.model_id == other.model_id
            and self.model_name == other.model_name
        )


@dataclass
class TemplateProperties(Properties):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class NoteProperties(Properties):
    note_id: int
    tags: List[str]
    date_modified_in_anki: Optional[datetime]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, NoteProperties)
            and super().__eq__(other)
            and self.note_id == other.note_id
            and self.tags == other.tags
            and self.date_modified_in_anki == other.date_modified_in_anki
        )


@dataclass
class Field(ABC):
    name: str
    text: str

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Field)
            and self.name == other.name
            and self.text == other.text
        )

    @abstractmethod
    def set_from_markdown(self, markdown: str):
        ...

    @abstractmethod
    def set_from_html(self, html: str):
        ...

    @abstractmethod
    def to_markdown(self) -> str:
        ...

    @abstractmethod
    def to_html(self) -> str:
        ...


@dataclass
class TemplateField(Field, ABC):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class NoteField(Field, ABC):
    references: List["Reference"]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, NoteField)
            and super().__eq__(other)
            and len(self.references) == len(other.references)
            and all(sa == oa for sa, oa in zip(self.references, other.references))
        )


@dataclass
class Reference(ABC):
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, type(self))
            and self.to_field_text() == other.to_field_text()
        )

    @abstractmethod
    def to_field_text(self) -> str:
        ...


@dataclass
class MediaReference(Reference, ABC):
    path: Path

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, type(self))
            and super().__eq__(other)
            and self.path == other.path
        )

    def to_field_text(self) -> str:
        return str(self.path)


@dataclass
class ObsidianURLReference(Reference, ABC):
    url: str

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, type(self))
            and super().__eq__(other)
            and self.url == other.url
        )

    def to_field_text(self) -> str:
        return self.url
