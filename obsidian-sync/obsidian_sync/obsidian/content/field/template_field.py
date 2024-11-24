from dataclasses import dataclass
from typing import List

from obsidian_sync.addon_config import AddonConfig
from obsidian_sync.base_types.content import TemplateField
from obsidian_sync.constants import OBSIDIAN_LINK_URL_FIELD_NAME
from obsidian_sync.obsidian.content.field.field import ObsidianFieldFactory, ObsidianField


class ObsidianTemplateFieldFactory(ObsidianFieldFactory):
    @staticmethod
    def from_fields(fields: List[TemplateField]) -> List["ObsidianTemplateField"]:
        fields = [
            ObsidianTemplateField.from_field(field=field)
            if field.name != OBSIDIAN_LINK_URL_FIELD_NAME
            else ObsidianLinkURLTemplateField.from_field(field=field)
            for field in fields
        ]
        return fields

    def from_obsidian_file_text(
        self, file_text: str, addon_config: AddonConfig
    ) -> List["ObsidianTemplateField"]:
        headers_and_paragraphs = self._get_headers_and_paragraphs_from_file_text(file_text=file_text)

        fields = [
            ObsidianTemplateField(name=header.strip(), text=paragraph.strip())
            for header, paragraph in headers_and_paragraphs
        ]

        if addon_config.add_obsidian_url_in_anki:
            fields.append(
                ObsidianLinkURLTemplateField(name=OBSIDIAN_LINK_URL_FIELD_NAME, text="")
            )

        return fields


@dataclass
class ObsidianTemplateField(TemplateField, ObsidianField):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_field(cls, field: TemplateField) -> "ObsidianTemplateField":
        markdown_text = field.to_markdown()
        return cls(name=field.name, text=markdown_text)

    def to_obsidian_file_text(self) -> str:
        field_title = self._build_field_title()
        field_text = f"{field_title}\n\n{self.text}\n\n"
        return field_text


@dataclass
class ObsidianLinkURLTemplateField(ObsidianTemplateField):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def to_obsidian_file_text(self) -> str:
        return ""
