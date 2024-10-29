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
from abc import ABC, abstractmethod
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

import yaml

from obsidian_sync.constants import SRS_NOTE_FIELD_IDENTIFIER_COMMENT, IMAGE_FILE_EXTENSIONS, SRS_NOTE_IDENTIFIER_COMMENT, \
    MODEL_ID_PROPERTY_NAME, NOTE_ID_PROPERTY_NAME, TAGS_PROPERTY_NAME, DATE_MODIFIED_PROPERTY_NAME, \
    SRS_HEADER_TITLE_LEVEL, DATETIME_FORMAT, TEMPLATE_TIME_FORMAT, TEMPLATE_DATE_FORMAT, DATE_SYNCED_PROPERTY_NAME
from obsidian_sync.base_types.content import Image, Content, Field, Properties
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.base_types.template import Template


@dataclass
class ObsidianContent(ABC, Content):
    properties: "ObsidianProperties"
    fields: List["ObsidianField"]

    @classmethod
    def from_obsidian_file_text(cls, file_text: str, markup_translator: MarkupTranslator) -> "ObsidianContent":
        properties = cls._properties_from_obsidian_file_text(file_text=file_text)
        fields = ObsidianField.from_obsidian_file_text(
            file_text=file_text, markup_translator=markup_translator
        )
        content = cls(fields=fields, properties=properties)
        return content

    def to_obsidian_file_text(self) -> str:
        file_text = self.properties.to_obsidian_file_text()
        file_text += f"{SRS_NOTE_IDENTIFIER_COMMENT}\n"

        for field in self.fields:
            file_text += field.to_obsidian_file_text()

        return file_text

    @classmethod
    @abstractmethod
    def _properties_from_obsidian_file_text(cls, file_text: str) -> "ObsidianProperties":
        ...


@dataclass
class ObsidianTemplateContent(ObsidianContent):
    properties: "ObsidianTemplateProperties"

    @classmethod
    def from_template(
        cls, template: Template,
        obsidian_config: ObsidianConfig,
        markup_translator: MarkupTranslator,
    ):
        properties = ObsidianTemplateProperties.from_template(template=template)
        fields = [
            ObsidianField.from_field(
                field=anki_field, markup_translator=markup_translator, obsidian_config=obsidian_config
            )
            for anki_field in template.content.fields
        ]
        return cls(properties=properties, fields=fields)

    @classmethod
    def _properties_from_obsidian_file_text(cls, file_text: str) -> "ObsidianTemplateProperties":
        return ObsidianTemplateProperties.from_obsidian_file_text(file_text=file_text)


@dataclass
class ObsidianNoteContent(ObsidianContent):
    properties: "ObsidianNoteProperties"

    @classmethod
    def _properties_from_obsidian_file_text(cls, file_text: str) -> "ObsidianNoteProperties":
        return ObsidianNoteProperties.from_obsidian_file_text(file_text=file_text)


@dataclass
class ObsidianProperties(Properties):
    note_id: int
    tags: List[str]
    date_modified: Union[str, datetime]
    date_synced: Optional[datetime]

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
    date_modified: str = dataclass_field(default=f"\"{{{{date:{TEMPLATE_DATE_FORMAT} {TEMPLATE_TIME_FORMAT}}}}}\"")
    date_synced: Optional[datetime] = dataclass_field(default=None)

    @classmethod
    def from_template(cls, template: Template) -> "ObsidianTemplateProperties":
        return cls(model_id=template.content.properties.model_id)

    def to_obsidian_file_text(self) -> str:
        properties_dict = {
            MODEL_ID_PROPERTY_NAME: self.model_id,
            NOTE_ID_PROPERTY_NAME: self.note_id,
            TAGS_PROPERTY_NAME: self.tags,
            DATE_MODIFIED_PROPERTY_NAME: self.date_modified,
            DATE_SYNCED_PROPERTY_NAME: self.date_synced,
        }
        return (
            f"---\n"
            f"{yaml.safe_dump(data=properties_dict, sort_keys=False)}\n"
            f"---\n"
        )

    @classmethod
    def _properties_from_dict(cls, properties_dict: dict) -> "ObsidianTemplateProperties":
        properties = cls(
            model_id=int(properties_dict[MODEL_ID_PROPERTY_NAME]),
        )
        return properties


