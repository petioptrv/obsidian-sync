from pathlib import Path

from obsidian_sync.synchronizers.notes_synchronizer import NotesSynchronizer
from tests.anki_test_app import AnkiTestApp
from tests.utils import build_obsidian_cloze_note


def test_sync_new_obsidian_note_with_math_equations_in_cloze_to_anki(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
    notes_synchronizer: NotesSynchronizer,
):
    in_line_equation = "A^*"
    block_equation = "B^*"
    cloze_field_html = f"""Some front with an in-line math {{{{c1::equation ${in_line_equation}$}}}}
and a {{{{c2::block equation:&nbsp;$${block_equation}$$}}}}"""
    build_obsidian_cloze_note(
        anki_test_app=anki_test_app,
        text=cloze_field_html,
        file_path=srs_folder_in_obsidian / "test.md",
    )

    notes_synchronizer.synchronize_notes()

    anki_note = list(anki_test_app.get_all_notes().values())[0]

    assert f"\({in_line_equation}\)" in anki_note.content.fields[0].to_html()
    assert f"\[{block_equation}\]" in anki_note.content.fields[0].to_html()
