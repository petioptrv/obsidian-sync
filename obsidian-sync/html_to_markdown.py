from .markdownify.markdownify import ATX, MarkdownConverter


class HTMLToMarkdown:
    def __init__(self):
        self._markdown_converter = MarkdownConverter(heading_style=ATX)

    def convert(self, html: str) -> str:
        return self._markdown_converter.convert(html=html)
