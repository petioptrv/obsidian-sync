import re
from dataclasses import dataclass
from typing import List

from obsidian_sync.base_types.content import Image, Field, Content, Properties
from obsidian_sync.markup_translator import MarkupTranslator


@dataclass
class AnkiContent(Content):
    properties: "AnkiProperties"
    fields: List["AnkiField"]


@dataclass
class AnkiProperties(Properties):
    pass


@dataclass
class AnkiField(Field):
    _markup_translator: MarkupTranslator

    def to_markdown(self) -> str:
        raise NotImplementedError

    def to_html(self) -> str:
        return self.text


@dataclass
class AnkiImage(Image):
    @staticmethod
    def _html_image_paths_from_note_text(file_text: str) -> List[str]:
        # source: https://stackoverflow.com/a/37646739/6793798
        html_image_pattern = r"""<img\b(?=\s)(?=(?:[^>=]|='[^']*'|="[^"]*"|=[^'"][^\s>]*)*?\ssrc=['"]([^"]*)['"]?)(?:[^>=]|='[^']*'|="[^"]*"|=[^'"\s]*)*"\s?\/?>"""
        image_paths = re.findall(html_image_pattern, file_text, re.DOTALL)
        return image_paths
