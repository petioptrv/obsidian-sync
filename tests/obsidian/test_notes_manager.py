import time
from pathlib import Path

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.addon_metadata import AddonMetadata
from obsidian_sync.obsidian.obsidian_notes_manager import ObsidianNotesManager
from tests.anki_test_app import AnkiTestApp
from tests.utils import build_basic_obsidian_note


def test_get_note_changes_method_finds_new_note(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    addon_metadata: AddonMetadata,
    srs_folder_in_obsidian: Path,
    obsidian_notes_manager: ObsidianNotesManager,
):
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=srs_folder_in_obsidian / "test.md",
    )

    with addon_metadata:
        note_changes = obsidian_notes_manager.get_all_obsidian_notes(
            updated_and_new_notes_only=True
        )

    assert len(note_changes.new_notes) == 1
    assert len(note_changes.existing_notes) == 0
    assert len(note_changes.deleted_note_ids) == 0


def test_get_note_changes_method_finds_updated_note(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    addon_metadata: AddonMetadata,
    srs_folder_in_obsidian: Path,
    obsidian_notes_manager: ObsidianNotesManager,
):
    obsidian_note_path = srs_folder_in_obsidian / "test.md"
    some_note_id = 1
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=obsidian_note_path,
        mock_note_id=some_note_id,
    )

    with addon_metadata:
        addon_metadata.add_synced_note(note_id=some_note_id, note_path=obsidian_note_path)
        addon_metadata._last_sync_timestamp = int(time.time()) - 1
        note_changes = obsidian_notes_manager.get_all_obsidian_notes(
            updated_and_new_notes_only=True
        )

    assert len(note_changes.new_notes) == 0
    assert len(note_changes.existing_notes) == 1
    assert len(note_changes.deleted_note_ids) == 0


def test_get_note_changes_method_ignores_unchanged_note(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    addon_metadata: AddonMetadata,
    srs_folder_in_obsidian: Path,
    obsidian_notes_manager: ObsidianNotesManager,
):
    obsidian_note_path = srs_folder_in_obsidian / "test.md"
    some_note_id = 1
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=obsidian_note_path,
        mock_note_id=some_note_id,
    )

    with addon_metadata:
        addon_metadata.add_synced_note(note_id=some_note_id, note_path=obsidian_note_path)
        addon_metadata._last_sync_timestamp = int(time.time()) + 1
        note_changes = obsidian_notes_manager.get_all_obsidian_notes(
            updated_and_new_notes_only=True
        )

    assert len(note_changes.new_notes) == 0
    assert len(note_changes.existing_notes) == 0
    assert len(note_changes.deleted_note_ids) == 0


def test_get_note_changes_method_finds_deleted_note(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    addon_metadata: AddonMetadata,
    srs_folder_in_obsidian: Path,
    obsidian_notes_manager: ObsidianNotesManager,
):
    obsidian_note_path = srs_folder_in_obsidian / "test.md"
    some_note_id = 1
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=obsidian_note_path,
        mock_note_id=some_note_id,
    )
    obsidian_note_path.unlink()

    with addon_metadata:
        addon_metadata.add_synced_note(note_id=some_note_id, note_path=obsidian_note_path)
        note_changes = obsidian_notes_manager.get_all_obsidian_notes(
            updated_and_new_notes_only=True
        )

    assert len(note_changes.new_notes) == 0
    assert len(note_changes.existing_notes) == 0
    assert len(note_changes.deleted_note_ids) == 1


def test_get_note_changes_method_finds_moved_note_identified_as_existing(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    addon_metadata: AddonMetadata,
    srs_folder_in_obsidian: Path,
    obsidian_notes_manager: ObsidianNotesManager,
):
    obsidian_note_path = srs_folder_in_obsidian / "test.md"
    updated_note_path = srs_folder_in_obsidian / "updated test.md"
    some_note_id = 1
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=obsidian_note_path,
        mock_note_id=some_note_id,
    )
    obsidian_note_path.rename(updated_note_path)

    with addon_metadata:
        addon_metadata.add_synced_note(note_id=some_note_id, note_path=obsidian_note_path)
        note_changes = obsidian_notes_manager.get_all_obsidian_notes(
            updated_and_new_notes_only=True
        )

    assert len(note_changes.new_notes) == 0
    assert len(note_changes.existing_notes) == 1
    assert len(note_changes.deleted_note_ids) == 0
    assert note_changes.existing_notes[some_note_id].file.path == updated_note_path

    with addon_metadata:
        assert addon_metadata.get_note_id_from_path(updated_note_path) == some_note_id
