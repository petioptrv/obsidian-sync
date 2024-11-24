import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.base_types.content import NoteField
from obsidian_sync.constants import OBSIDIAN_LINK_URL_FIELD_NAME
from obsidian_sync.obsidian.attachments_manager import ObsidianAttachmentsManager
from obsidian_sync.obsidian.content.attachment import ObsidianLinkedAttachment
from obsidian_sync.obsidian.content.field.field import ObsidianFieldFactory, ObsidianField


class ObsidianNoteFieldFactory(ObsidianFieldFactory):
    @staticmethod
    def from_fields(
        fields: List[NoteField],
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        note_path: Path,
    ) -> List["ObsidianNoteField"]:
        obsidian_fields = [
            ObsidianNoteField.from_field(
                field=field_,
                obsidian_attachments_manager=obsidian_attachments_manager,
                note_path=note_path,
            )
            if field_.name != OBSIDIAN_LINK_URL_FIELD_NAME
            else ObsidianLinkURLNoteField.from_field(
                field=field_,
                obsidian_attachments_manager=obsidian_attachments_manager,
                note_path=note_path,
            )
            for field_ in fields
        ]
        return obsidian_fields

    @classmethod
    def from_obsidian_file_text(
        cls,
        file_text: str,
        note_path: Path,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        addon_config: AddonConfig,
    ) -> List["ObsidianNoteField"]:
        headers_and_paragraphs = cls._get_headers_and_paragraphs_from_file_text(file_text=file_text)
        fields = []

        for header, paragraph in headers_and_paragraphs:
            text = paragraph.strip()
            attachments = ObsidianLinkedAttachment.from_obsidian_file_text(
                file_text=text, note_path=note_path, obsidian_attachments_manager=obsidian_attachments_manager
            )
            for attachment in attachments:
                text = text.replace(
                    attachment.to_obsidian_file_text(), attachment.to_field_text()
                )
            fields.append(
                ObsidianNoteField(
                    name=header.strip(),
                    text=text,
                    attachments=attachments,
                )
            )

        if addon_config.add_obsidian_url_in_anki:
            vault_name = addon_config.obsidian_vault_path.name
            note_path_relative_to_vault = note_path.relative_to(addon_config.obsidian_vault_path)
            obsidian_url = urllib.parse.quote(
                f"obsidian://open?vault={vault_name}&file={note_path_relative_to_vault}"
            )
            fields.append(
                ObsidianLinkURLNoteField(name=OBSIDIAN_LINK_URL_FIELD_NAME, text=obsidian_url)
            )

        return fields


@dataclass
class ObsidianNoteField(NoteField, ObsidianField):
    attachments: List["ObsidianLinkedAttachment"]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_field(
        cls,
        field: NoteField,
        obsidian_attachments_manager: ObsidianAttachmentsManager,
        note_path: Path,
    ) -> "ObsidianNoteField":
        markdown_text = field.to_markdown()

        obsidian_attachments = []
        for attachment in field.attachments:
            obsidian_attachment = ObsidianLinkedAttachment.from_attachment(
                attachment=attachment,
                obsidian_attachments_manager=obsidian_attachments_manager,
                note_path=note_path,
            )
            obsidian_attachments.append(obsidian_attachment)
            markdown_text = markdown_text.replace(
                attachment.to_field_text(), obsidian_attachment.to_field_text()
            )

        return cls(
            name=field.name,
            text=markdown_text,
            attachments=obsidian_attachments,
        )

    def to_obsidian_file_text(self) -> str:
        field_title = self._build_field_title()
        field_text = f"{field_title}\n\n{self.text}\n\n"
        for attachment in self.attachments:
            field_text = field_text.replace(
                attachment.to_field_text(), attachment.to_obsidian_file_text()
            )
        return field_text


@dataclass
class ObsidianLinkURLNoteField(ObsidianNoteField):
    attachments: List["ObsidianLinkedAttachment"] = field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def to_obsidian_file_text(self) -> str:
        return ""
