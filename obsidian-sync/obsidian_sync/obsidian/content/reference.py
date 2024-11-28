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
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List

from obsidian_sync.base_types.content import Reference, MediaReference, ObsidianURLReference, NoteField
from obsidian_sync.obsidian.reference_manager import ObsidianReferencesManager


class ObsidianReferenceFactory:
    def __init__(self, obsidian_references_manager: ObsidianReferencesManager):
        self._obsidian_attachments_manager = obsidian_references_manager

    def from_obsidian_field_text(
        self, field_text: str, note_path: Path,
    ) -> List["ObsidianReference"]:
        attachment_paths = self._obsidian_attachments_manager.media_paths_from_file_text(
            file_text=field_text, note_path=note_path
        )
        references: List["ObsidianReference"] = [
            ObsidianMediaReference(
                path=path,
                _obsidian_file_text_path=obsidian_file_text_path,
                _obsidian_references_manager=self._obsidian_attachments_manager,
            )
            for obsidian_file_text_path, path in attachment_paths.items()
        ]
        obsidian_urls = self._obsidian_attachments_manager.obsidian_urls_from_file_text(
            file_text=field_text, note_path=note_path
        )
        references.extend(
            ObsidianURLReferenceInObsidian(
                url=url,
                _obsidian_file_text_path=obsidian_file_text_path,
                _obsidian_references_manager=self._obsidian_attachments_manager,
            )
            for obsidian_file_text_path, url in obsidian_urls.items()
        )
        return references

    def from_reference(self, reference: Reference, note_path: Path) -> "ObsidianReference":

        if isinstance(reference, MediaReference):
            obsidian_reference = ObsidianMediaReference.from_reference(
                reference=reference,
                obsidian_references_manager=self._obsidian_attachments_manager,
                note_path=note_path,
            )
        elif isinstance(reference, ObsidianURLReference):
            obsidian_reference = ObsidianURLReferenceInObsidian.from_reference(
                reference=reference,
                obsidian_references_manager=self._obsidian_attachments_manager,
                note_path=note_path,
            )
        else:
            raise NotImplementedError

        return obsidian_reference


class ObsidianReference(Reference, ABC):
    @abstractmethod
    def to_obsidian_file_text(self) -> str:
        ...


@dataclass
class ObsidianMediaReference(ObsidianReference, MediaReference):
    _obsidian_file_text_path: str
    _obsidian_references_manager: ObsidianReferencesManager

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_reference(
        cls,
        reference: MediaReference,
        obsidian_references_manager: ObsidianReferencesManager,
        note_path: Path,
    ) -> "ObsidianMediaReference":
        obsidian_media_path = obsidian_references_manager.ensure_media_is_in_obsidian(
            reference=reference, note_path=note_path
        )
        obsidian_file_text_path = str(obsidian_media_path.relative_to(obsidian_references_manager.vault_path))
        return cls(
            path=obsidian_media_path,
            _obsidian_file_text_path=obsidian_file_text_path,
            _obsidian_references_manager=obsidian_references_manager,
        )

    def to_obsidian_file_text(self) -> str:
        path_quote = urllib.parse.quote(string=self._obsidian_file_text_path)
        return path_quote


@dataclass
class ObsidianURLReferenceInObsidian(ObsidianReference, ObsidianURLReference):
    _obsidian_file_text_path: str
    _obsidian_references_manager: ObsidianReferencesManager

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_reference(
        cls,
        reference: ObsidianURLReference,
        obsidian_references_manager: ObsidianReferencesManager,
        note_path: Path,
    ) -> "ObsidianURLReferenceInObsidian":
        path_to_referenced_file = obsidian_references_manager.resolve_obsidian_url(
            reference=reference, note_path=note_path
        )
        obsidian_file_text_path = str(path_to_referenced_file.relative_to(obsidian_references_manager.vault_path))
        return cls(
            url=reference.url,
            _obsidian_file_text_path=obsidian_file_text_path,
            _obsidian_references_manager=obsidian_references_manager,
        )

    def to_obsidian_file_text(self) -> str:
        path_quote = urllib.parse.quote(string=self._obsidian_file_text_path)
        return path_quote
