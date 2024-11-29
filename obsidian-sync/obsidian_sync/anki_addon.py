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

from obsidian_sync.anki.app.anki_app import AnkiApp
from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.constants import ADD_ON_NAME
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.synchronizers.notes_synchronizer import NotesSynchronizer
from obsidian_sync.synchronizers.templates_synchronizer import TemplatesSynchronizer
from obsidian_sync.utils import format_add_on_message


class AnkiAddon:
    """Anki add-on composition root.

    todo: debug why Obsidian URL field is not displayed on my personal collection (it's still added...)
    todo: Implement the metadata-based approach
        - Ensure that an already synced Obsidian file that has been moved or renamed is handled properly

    todo: explore using wikilinks (the markdown converters have support for it)
    todo: add initialization walkthrough for first-time users to setup the configs interactively
    todo: Explore adding an option to include links in Obsidian that open the note in Anki using AnkiConnect
    """

    def __init__(self):
        self._anki_app = AnkiApp()
        self._addon_config = AddonConfig(anki_app=self._anki_app)
        self._obsidian_config = ObsidianConfig(addon_config=self._addon_config)
        self._templates_synchronizer = TemplatesSynchronizer(
            anki_app=self._anki_app,
            addon_config=self._addon_config,
            obsidian_config=self._obsidian_config,
        )
        self._notes_synchronizer = NotesSynchronizer(
            anki_app=self._anki_app,
            addon_config=self._addon_config,
            obsidian_config=self._obsidian_config,
        )

        self._add_menu_items()
        self._add_hooks()

    def _add_menu_items(self):
        self._anki_app.add_menu_item(title="Obsidian Sync", key_sequence="Ctrl+Y", callback=self._sync_with_obsidian)

    def _add_hooks(self):
        self._anki_app.add_sync_hook(self._sync_with_obsidian_on_anki_web_sync)

    def _sync_with_obsidian_on_anki_web_sync(self):
        if self._addon_config.sync_with_obsidian_on_anki_web_sync:
            self._sync_with_obsidian()

    def _sync_with_obsidian(self):
        if self._check_can_sync():
            self._templates_synchronizer.synchronize_templates()
            self._notes_synchronizer.synchronize_notes()

    def _check_can_sync(self) -> bool:
        can_sync = self._check_obsidian_settings()
        can_sync = can_sync and self._check_no_open_editing_anki_windows()
        return can_sync

    def _check_obsidian_settings(self) -> bool:
        can_sync = True

        if not self._obsidian_config.use_markdown_links:
            message = (
                "Wikilinks are not supported. To use Markdown links in Obsidian:"
                "\n\nOptions -> Files and links -> uncheck the \"Use [[Wikilinks]]\" option."
            )
            self._anki_app.show_critical(
                text=format_add_on_message(message=message),
                title=ADD_ON_NAME,
            )
            can_sync = False
        if not self._obsidian_config.templates_enabled:
            message = (
                "Obsidian templates must be enabled:"
                "\n\nOptions -> Core plugins -> check the \"Templates\" option."
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
