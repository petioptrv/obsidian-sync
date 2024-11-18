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
from hashlib import sha256
from pathlib import Path
from string import ascii_letters, digits

from send2trash import send2trash

from obsidian_sync.constants import MARKDOWN_FILE_SUFFIX, SRS_NOTE_IDENTIFIER_COMMENT, ATTACHMENT_FILE_SUFFIXES, \
    SMALL_FILE_SIZE_MB_CUT_OFF, MEDIUM_FILE_SIZE_MG_CUT_OFF


def check_is_srs_file(path: Path) -> bool:
    return (
        check_is_markdown_file(path=path)
        and SRS_NOTE_IDENTIFIER_COMMENT in path.read_text(encoding="utf-8")
    )


def check_is_attachment_file(path: Path) -> bool:
    return path.suffix in ATTACHMENT_FILE_SUFFIXES


def check_is_markdown_file(path: Path) -> bool:
    return path.suffix == MARKDOWN_FILE_SUFFIX


def move_file_to_system_trash(file_path: Path):
    send2trash(paths=file_path)


def clean_string_for_file_name(string: str) -> str:
    cloze_pattern = r"\{\{c\d+::(.*?)\}\}"
    string = re.sub(cloze_pattern, r"\1", string)  # remove cloze markers
    valid_chars = "-_.() %s%s" % (ascii_letters, digits)
    return "".join(c for c in string if c in valid_chars)


def check_files_are_identical(first: Path, second: Path) -> bool:
    identical = (
        (first.exists() and second.exists())
        and (first.stat().st_size == second.stat().st_size)
        and _check_file_content_is_identical(first=first, second=second)
    )
    return identical


def _check_file_content_is_identical(first: Path, second: Path) -> bool:
    identical = True

    if first.stat().st_size < SMALL_FILE_SIZE_MB_CUT_OFF:
        identical = first.read_bytes() == second.read_bytes()
    elif first.stat().st_size < MEDIUM_FILE_SIZE_MG_CUT_OFF:
        identical = _calculate_file_hash(file=first) == _calculate_file_hash(file=second)

    return identical


def _calculate_file_hash(file: Path):
    hash_func = sha256()

    with open(file, "rb") as f:
        while chunk := f.read(8192):  # Read in chunks of 8KB
            hash_func.update(chunk)

    return hash_func.hexdigest()
