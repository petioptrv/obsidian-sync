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
from abc import abstractmethod
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from typing import Optional, List

import yaml
from obsidian_sync.base_types.content import NoteProperties, TemplateProperties
from obsidian_sync.constants import DATETIME_FORMAT, MODEL_ID_PROPERTY_NAME, MODEL_NAME_PROPERTY_NAME, \
    NOTE_ID_PROPERTY_NAME, TAGS_PROPERTY_NAME, DATE_MODIFIED_PROPERTY_NAME, DATE_SYNCED_PROPERTY_NAME, \
    SUSPENDED_PROPERTY_NAME, MAXIMUM_CARD_DIFFICULTY_PROPERTY_NAME, DEFAULT_NOTE_MAXIMUM_CARD_DIFFICULTY_FOR_NEW_NOTES, \
    DEFAULT_NOTE_ID_FOR_NEW_NOTES, DEFAULT_NOTE_SUSPENDED_STATE_FOR_NEW_NOTES


@dataclass
class ObsidianProperties(NoteProperties):
    date_synced: Optional[datetime]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, type(self))
            and super().__eq__(other)
            and self.date_synced == other.date_synced
        )

    @classmethod
    def from_obsidian_file_text(cls, file_text: str) -> "ObsidianProperties":
        properties_pattern = r"^---\s*([\s\S]*?)\s*---"

        match = re.search(properties_pattern, file_text)

        properties_text = match.group(1).strip()
        properties_dict = yaml.safe_load(stream=properties_text)

        properties = cls._properties_from_dict(properties_dict=properties_dict)

        return properties

    @abstractmethod
    def to_obsidian_file_text(self) -> str:
        ...

    @classmethod
    @abstractmethod
    def _properties_from_dict(cls, properties_dict: dict) -> "ObsidianProperties":
        ...


@dataclass
class ObsidianTemplateProperties(ObsidianProperties):
    note_id: int = dataclass_field(default=DEFAULT_NOTE_ID_FOR_NEW_NOTES)
    tags: List[str] = dataclass_field(default_factory=list)
    suspended: bool = dataclass_field(default=DEFAULT_NOTE_SUSPENDED_STATE_FOR_NEW_NOTES)
    maximum_card_difficulty: float = dataclass_field(default=DEFAULT_NOTE_MAXIMUM_CARD_DIFFICULTY_FOR_NEW_NOTES)
    date_modified_in_anki: Optional[datetime] = dataclass_field(default=None)
    date_synced: Optional[datetime] = dataclass_field(default=None)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_properties(cls, properties: TemplateProperties) -> "ObsidianTemplateProperties":
        return cls(
            model_id=properties.model_id,
            model_name=properties.model_name,
        )

    def to_obsidian_file_text(self) -> str:
        date_modified_in_anki = (
            self.date_modified_in_anki.strftime(DATETIME_FORMAT)
            if self.date_modified_in_anki is not None
            else self.date_modified_in_anki
        )
        date_synced = (
            self.date_synced.strftime(DATETIME_FORMAT)
            if self.date_synced is not None
            else self.date_synced
        )
        properties_dict = {
            MODEL_ID_PROPERTY_NAME: self.model_id,
            MODEL_NAME_PROPERTY_NAME: self.model_name,
            NOTE_ID_PROPERTY_NAME: self.note_id,
            TAGS_PROPERTY_NAME: self.tags,
            SUSPENDED_PROPERTY_NAME: self.suspended,
            MAXIMUM_CARD_DIFFICULTY_PROPERTY_NAME: self.maximum_card_difficulty,
            DATE_MODIFIED_PROPERTY_NAME: date_modified_in_anki,
            DATE_SYNCED_PROPERTY_NAME: date_synced,
        }
        return (
            f"---\n"
            f"{yaml.safe_dump(data=properties_dict, sort_keys=False)}"
            f"---\n"
        )

    @classmethod
    def _properties_from_dict(cls, properties_dict: dict) -> "ObsidianTemplateProperties":
        properties = cls(
            model_id=int(properties_dict[MODEL_ID_PROPERTY_NAME]),
            model_name=properties_dict[MODEL_NAME_PROPERTY_NAME],
            note_id=properties_dict[NOTE_ID_PROPERTY_NAME],
            tags=properties_dict[TAGS_PROPERTY_NAME],
            suspended=properties_dict[SUSPENDED_PROPERTY_NAME],
            maximum_card_difficulty=properties_dict[MAXIMUM_CARD_DIFFICULTY_PROPERTY_NAME],
            date_modified_in_anki=properties_dict[DATE_MODIFIED_PROPERTY_NAME],
            date_synced=properties_dict[DATE_SYNCED_PROPERTY_NAME],
        )
        return properties


