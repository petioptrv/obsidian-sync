import logging
from typing import Dict, List

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.anki.app.app import AnkiApp
from obsidian_sync.anki.note import AnkiNote
from obsidian_sync.constants import ADD_ON_NAME
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.config import ObsidianConfig
from obsidian_sync.obsidian.note import ObsidianNote
from obsidian_sync.obsidian.notes_manager import ObsidianNotesManager
from obsidian_sync.obsidian.vault import ObsidianVault
from obsidian_sync.utils import format_add_on_message


class NotesSynchronizer:
    def __init__(
        self,
        anki_app: AnkiApp,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        obsidian_vault = ObsidianVault(addon_config=addon_config, obsidian_config=obsidian_config)
        self._obsidian_notes_manager = ObsidianNotesManager(
            anki_app=anki_app,
            addon_config=addon_config,
            obsidian_config=obsidian_config,
            obsidian_vault=obsidian_vault,
        )
        self._markup_translator = MarkupTranslator()

    def synchronize_notes(self):
        try:
            anki_notes = self._anki_app.get_all_notes()
            self._obsidian_notes_manager.start_sync()
            obsidian_notes_result = self._obsidian_notes_manager.get_all_obsidian_notes()
            obsidian_notes_result.new_obsidian_notes = self._sanitize_new_obsidian_notes(
                new_obsidian_notes=obsidian_notes_result.new_obsidian_notes
            )

            while len(anki_notes) != 0:
                note_id, anki_note = anki_notes.popitem()
                obsidian_note = obsidian_notes_result.existing_obsidian_notes.pop(note_id, None)

                if obsidian_note is not None:
                    self._synchronize_notes(anki_note=anki_note, obsidian_note=obsidian_note)
                elif note_id in obsidian_notes_result.deleted_note_ids:
                    self._anki_app.delete_note_in_anki(note=anki_note)
                else:
                    anki_note = self._sanitize_anki_note(anki_note=anki_note)
                    self._obsidian_notes_manager.create_new_obsidian_note_from_note(
                        reference_note=anki_note
                    )

            while len(obsidian_notes_result.existing_obsidian_notes) != 0:
                note_id, obsidian_note = obsidian_notes_result.existing_obsidian_notes.popitem()
                self._obsidian_notes_manager.delete_note(note=obsidian_note)

            while len(obsidian_notes_result.new_obsidian_notes) != 0:
                obsidian_note = obsidian_notes_result.new_obsidian_notes.pop()
                anki_note = self._anki_app.create_new_note_in_anki_from_note(
                    note=obsidian_note, deck_name=self._addon_config.anki_deck_name_for_obsidian_imports
                )
                self._obsidian_notes_manager.update_obsidian_note_with_note(  # update note ID and timestamps
                    obsidian_note=obsidian_note, reference_note=anki_note
                )

            self._obsidian_notes_manager.commit_sync()

            self._anki_app.show_tooltip(tip=format_add_on_message("Notes synced successfully."))
        except Exception as e:
            logging.exception("Failed to sync notes.")
            self._anki_app.show_critical(
                text=format_add_on_message(f"Obsidian sync error: {str(e)}"),
                title=ADD_ON_NAME,
            )

    def _synchronize_notes(self, anki_note: AnkiNote, obsidian_note: ObsidianNote):
        anki_note_date_modified = anki_note.content.properties.date_modified_in_anki.timestamp()
        obsidian_note_date_modified_in_anki = obsidian_note.content.properties.date_modified_in_anki.timestamp()
        last_sync = obsidian_note.content.properties.date_synced.timestamp()
        obsidian_note_file_date_modified = obsidian_note.file.path.stat().st_mtime

        if anki_note_date_modified != obsidian_note_date_modified_in_anki:
            if anki_note_date_modified > obsidian_note_file_date_modified:
                anki_note = self._sanitize_anki_note(anki_note=anki_note)
                self._obsidian_notes_manager.update_obsidian_note_with_note(
                    obsidian_note=obsidian_note, reference_note=anki_note
                )
            else:
                obsidian_note = self._sanitize_obsidian_note(obsidian_note=obsidian_note)
                self._anki_app.update_anki_note_with_note(note=obsidian_note)
        elif obsidian_note_file_date_modified > last_sync + 1:  # this also covers Obsidian properties updates
            obsidian_note = self._sanitize_obsidian_note(obsidian_note=obsidian_note)
            self._anki_app.update_anki_note_with_note(note=obsidian_note)
        elif anki_note.content.properties != obsidian_note.content.properties:  # for props like max difficulty
            anki_note = self._sanitize_anki_note(anki_note=anki_note)
            self._obsidian_notes_manager.update_obsidian_note_with_note(
                obsidian_note=obsidian_note, reference_note=anki_note
            )

    def _sanitize_anki_notes(self, anki_notes: Dict[int, AnkiNote]) -> Dict[int, AnkiNote]:
        for note_id in list(anki_notes.keys()):
            anki_note = anki_notes[note_id]
            anki_notes[note_id] = self._sanitize_anki_note(anki_note=anki_note)

        return anki_notes

    def _sanitize_anki_note(self, anki_note: AnkiNote) -> AnkiNote:
        refactored = False

        for field in anki_note.content.fields:
            original_field_html = field.to_html()
            sanitized_field_html = self._markup_translator.sanitize_html(html=original_field_html)
            if sanitized_field_html != original_field_html:
                field.set_from_html(html=sanitized_field_html)
                refactored = True

        if refactored:
            self._anki_app.update_anki_note_with_note(note=anki_note)
            anki_note = self._anki_app.get_note_by_id(note_id=anki_note.id)

        return anki_note

    def _sanitize_new_obsidian_notes(self, new_obsidian_notes: List[ObsidianNote]) -> List[ObsidianNote]:
        new_obsidian_notes = [
            self._sanitize_obsidian_note(obsidian_note=obsidian_note)
            for obsidian_note in new_obsidian_notes
        ]
        return new_obsidian_notes

    def _sanitize_obsidian_note(self, obsidian_note: ObsidianNote) -> ObsidianNote:
        refactored = False

        for field in obsidian_note.content.fields:
            sanitized_field_markdown = self._markup_translator.sanitize_markdown(markdown=field.to_markdown())
            if field.to_markdown() != sanitized_field_markdown:
                field.set_from_markdown(markdown=sanitized_field_markdown)
                refactored = True

        if refactored:
            obsidian_note = self._obsidian_notes_manager.update_obsidian_note_with_note(
                obsidian_note=obsidian_note, reference_note=obsidian_note
            )

        return obsidian_note
