import filecmp
import shutil
from pathlib import Path

from PIL import Image as PILImage

from obsidian_sync.synchronizers.media_synchronizer import MediaSynchronizer
from tests.anki_mock import AnkiMocker


def test_copy_new_anki_media_to_obsidian(
    tmp_path: Path,
    anki_mocker: AnkiMocker,
    some_test_image: PILImage,
    srs_attachments_in_obsidian_folder_mock: Path,
    media_synchronizer: MediaSynchronizer,
):
    anki_image_file = tmp_path / "img.jpg"
    some_test_image.save(anki_image_file)
    anki_mocker.set_media_files(files=[anki_image_file])

    assert not srs_attachments_in_obsidian_folder_mock.exists()

    media_synchronizer.synchronize_media()
    srs_attachments_in_obsidian = list(srs_attachments_in_obsidian_folder_mock.iterdir())

    assert len(srs_attachments_in_obsidian) == 1
    assert len(anki_mocker.get_added_media_files()) == 0

    obsidian_attachment = srs_attachments_in_obsidian[0]

    assert filecmp.cmp(f1=anki_image_file, f2=obsidian_attachment, shallow=False)

    media_synchronizer.synchronize_media()

    assert len(list(srs_attachments_in_obsidian_folder_mock.iterdir())) == 1
    assert len(anki_mocker.get_added_media_files()) == 0


def test_copy_new_obsidian_media_to_anki(
    tmp_path: Path,
    srs_attachments_in_obsidian_folder_mock: Path,
    anki_mocker: AnkiMocker,
    some_test_image: PILImage,
    media_synchronizer: MediaSynchronizer,
):
    srs_attachments_in_obsidian_folder_mock.mkdir(parents=True)
    obsidian_image_file = srs_attachments_in_obsidian_folder_mock / "img.jpg"
    some_test_image.save(obsidian_image_file)

    media_synchronizer.synchronize_media()

    added_anki_media_files = anki_mocker.get_added_media_files()

    assert len(list(srs_attachments_in_obsidian_folder_mock.iterdir())) == 1
    assert len(added_anki_media_files) == 1
    assert filecmp.cmp(f1=obsidian_image_file, f2=added_anki_media_files[0], shallow=False)

    anki_image_file = tmp_path / "img.jpg"
    some_test_image.save(anki_image_file)
    anki_mocker.set_media_files(files=[anki_image_file])

    media_synchronizer.synchronize_media()

    assert len(list(srs_attachments_in_obsidian_folder_mock.iterdir())) == 1
    assert len(anki_mocker.get_added_media_files()) == 1


def test_update_anki_media_in_obsidian(
    tmp_path: Path,
    srs_attachments_in_obsidian_folder_mock: Path,
    anki_mocker: AnkiMocker,
    some_test_image: PILImage,
    second_test_image: PILImage,
    media_synchronizer: MediaSynchronizer,
):
    srs_attachments_in_obsidian_folder_mock.mkdir(parents=True)
    obsidian_image_file = srs_attachments_in_obsidian_folder_mock / "img.jpg"
    obsidian_image_file_duplicat = tmp_path / "img-back.jpg"
    some_test_image.save(obsidian_image_file)
    shutil.copy(src=obsidian_image_file, dst=obsidian_image_file_duplicat)

    anki_image_file = tmp_path / "img.jpg"
    second_test_image.save(anki_image_file)
    anki_mocker.set_media_files(files=[anki_image_file])

    assert obsidian_image_file != obsidian_image_file_duplicat
    assert filecmp.cmp(f1=obsidian_image_file, f2=obsidian_image_file_duplicat, shallow=False)
    assert not filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file, shallow=False)
    assert not filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file_duplicat, shallow=False)

    media_synchronizer.synchronize_media()

    assert len(anki_mocker.get_added_media_files()) == 0
    assert not filecmp.cmp(f1=obsidian_image_file, f2=obsidian_image_file_duplicat, shallow=False)
    assert filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file, shallow=False)


def test_update_obsidian_media_in_anki(
    tmp_path: Path,
    srs_attachments_in_obsidian_folder_mock: Path,
    anki_mocker: AnkiMocker,
    some_test_image: PILImage,
    second_test_image: PILImage,
    media_synchronizer: MediaSynchronizer,
):
    anki_image_file = tmp_path / "img.jpg"
    second_test_image.save(anki_image_file)
    anki_mocker.set_media_files(files=[anki_image_file])

    srs_attachments_in_obsidian_folder_mock.mkdir(parents=True)
    obsidian_image_file = srs_attachments_in_obsidian_folder_mock / "img.jpg"
    obsidian_image_file_duplicat = tmp_path / "img-back.jpg"
    some_test_image.save(obsidian_image_file)
    shutil.copy(src=obsidian_image_file, dst=obsidian_image_file_duplicat)

    assert obsidian_image_file != obsidian_image_file_duplicat
    assert filecmp.cmp(f1=obsidian_image_file, f2=obsidian_image_file_duplicat, shallow=False)
    assert not filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file, shallow=False)
    assert not filecmp.cmp(f1=anki_image_file, f2=obsidian_image_file_duplicat, shallow=False)

    media_synchronizer.synchronize_media()

    assert len(anki_mocker.get_added_media_files()) == 1
    assert anki_mocker.get_added_media_files()[0] == obsidian_image_file
    assert filecmp.cmp(f1=obsidian_image_file, f2=obsidian_image_file_duplicat, shallow=False)
