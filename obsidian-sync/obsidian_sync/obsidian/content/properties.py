import re
from abc import abstractmethod
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from typing import Optional, List

import yaml
from obsidian_sync.base_types.content import NoteProperties, TemplateProperties
from obsidian_sync.constants import DATETIME_FORMAT, MODEL_ID_PROPERTY_NAME, MODEL_NAME_PROPERTY_NAME, \
    NOTE_ID_PROPERTY_NAME, TAGS_PROPERTY_NAME, DATE_MODIFIED_PROPERTY_NAME, DATE_SYNCED_PROPERTY_NAME, \
    SUSPENDED_PROPERTY_NAME, MAXIMUM_CARD_DIFFICULTY_PROPERTY_NAME


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
    note_id: int = dataclass_field(default=0)
    tags: List[str] = dataclass_field(default_factory=list)
    suspended: bool = dataclass_field(default=False)
    maximum_card_difficulty: float = dataclass_field(default=0.0)
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
        return cls(
            model_id=properties.model_id,
            model_name=properties.model_name,
            note_id=properties.note_id,
            tags=properties.tags,
            suspended=properties.suspended,
            maximum_card_difficulty=properties.maximum_card_difficulty,
            date_modified_in_anki=properties.date_modified_in_anki,
            date_synced=datetime.now(),
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
            if date_modified_in_anki_value is not None
            else date_modified_in_anki_value
        )
        date_synced_value = properties_dict[DATE_SYNCED_PROPERTY_NAME]
        date_synced = datetime.strptime(date_synced_value, DATETIME_FORMAT) if date_synced_value else None
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
