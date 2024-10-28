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

from obsidian_sync.anki.anki_app import AnkiApp
from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.constants import ADD_ON_NAME
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.synchronizers.media_synchronizer import MediaSynchronizer
from obsidian_sync.synchronizers.templates_synchronizer import TemplatesSynchronizer
from obsidian_sync.utils import format_add_on_message


class AnkiAddon:
    """Anki add-on composition root."""

    def __init__(self):
        self._anki_app = AnkiApp()
        self._addon_config = AddonConfig(anki_app=self._anki_app)
        self._obsidian_config = ObsidianConfig(addon_config=self._addon_config)
        self._markup_translator = MarkupTranslator()
        self._obsidian_vault = ObsidianVault(
            anki_app=self._anki_app,
            addon_config=self._addon_config,
            obsidian_config=self._obsidian_config,
            markup_translator=self._markup_translator,
        )
        self._templates_synchronizer = TemplatesSynchronizer(
            anki_app=self._anki_app,
            addon_config=self._addon_config,
            obsidian_config=self._obsidian_config,
            obsidian_vault=self._obsidian_vault,
            markup_translator=self._markup_translator,
        )
        self._media_synchronizer = MediaSynchronizer()

        self._add_menu_items()
        self._add_menu_items()

    def _add_menu_items(self):
        self._anki_app.add_menu_item(title="Obsidian Sync", key_sequence="Ctrl+Y", callback=self._sync_with_obsidian)
        # todo: add option to open Obsidian note from selected Anki note (both shown on the review screen and if selected in the browse window)

    def _sync_with_obsidian(self):
        # todo: Update associated notes on model update (e.g. changing field names).

        # ENHANCEMENTS

        # todo: support note linking in Anki too (via the add-on)
        # todo: for conflicting notes
        #     todo: explore git-style diff conflict resolver in Python
        #     todo: else, interactive choice of which one to keep, with option to apply to all remaining: keep most recent/keep Anki/keep Obsidian

        # todo: add option to only transfer cards from Obsidian to Anki if their parents are already learned to a configurable level

        if self._check_can_sync():
            self._templates_synchronizer.synchronize_templates()
            # self._media_synchronizer.synchronize_media()
            # self._notes_synchronizer.synchronize_notes()

    def _check_can_sync(self) -> bool:
        can_sync = self._check_obsidian_settings()
        can_sync = can_sync and self._check_no_open_editing_anki_windows()
        return can_sync

    def _check_obsidian_settings(self) -> bool:
        can_sync = True

        if not self._obsidian_config.use_markdown_links:
            message = (
                "Wikilinks are not supported. To use Markdown links in Obsidian:"
                " Options -> Files and links -> uncheck the Use [[Wikilinks]] option."
            )
            self._anki_app.show_critical(
                text=format_add_on_message(message=message),
                title=ADD_ON_NAME,
            )
            can_sync = False
        elif not self._obsidian_config.templates_enabled:
            message = (
                "Obsidian templates must be enabled:"
                " Options -> Core plugins -> check the Templates option."
            )
            self._anki_app.show_critical(
                text=format_add_on_message(message=message),
                title=ADD_ON_NAME
            )
            can_sync = False

        return can_sync

    def _check_no_open_editing_anki_windows(self) -> bool:
        open_editing_windows = self._anki_app.get_open_editing_anki_windows()
        can_sync = True
        if open_editing_windows:
            message = "Please close the following windows before syncing:\n\n" + "\n".join(open_editing_windows)
            self._anki_app.show_critical(
                text=format_add_on_message(message=message),
                title=ADD_ON_NAME
            )
            can_sync = False
        return can_sync
