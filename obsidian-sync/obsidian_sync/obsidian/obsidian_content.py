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
import urllib.parse
from abc import ABC, abstractmethod
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

from obsidian_sync.constants import SRS_NOTE_FIELD_IDENTIFIER_COMMENT, \
    SRS_NOTE_IDENTIFIER_COMMENT, \
    MODEL_ID_PROPERTY_NAME, NOTE_ID_PROPERTY_NAME, TAGS_PROPERTY_NAME, DATE_MODIFIED_PROPERTY_NAME, \
    SRS_HEADER_TITLE_LEVEL, DATETIME_FORMAT, DATE_SYNCED_PROPERTY_NAME, \
    MODEL_NAME_PROPERTY_NAME, SUSPENDED_PROPERTY_NAME, MAXIMUM_CARD_DIFFICULTY_PROPERTY_NAME
from obsidian_sync.base_types.content import Content, Field, LinkedAttachment, NoteProperties, NoteContent, \
    TemplateContent, TemplateProperties
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_attachments_manager import ObsidianAttachmentsManager


@dataclass
class ObsidianContent(Content, ABC):
    properties: "ObsidianProperties"
    fields: List["ObsidianField"]

    @classmethod
    def from_obsidian_file_text(
        cls,
        file_text: str,
        note_path: Path,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        markup_translator: MarkupTranslator,
    ) -> "ObsidianContent":
        properties = cls._properties_from_obsidian_file_text(file_text=file_text)
        fields = ObsidianField.from_obsidian_file_text(
            file_text=file_text,
            note_path=note_path,
            obsidian_attachments_manager=obsidian_attachments_manager,
            markup_translator=markup_translator,
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
    def from_content(
        cls,
        content: TemplateContent,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        markup_translator: MarkupTranslator,
        template_path: Path,
    ):
        properties = ObsidianTemplateProperties.from_properties(properties=content.properties)
        fields = ObsidianField.from_fields(
            fields=content.fields,
            markup_translator=markup_translator,
            obsidian_attachments_manager=obsidian_attachments_manager,
            note_path=template_path,
        )
        return cls(properties=properties, fields=fields)

    @classmethod
    def _properties_from_obsidian_file_text(cls, file_text: str) -> "ObsidianTemplateProperties":
        return ObsidianTemplateProperties.from_obsidian_file_text(file_text=file_text)


@dataclass
class ObsidianNoteContent(ObsidianContent):
    properties: "ObsidianNoteProperties"

    @classmethod
    def from_content(
        cls,
        content: NoteContent,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        markup_translator: MarkupTranslator,
        note_path: Path,
    ) -> "ObsidianNoteContent":
        properties = ObsidianNoteProperties.from_properties(properties=content.properties)
        fields = ObsidianField.from_fields(
            fields=content.fields,
            markup_translator=markup_translator,
            obsidian_attachments_manager=obsidian_attachments_manager,
            note_path=note_path,
        )
        return cls(properties=properties, fields=fields)

    @classmethod
    def _properties_from_obsidian_file_text(cls, file_text: str) -> "ObsidianNoteProperties":
        return ObsidianNoteProperties.from_obsidian_file_text(file_text=file_text)


@dataclass
class ObsidianProperties(NoteProperties):
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
    suspended: bool = dataclass_field(default=False)
    maximum_card_difficulty: float = dataclass_field(default=0.0)
    date_modified_in_anki: Optional[datetime] = dataclass_field(default=None)
    date_synced: Optional[datetime] = dataclass_field(default=None)

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


@dataclass
class ObsidianField(Field):
    attachments: List["ObsidianLinkedAttachment"]
    _markup_translator: MarkupTranslator

    @classmethod
    def from_obsidian_file_text(
        cls,
        file_text: str,
        note_path: Path,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        markup_translator: MarkupTranslator,
    ) -> List["ObsidianField"]:
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
            attachments = ObsidianLinkedAttachment.from_obsidian_file_text(
                file_text=text, note_path=note_path, obsidian_attachments_manager=obsidian_attachments_manager
            )
            for attachment in attachments:
                text = text.replace(
                    attachment.to_obsidian_file_text(), attachment.to_field_text()
                )
            result.append(
                ObsidianField(
                    name=header.strip(),
                    text=text,
                    attachments=attachments,
                    _markup_translator=markup_translator,
                )
            )

        return result

    @classmethod
    def from_fields(
        cls,
        fields: List[Field],
        markup_translator: MarkupTranslator,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        note_path: Path,
    ) -> List["ObsidianField"]:
        fields = [
            ObsidianField.from_field(
                field=field,
                markup_translator=markup_translator,
                obsidian_attachments_manager=obsidian_attachments_manager,
                note_path=note_path,
            )
            for field in fields
        ]
        return fields

    @classmethod
    def from_field(
        cls,
        field: Field,
        markup_translator: MarkupTranslator,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        note_path: Path,
    ) -> "ObsidianField":
        markdown_text = field.to_markdown()

        obsidian_attachments = []
        for attachment in field.attachments:
            obsidian_attachment = ObsidianLinkedAttachment.from_attachment(
                attachment=attachment,
                obsidian_attachments_manager=obsidian_attachments_manager,
                note_path=note_path,
            )
            obsidian_attachments.append(obsidian_attachment)
            markdown_text = markdown_text.replace(
                attachment.to_field_text(), obsidian_attachment.to_field_text()
            )

        return cls(
            name=field.name,
            text=markdown_text,
            attachments=obsidian_attachments,
            _markup_translator=markup_translator,
        )

    def set_from_markdown(self, markdown: str):
        self.text = markdown

    def set_from_html(self, html: str):
        markdown = self._markup_translator.translate_html_to_markdown(html=html)
        self.text = markdown

    def to_obsidian_file_text(self) -> str:
        field_title = self._build_field_title()
        field_text = f"{field_title}\n\n{self.text}\n\n"
        for attachment in self.attachments:
            field_text = field_text.replace(
                attachment.to_field_text(), attachment.to_obsidian_file_text()
            )
        return field_text

    def to_markdown(self) -> str:
        return self.text

    def to_html(self) -> str:
        html_text = self._markup_translator.translate_markdown_to_html(markdown=self.text)
        return html_text

    @staticmethod
    def _get_note_body(file_text: str) -> str:
        yaml_frontmatter_pattern = r"^---[\s\S]*?---\s*"
        note_body = re.sub(yaml_frontmatter_pattern, "", file_text, count=1)
        return note_body

    def _build_field_title(self) -> str:
        field_format_string = f"{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}\n{SRS_HEADER_TITLE_LEVEL} {self.name}"
        return field_format_string


@dataclass
class ObsidianLinkedAttachment(LinkedAttachment):
    _obsidian_file_text_path: str
    _obsidian_attachments_manager: ObsidianAttachmentsManager

    @classmethod
    def from_obsidian_file_text(
        cls,
        file_text: str,
        note_path: Path,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
    ) -> List["ObsidianLinkedAttachment"]:
        attachment_paths = obsidian_attachments_manager.attachment_paths_from_file_text(
            file_text=file_text, note_path=note_path
        )
        attachments = [
            cls(
                path=path,
                _obsidian_file_text_path=obsidian_file_text_path,
                _obsidian_attachments_manager=obsidian_attachments_manager,
            )
            for obsidian_file_text_path, path in attachment_paths.items()
        ]
        return attachments

    @classmethod
    def from_attachment(
        cls,
        attachment: LinkedAttachment,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        note_path: Path,
    ) -> "ObsidianLinkedAttachment":
        obsidian_file_text_path, obsidian_attachment_path = (
            obsidian_attachments_manager.ensure_attachment_is_in_obsidian(
                attachment=attachment, note_path=note_path
            )
        )
        return cls(
            path=obsidian_attachment_path,
            _obsidian_file_text_path=obsidian_file_text_path,
            _obsidian_attachments_manager=obsidian_attachments_manager,
        )

    def to_field_text(self) -> str:
        return str(self.path)

    def to_obsidian_file_text(self) -> str:
        path_quote = urllib.parse.quote(string=self._obsidian_file_text_path)
        return path_quote
