import shutil
from typing import List, Dict

import aqt
from anki.models import NotetypeDict

from obsidian_sync.anki.app.anki_app import AnkiApp
from obsidian_sync.anki.anki_note import AnkiNote
from obsidian_sync.base_types.note import Note
from obsidian_sync.constants import DEFAULT_NODE_ID_FOR_NEW_NOTES
from obsidian_sync.markup_translator import MarkupTranslator


class AnkiTestApp(AnkiApp):
    """Extends the AnkiApp, providing testing functionality"""
    def __init__(self, markup_translator: MarkupTranslator):
        super().__init__(markup_translator=markup_translator)
        self.setup_performed = False

    def get_all_models(self) -> List[NotetypeDict]:
        assert self.setup_performed  # use the anki_setup_and_teardown fixture
        col = aqt.mw.col
        all_models = col.models.all()
        return all_models

    def get_model_id(self, model_name: str) -> int:
        assert self.setup_performed  # use the anki_setup_and_teardown fixture
        return aqt.mw.col.models.id_for_name(name=model_name)

    def remove_all_note_models(self):
        assert self.setup_performed  # use the anki_setup_and_teardown fixture
        col = aqt.mw.col
        col.models.remove_all_notetypes()

        col.models._clear_cache()

    def add_backed_up_note_models(self, models: List[NotetypeDict]):
        assert self.setup_performed  # use the anki_setup_and_teardown fixture
        col = aqt.mw.col

        for model_data in models:
            if not col.models.by_name(name=model_data["name"]):
                model = col.models.new(model_data["name"])
                model_data.pop("id", None)
                model.update(model_data)
                col.models.add(model)

        col.models._clear_cache()

    def add_custom_model(
        self,
        model_name: str,
        field_names: List[str],
        template: Dict[str, str],
    ):
        assert self.setup_performed  # use the anki_setup_and_teardown fixture
        col = aqt.mw.col
        model = col.models.new(name=model_name)

        for i, field_name in enumerate(field_names):
            col.models.add_field(
                notetype=model,
                field={
                    "name": field_name,
                    "ord": i,
                    "sticky": False,
                    "rtl": False,
                    "plainText": False,
                    "font": "Arial",
                    "size": 20,
                    "description": "",
                    "collapsed": False,
                    "excludeFromSearch": False,
                    "tag": None,
                    "preventDeletion": False,
                },
            )

        model["tmpls"] = [template]

        col.models.add(notetype=model)

        col.models._clear_cache()

    def rename_model_field(self, model_name: str, field_order: int, new_name: str):
        assert self.setup_performed  # use the anki_setup_and_teardown fixture
        col = aqt.mw.col
        note_type = col.models.by_name(name=model_name)
        col.models.rename_field(notetype=note_type, field=note_type["flds"][field_order], new_name=new_name)
        col.models.update_dict(notetype=note_type)

        col.models._clear_cache()

    def remove_all_notes(self):
        assert self.setup_performed  # use the anki_setup_and_teardown fixture

        col = aqt.mw.col
        note_ids = col.find_notes("")
        col.remove_notes(note_ids)

    def add_note(self, note: Note, deck_name: str) -> AnkiNote:
        assert note.content.properties.note_id == DEFAULT_NODE_ID_FOR_NEW_NOTES  # ID is set by Anki

        col = aqt.mw.col

        deck_id = col.decks.add_normal_deck_with_name(name=deck_name).id
        note_type = col.models.get(id=note.content.properties.model_id)
        anki_note = col.new_note(notetype=note_type)
        anki_note.tags = note.content.properties.tags
        anki_note.fields = [
            field.to_html()
            for field in note.content.fields
        ]

        aqt.mw.col.add_note(note=anki_note, deck_id=deck_id)

        created_note = self.get_note_by_id(note_id=anki_note.id)

        return created_note

    def remove_all_attachments(self):
        shutil.rmtree(path=self._media_manager.media_directory)
        self._media_manager.media_directory.mkdir()
