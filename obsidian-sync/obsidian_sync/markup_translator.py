from markdownify import ATX, MarkdownConverter
from markdown import markdown as to_markdown


class MarkupTranslator:
    def __init__(self):
        self._markdown_converter = MarkdownConverter(heading_style=ATX)

    def translate_html_to_markdown(self, html: str) -> str:
        return self._markdown_converter.convert(html=html)

    @staticmethod
    def translate_markdown_to_html(markdown: str) -> str:
        return to_markdown(text=markdown)
