import re
import shutil
import urllib.parse
from pathlib import Path
from typing import Dict, Tuple

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.base_types.content import LinkedAttachment
from obsidian_sync.constants import ATTACHMENT_FILE_SUFFIXES
from obsidian_sync.file_utils import check_files_are_identical
from obsidian_sync.obsidian.obsidian_config import ObsidianConfig


class ObsidianAttachmentsManager:
    def __init__(
        self,
        addon_config: AddonConfig,
        obsidian_config: ObsidianConfig,
    ):
        self._addon_config = addon_config
        self._obsidian_config = obsidian_config

    def attachment_paths_from_file_text(self, file_text: str, note_path: Path) -> Dict[str, Path]:
        # source: https://stackoverflow.com/a/44227600/6793798
        attachments_matcher = "|\\".join(ATTACHMENT_FILE_SUFFIXES)
        markdown_attachment_pattern = rf"""!?\[[^\]]*\]\((.*?(?:{attachments_matcher}))\s*("(?:.*[^"])")?\s*\)"""
        attachment_paths = dict()

        for quoted_path_string, optional_part in re.findall(markdown_attachment_pattern, file_text, re.DOTALL):
            path_string = urllib.parse.unquote(string=quoted_path_string)
            attachment_paths[path_string] = self._resolve_attachment_path(
                base_path=Path(path_string), note_path=note_path, not_exist_ok=False
            )

        return attachment_paths

    def ensure_attachment_is_in_obsidian(self, attachment: LinkedAttachment, note_path: Path) -> Tuple[str, Path]:
        obsidian_attachment_path = self._resolve_attachment_path(
            base_path=Path(attachment.path.name), note_path=note_path, not_exist_ok=True
        )
        obsidian_file_text_path = str(obsidian_attachment_path.relative_to(self._obsidian_config.vault_folder))

        if (
            not obsidian_attachment_path.exists()
            or not check_files_are_identical(first=attachment.path, second=obsidian_attachment_path)
        ):
            obsidian_attachment_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src=attachment.path, dst=obsidian_attachment_path)

        return obsidian_file_text_path, obsidian_attachment_path

    def _resolve_attachment_path(self, base_path: Path, note_path: Path, not_exist_ok: bool) -> Path:
        """If the attachment file name is unique in the vault or if the file is
        in the same folder as the note, Obsidian will use only the file name.

        If there are duplicates in folders other than the note's folder, Obsidian will
        use paths relative to the vault directory."""

        if base_path.name == str(base_path):
            if (note_path / base_path.name).exists():
                attachment_path = note_path / base_path
            else:
                try:
                    attachment_path = next(
                        self._addon_config.obsidian_vault_path.rglob(pattern=str(base_path))
                    )
                except StopIteration:  # does not exist in Obsidian
                    if not_exist_ok:
                        default_attachment_folder = self._get_default_attachment_folder(note_path=note_path)
                        attachment_path = default_attachment_folder / base_path
                    else:
                        raise
        else:  # path relative to vault directory
            attachment_path = self._addon_config.obsidian_vault_path / base_path

        return attachment_path

    def _get_default_attachment_folder(self, note_path: Path) -> Path:
        return self._obsidian_config.srs_attachments_folder
