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
from typing import List

from obsidian_sync.anki.app.anki_media_manager import AnkiReferencesManager
from obsidian_sync.base_types.content import Field, Content, Properties, NoteProperties, Reference, NoteContent, \
    NoteField, TemplateField, MediaReference, ObsidianURLReference
from obsidian_sync.markup_translator import MarkupTranslator


@dataclass
class AnkiContent(Content):
    properties: "AnkiProperties"
    fields: List["AnkiField"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiTemplateContent(AnkiContent):
    properties: "AnkiTemplateProperties"
    fields: List["AnkiTemplateField"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiNoteContent(AnkiContent):
    properties: "AnkiNoteProperties"
    fields: List["AnkiNoteField"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_content(
        cls,
        content: NoteContent,
        references_factory: "AnkiReferencesFactory",
    ) -> "AnkiNoteContent":
        properties = AnkiNoteProperties.from_properties(properties=content.properties)
        fields = AnkiNoteField.from_fields(
            fields=content.fields, references_factory=references_factory
        )
        return cls(properties=properties, fields=fields)


@dataclass
class AnkiProperties(Properties):

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiTemplateProperties(AnkiProperties):

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiNoteProperties(NoteProperties):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_properties(cls, properties: NoteProperties) -> "AnkiNoteProperties":
        return cls(
            model_id=properties.model_id,
            model_name=properties.model_name,
            note_id=properties.note_id,
            tags=properties.tags,
            date_modified_in_anki=properties.date_modified_in_anki,
        )


@dataclass
class AnkiField(Field):
    def __post_init__(self):
        self._markup_translator = MarkupTranslator()

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def set_from_markdown(self, markdown: str):
        self.text = self._markup_translator.translate_markdown_to_html(markdown=markdown)

    def set_from_html(self, html: str):
        self.text = html

    def to_markdown(self) -> str:
        markdown_text = self._markup_translator.translate_html_to_markdown(html=self.text)
        return markdown_text

    def to_html(self) -> str:
        return self.text


@dataclass
class AnkiTemplateField(TemplateField, AnkiField):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)


@dataclass
class AnkiNoteField(NoteField, AnkiField):
    references: List["AnkiReference"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_fields(
        cls,
        fields: List[NoteField],
        references_factory: "AnkiReferencesFactory",
    ) -> List["AnkiNoteField"]:
        fields = [
            AnkiNoteField.from_field(
                field=field, references_factory=references_factory
            )
            for field in fields
        ]
        return fields

    @classmethod
    def from_field(
        cls,
        field: NoteField,
        references_factory: "AnkiReferencesFactory",
    ) -> "AnkiNoteField":
        html_text = field.to_html()
        anki_references = []

        for reference in field.references:
            anki_reference = references_factory.from_reference(
                reference=reference, references_manager=references_factory.references_manager
            )
            html_text = html_text.replace(
                reference.to_field_text(), anki_reference.to_field_text()
            )
            anki_references.append(anki_reference)

        return cls(
            name=field.name,
            text=html_text,
            references=anki_references,
        )

    def to_anki_field_text(self) -> str:
        field_text = self.text

        for reference in self.references:
            field_text = field_text.replace(
                reference.to_field_text(), reference.to_anki_field_text()
            )

        return field_text


class AnkiReferencesFactory:
    def __init__(self, anki_references_manager: AnkiReferencesManager):
        self._references_manager = anki_references_manager

    @property
    def references_manager(self) -> AnkiReferencesManager:
        return self._references_manager

    def from_card_field_text(
        self, model_id: int, card_field_text: str
    ) -> List["AnkiReference"]:
        references: List["AnkiReference"] = [
            AnkiMediaReference(path=file_path)
            for file_path in self._references_manager.get_media_file_paths_from_card_field_text(
                model_id=model_id, field_text=card_field_text
            )
        ]
        references.extend(
            ObsidianURLReferenceInAnki(url=obsidian_url)
            for obsidian_url in self._references_manager.get_obsidian_urls_from_card_field_text(
                field_text=card_field_text
            )
        )
        return references

    def from_reference(self, reference: Reference, references_manager: AnkiReferencesManager) -> "AnkiReference":
        if isinstance(reference, MediaReference):
            anki_reference = (
                AnkiMediaReference.from_reference(reference=reference, references_manager=references_manager)
            )
        elif isinstance(reference, ObsidianURLReference):
            anki_reference = ObsidianURLReferenceInAnki.from_reference(reference=reference)
        else:
            raise NotImplementedError

        return anki_reference


@dataclass
class AnkiReference(Reference, ABC):
    @abstractmethod
    def to_anki_field_text(self) -> str:
        ...


@dataclass
class AnkiMediaReference(AnkiReference, MediaReference):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_reference(
        cls, reference: MediaReference, references_manager: AnkiReferencesManager
    ) -> "AnkiMediaReference":
        anki_media_path = references_manager.ensure_media_is_in_anki(reference=reference)
        return cls(path=anki_media_path)

    def to_anki_field_text(self) -> str:
        return self.path.name


@dataclass
class ObsidianURLReferenceInAnki(AnkiReference, ObsidianURLReference):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_reference(cls, reference: ObsidianURLReference) -> "ObsidianURLReferenceInAnki":
        return cls(url=reference.url)

    def to_anki_field_text(self) -> str:
        return self.url
