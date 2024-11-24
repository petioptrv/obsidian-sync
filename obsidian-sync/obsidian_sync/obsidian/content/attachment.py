import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import List

from obsidian_sync.base_types.content import LinkedAttachment
from obsidian_sync.obsidian.attachments_manager import ObsidianAttachmentsManager


@dataclass
class ObsidianLinkedAttachment(LinkedAttachment):
    _obsidian_file_text_path: str
    _obsidian_attachments_manager: ObsidianAttachmentsManager

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_obsidian_file_text(
        cls,
        file_text: str,
        note_path: Path,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
    ) -> List["ObsidianLinkedAttachment"]:
        attachment_paths = obsidian_attachments_manager.attachment_paths_from_file_text(
            file_text=file_text, note_path=note_path
        )
        attachments = [
            cls(
                path=path,
                _obsidian_file_text_path=obsidian_file_text_path,
                _obsidian_attachments_manager=obsidian_attachments_manager,
            )
            for obsidian_file_text_path, path in attachment_paths.items()
        ]
        return attachments

    @classmethod
    def from_attachment(
        cls,
        attachment: LinkedAttachment,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        note_path: Path,
    ) -> "ObsidianLinkedAttachment":
        obsidian_file_text_path, obsidian_attachment_path = (
            obsidian_attachments_manager.ensure_attachment_is_in_obsidian(
                attachment=attachment, note_path=note_path
            )
        )
        return cls(
            path=obsidian_attachment_path,
            _obsidian_file_text_path=obsidian_file_text_path,
            _obsidian_attachments_manager=obsidian_attachments_manager,
        )

    def to_field_text(self) -> str:
        return str(self.path)

    def to_obsidian_file_text(self) -> str:
        path_quote = urllib.parse.quote(string=self._obsidian_file_text_path)
        return path_quote
