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
from pathlib import Path

ADD_ON_ID = "0"  # todo: update when available
ADD_ON_NAME = "obsidian-sync"

# GENERAL

DEFAULT_NODE_ID_FOR_NEW_NOTES = 0

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
SMALL_FILE_SIZE_MB_CUT_OFF = 2 << 11  # 4 MB
MEDIUM_FILE_SIZE_MG_CUT_OFF = 2 << 15  # 65 MB

IMAGE_FILE_SUFFIXES = [  # https://help.obsidian.md/Files+and+folders/Accepted+file+formats
    ".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"
]
AUDIO_FILE_SUFFIXES = [  # https://help.obsidian.md/Files+and+folders/Accepted+file+formats
    ".lac", ".m4a", ".mp3", ".ogg", ".wav", ".webm", ".3gp"
]
VIDEO_FILE_SUFFIXES = [  # https://help.obsidian.md/Files+and+folders/Accepted+file+formats
    ".mkv", ".mov", ".mp4", ".ogv", ".webm"
]
ATTACHMENT_FILE_SUFFIXES = IMAGE_FILE_SUFFIXES + AUDIO_FILE_SUFFIXES + VIDEO_FILE_SUFFIXES

# ADDON CONFIG

CONF_VAULT_PATH = "vault-path"
CONF_SRS_FOLDER_IN_OBSIDIAN = "srs-folder-in-obsidian"
CONF_SYNC_WITH_OBSIDIAN_ON_ANKI_WEB_SYNC = "sync-with-obsidian-on-anki-web-sync"
CONF_ANKI_DECK_NAME_FOR_OBSIDIAN_IMPORTS = "anki-deck-name-for-obsidian-imports"

# ANKI

DECK_NAME_SEPARATOR = "::"
OBSIDIAN_IMPORTS_DECK_NAME = "Obsidian Imports"

# OBSIDIAN

MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH = 200

MARKDOWN_FILE_SUFFIX = ".md"
SRS_ATTACHMENTS_FOLDER = "srs-media"

OBSIDIAN_SETTINGS_FOLDER = ".obsidian"
OBSIDIAN_TEMPLATES_SETTINGS_FILE = "templates.json"
OBSIDIAN_APP_SETTINGS_FILE = "app.json"
OBSIDIAN_LOCAL_TRASH_FOLDER = ".trash"

OBSIDIAN_TRASH_OPTION_KEY = "trashOption"
OBSIDIAN_SYSTEM_TRASH_OPTION_VALUE = "system"
OBSIDIAN_LOCAL_TRASH_OPTION_VALUE = "local"
OBSIDIAN_PERMA_DELETE_TRASH_OPTION_VALUE = "none"
OBSIDIAN_USE_MARKDOWN_LINKS_OPTION_KEY = "useMarkdownLinks"
OBSIDIAN_TEMPLATES_OPTION_KEY = "useMarkdownLinks"
OBSIDIAN_ATTACHMENT_FOLDER_PATH_OPTION_KEY = "attachmentFolderPath"

TEMPLATES_FOLDER_JSON_FIELD_NAME = "folder"

SRS_HEADER_TITLE_LEVEL = "##"
SRS_NOTE_IDENTIFIER_COMMENT = "%% anki-note %%"
SRS_NOTE_FIELD_IDENTIFIER_COMMENT = "%% srs-note-field %%"

# properties
MODEL_ID_PROPERTY_NAME = "model ID"
MODEL_NAME_PROPERTY_NAME = "model name"
NOTE_ID_PROPERTY_NAME = "note ID"
TAGS_PROPERTY_NAME = "tags"
DATE_MODIFIED_PROPERTY_NAME = "date modified in Anki"
DATE_SYNCED_PROPERTY_NAME = "date synced"
