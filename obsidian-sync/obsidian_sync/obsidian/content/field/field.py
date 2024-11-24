import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from obsidian_sync.base_types.content import Field
from obsidian_sync.constants import SRS_NOTE_FIELD_IDENTIFIER_COMMENT, SRS_HEADER_TITLE_LEVEL
from obsidian_sync.markup_translator import MarkupTranslator


class ObsidianFieldFactory:
    @classmethod
    def _get_headers_and_paragraphs_from_file_text(cls, file_text: str) -> List[str]:
        headers_and_paragraph_matching_pattern = (
            f"{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}\n{SRS_HEADER_TITLE_LEVEL} (.*?)\n"
            f"([\s\S]*?)(?={SRS_NOTE_FIELD_IDENTIFIER_COMMENT}|\Z)"
        )
        note_body = cls._get_note_body(file_text=file_text)
        matches = re.findall(
            headers_and_paragraph_matching_pattern,
            f"{note_body}\n",  # ensures the matching string works even if file ends at field title
            re.DOTALL,
        )
        return matches

    @staticmethod
    def _get_note_body(file_text: str) -> str:
        yaml_frontmatter_pattern = r"^---[\s\S]*?---\s*"
        note_body = re.sub(yaml_frontmatter_pattern, "", file_text, count=1)
        return note_body


@dataclass
class ObsidianField(Field, ABC):
    def __post_init__(self):
        self._markup_translator = MarkupTranslator()

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @abstractmethod
    def to_obsidian_file_text(self) -> str:
        ...

    def set_from_markdown(self, markdown: str):
        self.text = markdown

    def set_from_html(self, html: str):
        markdown = self._markup_translator.translate_html_to_markdown(html=html)
        self.text = markdown

    def to_markdown(self) -> str:
        return self.text

    def to_html(self) -> str:
        html_text = self._markup_translator.translate_markdown_to_html(markdown=self.text)
        return html_text

    def _build_field_title(self) -> str:
        field_format_string = f"{SRS_NOTE_FIELD_IDENTIFIER_COMMENT}\n{SRS_HEADER_TITLE_LEVEL} {self.name}"
        return field_format_string
