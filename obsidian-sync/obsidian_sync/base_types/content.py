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
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Content:
    properties: "Properties"
    fields: List["Field"]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, type(self))
            and self.properties == other.properties
            and len(self.fields) == len(other.fields)
            and all(sf == of for sf, of in zip(self.fields, other.fields))
        )


@dataclass
class Properties:
    model_id: int


@dataclass
class Field(ABC):
    name: str
    text: str
    images: List["Image"]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Field)
            and self.name == other.name
            and self.text == other.text
            and len(self.images) == len(other.images)
            and all(si == oi for si, oi in zip(self.images, other.images))
        )

    @abstractmethod
    def to_markdown(self) -> str:
        ...

    @abstractmethod
    def to_html(self) -> str:
        ...


@dataclass
class LinkedResource(ABC):
    path: Path

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.path == other.path


@dataclass
class Image(LinkedResource):
    pass


@dataclass
class Video(LinkedResource):
    pass


@dataclass
class Audio(LinkedResource):
    pass
