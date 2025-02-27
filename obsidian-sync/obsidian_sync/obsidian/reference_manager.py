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
import shutil
import unicodedata
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.base_types.content import MediaReference, ObsidianURLReference
from obsidian_sync.constants import MEDIA_FILE_SUFFIXES, MARKDOWN_FILE_SUFFIX
from obsidian_sync.file_utils import check_files_are_identical
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.utils import obsidian_url_for_note_path


class ObsidianReferencesManager:
    def __init__(
        self, addon_config: AddonConfig, obsidian_config: ObsidianConfig
    ):
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config

    @property
    def vault_path(self) -> Path:
        return self._addon_config.obsidian_vault_path

    def media_paths_from_file_text(self, file_text: str, note_path: Path) -> List["ReferencedVaultFile"]:
        media_paths = self._referenced_vault_files_from_file_text(
            file_text=file_text,
            note_path=note_path,
            file_suffixes=MEDIA_FILE_SUFFIXES,
            allow_location_identifiers=False,
        )
        return media_paths

    def ensure_media_is_in_obsidian(self, reference: MediaReference, note_path: Path) -> Path:
        obsidian_media_path = self._resolve_vault_file_reference_path(
            base_path=Path(reference.path.name), note_path=note_path
        )

        if (
            not obsidian_media_path.exists()
            or not check_files_are_identical(first=reference.path, second=obsidian_media_path)
        ):
            obsidian_media_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src=reference.path, dst=obsidian_media_path)

        return obsidian_media_path

    def obsidian_urls_from_file_text(self, file_text: str, note_path: Path) -> Dict[str, str]:
        markdown_file_paths = self._referenced_vault_files_from_file_text(
            file_text=file_text,
            note_path=note_path,
            file_suffixes=[MARKDOWN_FILE_SUFFIX],
            allow_location_identifiers=True,
            allow_location_identifiers_only=True,
        )
        obsidian_urls = {}
        for referenced_vault_file in markdown_file_paths:
            url = obsidian_url_for_note_path(
                vault_path=self._addon_config.obsidian_vault_path,
                note_path=referenced_vault_file.path,
                location_identifier=referenced_vault_file.location_identifier,
            )
            obsidian_urls[referenced_vault_file.string_in_text] = url
        return obsidian_urls

    def resolve_obsidian_url(self, reference: ObsidianURLReference, note_path: Path) -> "ReferencedVaultFile":
        obsidian_url_pattern = r"obsidian:\/\/open\?vault=([^&]+)&file=([^&#]+)(#.+)?"
        unquoted_url = urllib.parse.unquote(reference.url)
        match = re.match(pattern=obsidian_url_pattern, string=unquoted_url)
        base_path = Path(match.group(2))
        vault_file_path = self._resolve_vault_file_reference_path(
            base_path=base_path, note_path=note_path
        )
        location_identifier = match.group(3) or ""
        string_in_text = f"{urllib.parse.quote(str(base_path)) if vault_file_path != note_path else ''}{location_identifier}"
        return ReferencedVaultFile(
            path=vault_file_path, location_identifier=location_identifier, string_in_text=string_in_text
        )

    def _referenced_vault_files_from_file_text(
        self,
        file_text: str,
        note_path: Path,
        file_suffixes: List[str],
        allow_location_identifiers: bool,
        allow_location_identifiers_only: bool = False,
    ) -> List["ReferencedVaultFile"]:
        file_reference_pattern = self._build_reference_file_type_matcher(
            file_suffixes=file_suffixes,
            allow_location_identifiers=allow_location_identifiers,
            allow_location_identifiers_only=allow_location_identifiers_only,
        )
        vault_file_paths = []

        for quoted_path_string, location_identifier, _ in re.findall(file_reference_pattern, file_text, re.DOTALL):
            path_string = urllib.parse.unquote(string=quoted_path_string) if quoted_path_string else str(note_path)
            file_path = self._resolve_vault_file_reference_path(
                base_path=Path(path_string), note_path=note_path
            )
            if file_path.exists():
                associated_string_in_text = f"{quoted_path_string}{location_identifier}"
                vault_file_paths.append(
                    ReferencedVaultFile(
                        path=file_path,
                        location_identifier=location_identifier,
                        string_in_text=associated_string_in_text,
                    )
                )

        return vault_file_paths

    def _resolve_vault_file_reference_path(self, base_path: Path, note_path: Path) -> Path:
        """If the file name is unique in the vault or if the file is
        in the same folder as the note, Obsidian will use only the file name.

        If there are duplicates in folders other than the note's folder, Obsidian will
        use paths relative to the vault directory."""

        sanitized_path = Path(self._sanitize_path_string(path_string=str(base_path)))

        if sanitized_path.name == str(sanitized_path):
            if (note_path / sanitized_path.name).exists():
                media_path = note_path / sanitized_path
            else:
                try:
                    media_path = next(
                        self._addon_config.obsidian_vault_path.rglob(pattern=str(sanitized_path))
                    )
                except StopIteration:  # does not exist in Obsidian
                    default_media_folder = self._get_default_attachment_folder(note_path=note_path)
                    media_path = default_media_folder / sanitized_path
        else:  # path relative to vault directory
            media_path = self._addon_config.obsidian_vault_path / sanitized_path

        return media_path

    @staticmethod
    def _sanitize_path_string(path_string: str) -> str:
        path_string = "".join(   # Replace all non-standard spaces and whitespace
            " " if unicodedata.category(char).startswith("Z") else char for char in path_string
        )
        path_string = re.sub(r"\s", " ", path_string)  # Remove any other problematic characters if needed
        return path_string

    def _get_default_attachment_folder(self, note_path: Path) -> Path:
        return self._obsidian_config.srs_attachments_folder

    @staticmethod
    def _build_reference_file_type_matcher(
        file_suffixes: List[str],
        allow_location_identifiers: bool,
        allow_location_identifiers_only: bool = False,  # for referencing a section or block in the current file
    ) -> str:
        assert not allow_location_identifiers_only or allow_location_identifiers

        square_brackets_piece = r"!?\[[^\]]*\]"

        file_reference_matcher = "\\" + "|\\".join(file_suffixes)
        file_matcher = f"(.*?(?:{file_reference_matcher})){'?' if allow_location_identifiers_only else ''}"
        location_matcher = """(#[^)"]+)?""" if allow_location_identifiers else "()?"

        comment_piece_matcher = """("(?:.*[^"])")?"""

        matcher = (  # source: https://stackoverflow.com/a/44227600/6793798
            rf"""{square_brackets_piece}\({file_matcher}{location_matcher}\s*{comment_piece_matcher}\s*\)"""
        )

        return matcher


@dataclass
class ReferencedVaultFile:
    path: Path
    location_identifier: str
    string_in_text: str