@dataclass
class ObsidianNoteProperties(ObsidianProperties):
    note_id: int
    tags: List[str]
    date_modified_in_anki: Optional[datetime]
    date_synced: Optional[datetime]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_properties(cls, properties: NoteProperties):
        date_synced = datetime.now() if not isinstance(properties, ObsidianNoteProperties) else properties.date_synced
        return cls(
            model_id=properties.model_id,
            model_name=properties.model_name,
            note_id=properties.note_id,
            tags=properties.tags,
            suspended=properties.suspended,
            maximum_card_difficulty=properties.maximum_card_difficulty,
            date_modified_in_anki=properties.date_modified_in_anki,
            date_synced=date_synced,
        )

    def to_obsidian_file_text(self) -> str:
        date_modified_in_anki = (
            self.date_modified_in_anki.strftime(DATETIME_FORMAT)
            if self.date_modified_in_anki is not None
            else self.date_modified_in_anki
        )
        date_synced = (
            self.date_synced.strftime(DATETIME_FORMAT)
            if self.date_synced is not None
            else self.date_synced
        )
        properties_dict = {
            MODEL_ID_PROPERTY_NAME: self.model_id,
            MODEL_NAME_PROPERTY_NAME: self.model_name,
            NOTE_ID_PROPERTY_NAME: self.note_id,
            TAGS_PROPERTY_NAME: self.tags,
            SUSPENDED_PROPERTY_NAME: self.suspended,
            MAXIMUM_CARD_DIFFICULTY_PROPERTY_NAME: self.maximum_card_difficulty,
            DATE_MODIFIED_PROPERTY_NAME: date_modified_in_anki,
            DATE_SYNCED_PROPERTY_NAME: date_synced,
        }
        return (
            f"---\n"
            f"{yaml.safe_dump(data=properties_dict, sort_keys=False)}"
            f"---\n"
        )

    @classmethod
    def _properties_from_dict(cls, properties_dict: dict) -> "ObsidianNoteProperties":
        date_modified_in_anki_value = properties_dict[DATE_MODIFIED_PROPERTY_NAME]
        date_modified_in_anki = (
            datetime.strptime(date_modified_in_anki_value, DATETIME_FORMAT)
            if isinstance(date_modified_in_anki_value, str)
            else date_modified_in_anki_value
        )
        date_synced_value = properties_dict[DATE_SYNCED_PROPERTY_NAME]
        date_synced = (
            datetime.strptime(date_synced_value, DATETIME_FORMAT)
            if isinstance(date_synced_value, str)
            else date_synced_value
        )
        properties = cls(
            note_id=int(properties_dict[NOTE_ID_PROPERTY_NAME]),
            model_name=properties_dict[MODEL_NAME_PROPERTY_NAME],
            model_id=int(properties_dict[MODEL_ID_PROPERTY_NAME]),
            tags=properties_dict[TAGS_PROPERTY_NAME],
            suspended=properties_dict[SUSPENDED_PROPERTY_NAME],
            maximum_card_difficulty=properties_dict[MAXIMUM_CARD_DIFFICULTY_PROPERTY_NAME],
            date_modified_in_anki=date_modified_in_anki,
            date_synced=date_synced,
        )
        return properties
