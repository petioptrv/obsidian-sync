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

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ANKI

DECK_NAME_SEPARATOR = "::"

# OBSIDIAN

CONF_VAULT_PATH = "vault-path"
CONF_SRS_FOLDER_IN_OBSIDIAN = "srs-folder-in-obsidian"

MAX_OBSIDIAN_NOTE_FILE_NAME_LENGTH = 200

MARKDOWN_FILE_SUFFIX = "md"
SRS_ATTACHMENTS_FOLDER = Path("/ankimedia")

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
TEMPLATE_DATE_FORMAT = "YYYY-MM-DD"
TEMPLATE_TIME_FORMAT = "HH:mm:ss"

SRS_HEADER_TITLE_LEVEL = "##"
SRS_NOTE_IDENTIFIER_COMMENT = "<!--anki-note-->"
SRS_NOTE_FIELD_IDENTIFIER_COMMENT = "<!--srs-note-field-->"

# properties
MODEL_ID_PROPERTY_NAME = "mid"
NOTE_ID_PROPERTY_NAME = "nid"
TAGS_PROPERTY_NAME = "tags"
DATE_MODIFIED_PROPERTY_NAME = "date modified"
DATE_SYNCED_PROPERTY_NAME = "date synced"

DEFAULT_NODE_ID_FOR_NEW_OBSIDIAN_NOTES = 0

IMAGE_FILE_EXTENSIONS = [  # https://help.obsidian.md/Files+and+folders/Accepted+file+formats
    "avif", "bmp", "gif", "jpeg", "jpg", "png", "svg", "webp"
]
AUDIO_EXTENSIONS = [  # https://help.obsidian.md/Files+and+folders/Accepted+file+formats
    "lac", "m4a", "mp3", "ogg", "wav", "webm", "3gp"
]
VIDEO_EXTENSIONS = [  # https://help.obsidian.md/Files+and+folders/Accepted+file+formats
    "mkv", "mov", "mp4", "ogv", "webm"
]
