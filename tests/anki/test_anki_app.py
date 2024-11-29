import time
from pathlib import Path

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.addon_metadata import AddonMetadata
from tests.anki_test_app import AnkiTestApp
from tests.utils import build_basic_anki_note


def test_get_note_changes_method_finds_new_note(
    anki_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    addon_metadata: AddonMetadata,
):
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    with addon_metadata:
        note_changes = anki_test_app.get_note_changes()

    assert len(note_changes.new_notes) == 1
    assert len(note_changes.updated_notes) == 0
    assert len(note_changes.deleted_note_ids) == 0


def test_get_note_changes_method_finds_updated_note(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    addon_metadata: AddonMetadata,
    srs_folder_in_obsidian: Path,
):
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )
    obsidian_note_path = srs_folder_in_obsidian / "note.md"

    with addon_metadata:
        addon_metadata.add_synced_note(note_id=anki_note.id, note_path=obsidian_note_path)
        addon_metadata._last_sync_timestamp = int(time.time()) - 1
        note_changes = anki_test_app.get_note_changes()

    assert len(note_changes.new_notes) == 0
    assert len(note_changes.updated_notes) == 1
    assert len(note_changes.deleted_note_ids) == 0


def test_get_note_changes_method_ignores_unchanged_note(
    anki_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    addon_metadata: AddonMetadata,
    srs_folder_in_obsidian: Path,
):
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )
    obsidian_note_path = srs_folder_in_obsidian / "note.md"

    with addon_metadata:
        addon_metadata.add_synced_note(note_id=anki_note.id, note_path=obsidian_note_path)
        addon_metadata._last_sync_timestamp = int(time.time()) + 1
        note_changes = anki_test_app.get_note_changes()

    assert len(note_changes.new_notes) == 0
    assert len(note_changes.updated_notes) == 0
    assert len(note_changes.deleted_note_ids) == 0


def test_get_note_changes_method_finds_deleted_note(
    anki_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    addon_metadata: AddonMetadata,
    srs_folder_in_obsidian: Path,
):
    note = build_basic_anki_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )
    anki_test_app.delete_note_by_id(note_id=anki_note.id)
    obsidian_note_path = srs_folder_in_obsidian / "note.md"

    with addon_metadata:
        addon_metadata.add_synced_note(note_id=anki_note.id, note_path=obsidian_note_path)
        note_changes = anki_test_app.get_note_changes()

    assert len(note_changes.new_notes) == 0
    assert len(note_changes.updated_notes) == 0
    assert len(note_changes.deleted_note_ids) == 1
