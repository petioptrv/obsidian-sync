import time
from pathlib import Path

import pytest

from obsidian_sync.constants import SRS_PROPERTIES_DELIMITER, MODEL_ID_PROPERTY_NAME, SRS_NOTE_IDENTIFIER_COMMENT
from obsidian_sync.file_utils import check_is_markdown_file, check_is_srs_note_and_get_id
from tests.anki_test_app import AnkiTestApp
from tests.utils import build_basic_obsidian_note


@pytest.mark.skip(reason="for experimentation")
def test_first_approach_to_file_parsing(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
):
    file_path = srs_folder_in_obsidian / "some_test.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=file_path,
    )

    def second_approach(path: Path) -> bool:
        return (
            check_is_markdown_file(path=path)
            and SRS_NOTE_IDENTIFIER_COMMENT in path.read_text(encoding="utf-8")
        )

    t0 = time.time()

    for i in range(300000):
        second_approach(file_path)

    t1 = time.time()

    print(f"took {t1 - t0} seconds")


@pytest.mark.skip(reason="for experimentation")
def test_second_approach_to_file_parsing(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
):
    file_path = srs_folder_in_obsidian / "some_test.md"
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=file_path,
    )

    def second_approach(path: Path) -> bool:
        with open(path) as file:
            is_srs_file = check_is_markdown_file(path=path)
            if is_srs_file:
                line = file.readline()
                is_srs_file = line == SRS_PROPERTIES_DELIMITER
                if is_srs_file:
                    line = file.readline()
                    is_srs_file = line.startswith(MODEL_ID_PROPERTY_NAME)
                    while is_srs_file and line != SRS_PROPERTIES_DELIMITER:
                        try:
                            line = file.readline()
                        except EOFError:
                            is_srs_file = False
                    if is_srs_file:
                        is_srs_file = file.readline() == SRS_NOTE_IDENTIFIER_COMMENT

        return is_srs_file

    t0 = time.time()

    for i in range(300000):
        second_approach(file_path)

    t1 = time.time()

    print(f"took {t1 - t0} seconds")


@pytest.mark.skip(reason="for experimentation")
def test_third_approach_to_file_parsing(
    anki_setup_and_teardown,
    obsidian_setup_and_teardown,
    anki_test_app: AnkiTestApp,
    srs_folder_in_obsidian: Path,
):
    file_path = srs_folder_in_obsidian / "some_test.md"
    note_id = 1
    build_basic_obsidian_note(
        anki_test_app=anki_test_app,
        front_text="Some front",
        back_text="Some back",
        file_path=file_path,
        mock_note_id=note_id,
    )

    t0 = time.time()

    for i in range(3000):
        check_is_srs_note_and_get_id(file_path)

    t1 = time.time()

    print(f"took {t1 - t0} seconds")

    assert check_is_srs_note_and_get_id(file_path) == note_id
