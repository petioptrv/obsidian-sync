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

import urllib.parse
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import List

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.base_types.content import NoteField
from obsidian_sync.constants import OBSIDIAN_LINK_URL_FIELD_NAME
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.content.obsidian_reference import ObsidianReferenceFactory, \
    ObsidianReference
from obsidian_sync.obsidian.content.field.obsidian_field import ObsidianFieldFactory, ObsidianField
from obsidian_sync.obsidian.utils import obsidian_url_for_note_path


class ObsidianNoteFieldFactory(ObsidianFieldFactory):
    def __init__(self, addon_config: AddonConfig, references_factory: ObsidianReferenceFactory):
        super().__init__(addon_config=addon_config)
        self._references_factory = references_factory

    def from_fields(
        self,
        fields: List[NoteField],
        note_path: Path,
    ) -> List["ObsidianNoteField"]:
        obsidian_fields = [
            ObsidianNoteField.from_field(
                field=field_,
                obsidian_reference_factory=self._references_factory,
                note_path=note_path,
            )
            if field_.name != OBSIDIAN_LINK_URL_FIELD_NAME
            else ObsidianLinkURLNoteField.from_field(
                field=field_,
                obsidian_reference_factory=self._references_factory,
                note_path=note_path,
            )
            for field_ in fields
        ]

        if self._addon_config.add_obsidian_url_in_anki:
            obsidian_fields.append(
                ObsidianLinkURLNoteField.from_file_path(
                    note_path=note_path,
                    addon_config=self._addon_config,
                    obsidian_reference_factory=self._references_factory,
                )
            )

        return obsidian_fields

    def from_obsidian_file_text(self, file_text: str, note_path: Path) -> List["ObsidianNoteField"]:
        headers_and_paragraphs = self._get_headers_and_paragraphs_from_file_text(file_text=file_text)
        fields = []

        for header, paragraph in headers_and_paragraphs:
            fields.append(
                ObsidianNoteField.from_obsidian_file_header_and_paragraph(
                    header=header,
                    paragraph=paragraph,
                    note_path=note_path,
                    obsidian_reference_factory=self._references_factory,
                )
            )

        if self._addon_config.add_obsidian_url_in_anki:
            fields.append(
                ObsidianLinkURLNoteField.from_file_path(
                    note_path=note_path,
                    addon_config=self._addon_config,
                    obsidian_reference_factory=self._references_factory,
                )
            )

        return fields


@dataclass
class ObsidianNoteFieldBase(NoteField, ObsidianField, ABC):
    @classmethod
    def from_field(
        cls,
        field: NoteField,
        note_path: Path,
        obsidian_reference_factory: ObsidianReferenceFactory,
    ) -> "ObsidianNoteFieldBase":
        markdown_text = field.to_markdown()
        obsidian_references = []

        for reference in field.references:
            obsidian_reference = obsidian_reference_factory.from_reference(
                reference=reference, note_path=note_path
            )
            markdown_text = markdown_text.replace(
                reference.to_field_text(), obsidian_reference.to_field_text()
            )
            obsidian_references.append(obsidian_reference)

        return cls(
            name=field.name,
            text=markdown_text,
            references=obsidian_references,
        )


@dataclass
class ObsidianNoteField(ObsidianNoteFieldBase):
    references: List[ObsidianReference]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_obsidian_file_header_and_paragraph(
        cls,
        header: str,
        paragraph: str,
        note_path: Path,
        obsidian_reference_factory: ObsidianReferenceFactory,
    ) -> "ObsidianNoteField":
        text = paragraph.strip()
        references = obsidian_reference_factory.from_obsidian_field_text(
            field_text=text, note_path=note_path
        )

        for attachment in references:
            text = text.replace(
                f"]({attachment.to_obsidian_file_text()})", f"]({attachment.to_field_text()})"
            )

        field_ = ObsidianNoteField(name=header.strip(), text=text, references=references)

        return field_

    def to_obsidian_file_text(self) -> str:
        field_title = self._build_field_title()
        field_text = f"{field_title}\n\n{self.text}\n\n"
        for attachment in self.references:
            field_text = field_text.replace(
                attachment.to_field_text(), attachment.to_obsidian_file_text()
            )
        return field_text


@dataclass
class ObsidianLinkURLNoteField(ObsidianNoteFieldBase):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_file_path(
        cls,
        note_path: Path,
        addon_config: AddonConfig,
        obsidian_reference_factory: ObsidianReferenceFactory,
    ) -> "ObsidianLinkURLNoteField":
        markup_translator = MarkupTranslator()
        obsidian_url = obsidian_url_for_note_path(
            vault_path=addon_config.obsidian_vault_path, note_path=note_path
        )
        note_path_relative_to_vault = note_path.relative_to(addon_config.obsidian_vault_path)
        obsidian_field_text = markup_translator.to_markdown_link(
            text=OBSIDIAN_LINK_URL_FIELD_NAME, url=urllib.parse.quote(str(note_path_relative_to_vault))
        )
        field_text = markup_translator.to_markdown_link(text=OBSIDIAN_LINK_URL_FIELD_NAME, url=obsidian_url)
        field_text = markup_translator.sanitize_markdown(markdown=field_text)
        field_ = ObsidianLinkURLNoteField(
            name=OBSIDIAN_LINK_URL_FIELD_NAME,
            text=field_text,
            references=obsidian_reference_factory.from_obsidian_field_text(
                field_text=obsidian_field_text, note_path=note_path
            ),
        )
        return field_

    def to_obsidian_file_text(self) -> str:
        return ""