@dataclass
class ObsidianNoteProperties(ObsidianProperties):
    note_id: int
    tags: List[str]
    date_modified: datetime
    date_synced: Optional[datetime]

    def to_obsidian_file_text(self) -> str:
        properties_dict = {
            MODEL_ID_PROPERTY_NAME: self.model_id,
            NOTE_ID_PROPERTY_NAME: self.note_id,
            TAGS_PROPERTY_NAME: self.tags,
            DATE_MODIFIED_PROPERTY_NAME: self.date_modified.strftime(DATETIME_FORMAT),
            DATE_SYNCED_PROPERTY_NAME: self.date_synced.strftime(DATETIME_FORMAT) if self.date_synced else None,
        }
        return (
            f"---\n"
            f"{yaml.safe_dump(data=properties_dict, sort_keys=False)}\n"
            f"---\n"
        )

    @classmethod
    def _properties_from_dict(cls, properties_dict: dict) -> "ObsidianNoteProperties":
        date_synced_value = properties_dict[DATE_SYNCED_PROPERTY_NAME]
        properties = cls(
            note_id=int(properties_dict[NOTE_ID_PROPERTY_NAME]),
            model_id=int(properties_dict[MODEL_ID_PROPERTY_NAME]),
            tags=properties_dict[TAGS_PROPERTY_NAME],
            date_modified=datetime.strptime(properties_dict[DATE_MODIFIED_PROPERTY_NAME], DATETIME_FORMAT),
            date_synced=datetime.strptime(date_synced_value, DATETIME_FORMAT) if date_synced_value else None,
        )
        return properties


@dataclass
class ObsidianField(Field):
    _markup_translator: MarkupTranslator

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, type(self))
            and self.name == other.name
            and self.text == other.text
            and len(self.images) == len(other.images)
            and all(si == oi for si, oi in zip(self.images, other.images))
        )

    @classmethod
    def from_obsidian_file_text(cls, file_text: str, markup_translator: MarkupTranslator) -> List["ObsidianField"]:
        headers_and_paragraph_matching_pattern = (
            f"{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}\n{SRS_HEADER_TITLE_LEVEL} (.*?)\n"
            f"([\s\S]*?)(?={SRS_NOTE_FIELD_IDENTIFIER_COMMENT}|\Z)"
        )

        note_body = cls._get_note_body(file_text=file_text)
        matches = re.findall(
            headers_and_paragraph_matching_pattern,
            f"{note_body}\n",  # ensures the matching string works even if file ends at field title
            re.DOTALL,
        )
        result = []

        for header, paragraph in matches:
            text = paragraph.strip()
            images = ObsidianImage.from_obsidian_file_text(file_text=text)
            result.append(
                ObsidianField(name=header.strip(), text=text, images=images, _markup_translator=markup_translator)
            )

        return result

    @classmethod
    def from_field(
        cls, field: Field, markup_translator: MarkupTranslator, obsidian_config: ObsidianConfig
    ) -> "ObsidianField":
        obsidian_images = [
            ObsidianImage.from_image(image=image, obsidian_config=obsidian_config)
            for image in field.images
        ]
        markdown_text = markup_translator.translate_html_to_markdown(html=field.text)
        return cls(
            name=field.name, text=markdown_text, images=obsidian_images, _markup_translator=markup_translator
        )

    def to_obsidian_file_text(self) -> str:
        field_title = self._build_field_title()
        field_text = f"{field_title}\n{self.text}\n\n"
        return field_text

    def to_markdown(self) -> str:
        return self.text

    def to_html(self) -> str:
        raise NotImplementedError

    @staticmethod
    def _get_note_body(file_text: str) -> str:
        yaml_frontmatter_pattern = r"^---[\s\S]*?---\s*"
        note_body = re.sub(yaml_frontmatter_pattern, "", file_text, count=1)
        return note_body

    def _build_field_title(self) -> str:
        field_format_string = f"{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}\n{SRS_HEADER_TITLE_LEVEL} {self.name}"
        return field_format_string


@dataclass
class ObsidianImage(Image):
    def __eq__(self, other):
        return isinstance(other, type(self)) and self.path == other.path

    @classmethod
    def from_obsidian_file_text(cls, file_text: str) -> List["ObsidianImage"]:
        image_paths = cls._markdown_image_paths_from_file_text(file_text=file_text)
        images = [ObsidianImage(path=Path(path)) for path in image_paths]
        return images

    @classmethod
    def from_image(cls, image: Image, obsidian_config: ObsidianConfig) -> "ObsidianImage":
        image_path = obsidian_config.srs_attachments_folder / image.path.name
        return cls(path=image_path)

    @staticmethod
    def _markdown_image_paths_from_file_text(file_text: str) -> List[str]:
        # source: https://stackoverflow.com/a/44227600/6793798
        extensions_matcher = "|".join(IMAGE_FILE_EXTENSIONS)
        markdown_image_pattern = rf"""!?\[[^\]]*\]\((.*?\.(?:{extensions_matcher}))\s*("(?:.*[^"])")?\s*\)"""
        image_paths = [
            path
            for path, optional_part in
            re.findall(markdown_image_pattern, file_text, re.DOTALL)
        ]
        return image_paths
