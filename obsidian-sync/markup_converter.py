from .markdownify.markdownify import ATX, MarkdownConverter
from .markdown.markdown import markdown as to_markdown


class MarkupConverter:
    def __init__(self):
        self._markdown_converter = MarkdownConverter(heading_style=ATX)

    def convert_html_to_markdown(self, html: str) -> str:
        return self._markdown_converter.convert(html=html)

    def convert_markdown_to_html(self, markdown: str) -> str:
        return to_markdown(text=markdown)
