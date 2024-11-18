import re

from bs4 import Tag
from markdownify import ATX, MarkdownConverter as HTMLToMarkdownConverter
from markdown import Markdown as MarkdownToHTMLConverter
from markdown.postprocessors import Postprocessor as MarkdownToHTMLPostprocessor


class ExtendedHTMLToMarkdownConverter(HTMLToMarkdownConverter):
    def __getattr__(self, item):
        item = item.replace("-", "_")
        return self.__getattribute__(item)

    def convert_pre(self, el, text, convert_as_inline):  # adapted for use with Anki
        if not text:
            return ""
        text = text.strip()
        code_language = self.options["code_language"]

        if self.options["code_language_callback"]:
            code_language = self.options["code_language_callback"](el) or code_language

        return "\n```%s\n%s\n```\n" % (code_language, text)

    def convert_anki_mathjax(self, el: Tag, text: str, convert_as_inline: bool) -> str:
        text = self.unescape(text=text)
        block = el.attrs.get("block", "false")
        punctuation = "$$" if block == "true" else "$"
        return f"{punctuation}{text}{punctuation}"

    def unescape(self, text):
        if not text:
            return ""
        if self.options["escape_underscores"]:
            text = text.replace(r"\_", "_")
        if self.options["escape_asterisks"]:
            text = text.replace(r"\*", "*")
        if self.options["escape_misc"]:
            text = re.sub(r"\\([\\&<`[>~#=+|-])", r"\1", text)
            text = re.sub(r"([0-9])\\([.)])", r"\1\2", text)
        return text
    
    
class ExtendedMarkdownToHTMLMathPostprocessor(MarkdownToHTMLPostprocessor):
    def run(self, text):
        block_equation_pattern = r"\$\$(.+?)\$\$"
        block_equation_repl = r'<anki-mathjax block="true">\1</anki-mathjax>'
        in_line_equation_pattern = r"\$(.+?)\$"
        in_line_equation_repl = r"<anki-mathjax>\1</anki-mathjax>"

        text = re.sub(  # should be matched first
            pattern=block_equation_pattern,
            repl=block_equation_repl,
            string=text,
            flags=re.DOTALL,  # allows spanning multiple lines
        )
        text = re.sub(
            pattern=in_line_equation_pattern,
            repl=in_line_equation_repl,
            string=text,
        )
        return text


class MarkupTranslator:
    def __init__(self):
        self._html_to_markdown_converter = ExtendedHTMLToMarkdownConverter(
            heading_style=ATX,
            convert_as_inline=True,
        )
        self._markdown_to_html_converter = MarkdownToHTMLConverter(extensions=["fenced_code"])
        self._markdown_to_html_converter.postprocessors.register(
            item=ExtendedMarkdownToHTMLMathPostprocessor(md=self._markdown_to_html_converter),
            name="extended_markdown_to_html",
            priority=10,
        )

    def sanitize_markdown(self, markdown: str) -> str:
        """
        Ensures that the Markdown text can be converted to HTML and back to
        the original Markdown.
        """
        html_from_markdown = self._markdown_to_html_converter.convert(source=markdown)
        markdown_from_html = self._html_to_markdown_converter.convert(html=html_from_markdown)
        html_from_markdown = self._markdown_to_html_converter.convert(source=markdown_from_html)
        markdown_from_html = self._html_to_markdown_converter.convert(html=html_from_markdown)
        return markdown_from_html

    def sanitize_html(self, html: str) -> str:
        """
        Ensures that the HTML text can be converted to Makrdown and back to
        the original HTML.
        """
        markdown_from_html = self._html_to_markdown_converter.convert(html=html)
        html_from_markdown = self._markdown_to_html_converter.convert(source=markdown_from_html)
        markdown_from_html = self._html_to_markdown_converter.convert(html=html_from_markdown)
        html_from_markdown = self._markdown_to_html_converter.convert(source=markdown_from_html)
        return html_from_markdown

    def translate_html_to_markdown(self, html: str) -> str:
        return self._html_to_markdown_converter.convert(html=html)

    def translate_markdown_to_html(self, markdown: str) -> str:
        return self._markdown_to_html_converter.convert(source=markdown)

