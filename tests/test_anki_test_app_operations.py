from tests.anki_test_app import AnkiTestApp


def test_removing_and_creating_note_models(
    anki_setup_and_teardown,
    anki_test_app: AnkiTestApp,
):
    models_backup = anki_test_app.get_all_models()

    assert len(models_backup) == 6

    anki_test_app.remove_all_note_models()

    assert len(anki_test_app.get_all_models()) == 1

    model_template = {
        "name": "Card 1",
        "qfmt": "{{Front Alt}}",  # Question format
        "afmt": "{{FrontSide}}<hr id=answer>{{Back}}"  # Answer format
    }
    anki_test_app.add_custom_model(
        model_name="Basic Alt", field_names=["Front Alt", "Back"], template=model_template
    )

    assert len(anki_test_app.get_all_models()) == 2

    model_template = {
        "name": "Card 1",
        "qfmt": "{{Front Alt 2}}",  # Question format
        "afmt": "{{FrontSide}}<hr id=answer>{{Back}}"  # Answer format
    }
    anki_test_app.add_custom_model(
        model_name="Basic Alt 2", field_names=["Front Alt 2", "Back"], template=model_template
    )

    assert len(anki_test_app.get_all_models()) == 3

    anki_test_app.remove_all_note_models()
    anki_test_app.add_backed_up_note_models(models=models_backup)

    assert len(anki_test_app.get_all_models()) == 6
