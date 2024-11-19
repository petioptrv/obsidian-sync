import logging
from typing import Dict, List

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.addon_metadata import AddonMetadata
from obsidian_sync.anki.app.anki_app import AnkiApp
from obsidian_sync.anki.anki_note import AnkiNote
from obsidian_sync.constants import ADD_ON_NAME
from obsidian_sync.markup_translator import MarkupTranslator
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig
from obsidian_sync.obsidian.obsidian_note import ObsidianNote
from obsidian_sync.obsidian.obsidian_vault import ObsidianVault
from obsidian_sync.utils import format_add_on_message


class NotesSynchronizer:
    def __init__(
        self,
        anki_app: AnkiApp,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
        obsidian_vault: ObsidianVault,
        markup_translator: MarkupTranslator,
        metadata: AddonMetadata,
    ):
        self._anki_app = anki_app
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config
        self._obsidian_vault = obsidian_vault
        self._markup_translator = markup_translator
        self._metadata = metadata

    def synchronize_notes(self):
        try:
            self._metadata.load()
            anki_notes = self._anki_app.get_all_notes()
            anki_notes = self._sanitize_anki_notes(anki_notes=anki_notes)
            existing_obsidian_notes, new_obsidian_notes = self._obsidian_vault.get_all_obsidian_notes()
            new_obsidian_notes = self._sanitize_new_obsidian_notes(new_obsidian_notes=new_obsidian_notes)
            obsidian_deleted_notes = self._obsidian_vault.get_all_obsidian_deleted_notes()
            obsidian_deleted_notes = obsidian_deleted_notes.union(
                self._metadata.anki_notes_synced_to_obsidian.difference(
                    set(existing_obsidian_notes.keys())
                )
            )

            while len(anki_notes) != 0:
                note_id, anki_note = anki_notes.popitem()
                obsidian_note = existing_obsidian_notes.pop(note_id, None)

                if obsidian_note is not None:
                    self._synchronize_notes(anki_note=anki_note, obsidian_note=obsidian_note)
                elif note_id in obsidian_deleted_notes:
                    anki_note.delete()
                    self._metadata.anki_notes_synced_to_obsidian.discard(note_id)
                else:
                    ObsidianNote.from_note(
                        note=anki_note,
                        addon_config=self._addon_config,
                        obsidian_vault=self._obsidian_vault,
                        markup_translator=self._markup_translator,
                    )
                    self._metadata.anki_notes_synced_to_obsidian.add(anki_note.id)

            while len(existing_obsidian_notes) != 0:
                note_id, obsidian_note = existing_obsidian_notes.popitem()
                obsidian_note.delete()
                self._metadata.anki_notes_synced_to_obsidian.discard(note_id)

            while len(new_obsidian_notes) != 0:
                obsidian_note = new_obsidian_notes.pop()
                anki_note = AnkiNote.from_note(
                    note=obsidian_note,
                    anki_app=self._anki_app,
                    addon_config=self._addon_config,
                )
                obsidian_note.update_with_note(note=anki_note)  # update note ID and timestamps
                self._metadata.anki_notes_synced_to_obsidian.add(anki_note.id)

            self._metadata.save()

            self._anki_app.show_tooltip(tip=format_add_on_message("Notes synced successfully."))
        except Exception as e:
            logging.exception("Failed to sync notes.")
            self._anki_app.show_critical(
                text=format_add_on_message(f"Obsidian sync error: {str(e)}"),
                title=ADD_ON_NAME,
            )

    def _sanitize_anki_notes(self, anki_notes: Dict[int, AnkiNote]) -> Dict[int, AnkiNote]:
        for note_id in list(anki_notes.keys()):
            anki_note = anki_notes[note_id]
            refactored = False

            for field in anki_note.content.fields:
                sanitized_field_html = self._markup_translator.sanitize_html(html=field.to_html())
                if sanitized_field_html != field.to_html():
                    field.set_from_html(html=sanitized_field_html)
                    refactored = True

            if refactored:
                self._anki_app.update_note_in_anki(anki_note=anki_note)
                anki_notes[note_id] = self._anki_app.get_note_by_id(note_id=note_id)

        return anki_notes

    def _sanitize_new_obsidian_notes(self, new_obsidian_notes: List[ObsidianNote]) -> List[ObsidianNote]:
        for obsidian_note in new_obsidian_notes:
            refactored = False

            for field in obsidian_note.content.fields:
                sanitized_field_markdown = self._markup_translator.sanitize_markdown(markdown=field.to_markdown())
                if field.to_markdown() != sanitized_field_markdown:
                    field.set_from_markdown(markdown=sanitized_field_markdown)
                    refactored = True

            if refactored:
                obsidian_note.save()

        return new_obsidian_notes

    @staticmethod
    def _synchronize_notes(anki_note: AnkiNote, obsidian_note: ObsidianNote):
        anki_note_date_modified = anki_note.content.properties.date_modified_in_anki.timestamp()
        obsidian_note_date_modified_in_anki = obsidian_note.content.properties.date_modified_in_anki.timestamp()
        last_sync = obsidian_note.content.properties.date_synced.timestamp()
        obsidian_note_file_date_modified = obsidian_note.file.path.stat().st_mtime

        if anki_note_date_modified != obsidian_note_date_modified_in_anki:
            if anki_note_date_modified > obsidian_note_file_date_modified:
                obsidian_note.update_with_note(note=anki_note)
            else:
                anki_note.update_with_note(note=obsidian_note)
        elif obsidian_note_file_date_modified > last_sync + 1:  # this also covers Obsidian properties updates
            anki_note.update_with_note(note=obsidian_note)
        elif anki_note.content.properties != obsidian_note.content.properties:  # for props like max difficulty
            obsidian_note.update_with_note(note=obsidian_note)
