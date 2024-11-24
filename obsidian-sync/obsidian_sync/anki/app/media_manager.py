from pathlib import Path
from typing import List

import aqt

from obsidian_sync.base_types.content import LinkedAttachment


class AnkiMediaManager:
    @property
    def media_directory(self) -> Path:
        return Path(aqt.mw.col.media.dir())

    def get_media_file_paths(self, model_id: int, field_text: str) -> List[Path]:
        file_paths = [
            self.media_directory / file_name
            for file_name in aqt.mw.col.media.files_in_str(mid=model_id, string=field_text)
        ]
        return file_paths

    def ensure_attachment_is_in_anki(self, attachment: LinkedAttachment) -> Path:
        media = aqt.mw.col.media
        if not media.have(fname=attachment.path.name):
            media.add_file(path=attachment.path)
        attachment_path = self.media_directory / attachment.path.name
        return attachment_path
