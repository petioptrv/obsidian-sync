from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.obsidian.obsidian_notes_manager import ObsidianNotesManager
from obsidian_sync.synchronizers.notes_synchronizer import NotesSynchronizer
from tests.anki_test_app import AnkiTestApp
from tests.utils import build_anki_cloze_note


def test_sync_new_anki_note_with_math_equations_in_cloze_to_obsidian(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    addon_config: AddonConfig,
    notes_synchronizer: NotesSynchronizer,
    obsidian_notes_manager: ObsidianNotesManager,
):
    in_line_equation = "A^*"
    block_equation = "B^*"
    cloze_field_html = f"""Some front with an in-line math {{{{c1::equation \({in_line_equation}\)}}}} and
a {{{{c2::block equation:&nbsp;\[{block_equation}\]}}}}"""
    note = build_anki_cloze_note(
        anki_test_app=anki_test_app,
        text=cloze_field_html,
    )
    anki_note = anki_test_app.add_note(
        note=note, deck_name=addon_config.anki_deck_name_for_obsidian_imports
    )

    notes_synchronizer.synchronize_notes()

    obsidian_notes_result = obsidian_notes_manager.get_all_notes_categorized()
    obsidian_note = obsidian_notes_result.unchanged_notes[anki_note.id]
    first_field = obsidian_note.content.fields[0]

    assert f"${in_line_equation}$" in first_field.to_markdown()
    assert f"$${block_equation}$$" in first_field.to_markdown()

    anki_note = anki_test_app.get_note_by_id(note_id=anki_note.id)
    expected_sanitized_html = f"""<p>Some front with an in-line math {{{{c1::equation \({in_line_equation}\)}}}} and
a {{{{c2::block equation:&nbsp;\[{block_equation}\]}}}}</p>"""

    assert anki_note.content.fields[0].to_html() == expected_sanitized_html
