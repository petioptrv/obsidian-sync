# -*- coding: utf-8 -*-
# Obsidian Sync Add-on for Anki
#
# Copyright (C)  2024 Petrov P.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <mailto:petioptrv@icloud.com>.
#
# Any modifications to this file must keep this entire header intact.

import re
from textwrap import fill

from markdown_extensions.fenced_code import FencedCodeExtension
from markdown_extensions.wikilinks import WikiLinkExtension
from markdownify import ATX, MarkdownConverter as HTMLToMarkdownConverter
from markdown import Markdown as MarkdownToHTMLConverter
from markdown.postprocessors import Postprocessor as MarkdownToHTMLPostprocessor


class MarkupTranslator:
    def __init__(self):
        self._html_to_markdown_converter = ExtendedHTMLToMarkdownConverter(
            heading_style=ATX,
            convert_as_inline=True,
            escape_misc=False,
        )
        fenced_code = FencedCodeExtension()
        wikilinks = WikiLinkExtension()
        self._markdown_to_html_converter = MarkdownToHTMLConverter(
            extensions=[fenced_code, wikilinks], output_format="html"
        )
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

    @staticmethod
    def to_markdown_link(text: str, url: str) -> str:
        return f"[{text}]({url})"


class ExtendedHTMLToMarkdownConverter(HTMLToMarkdownConverter):
    def convert_p(self, el, text, convert_as_inline):
        if convert_as_inline:
            return text
        if self.options["wrap"]:
            text = fill(text,
                        width=self.options["wrap_width"],
                        break_long_words=False,
                        break_on_hyphens=False)
        return "\n%s\n" % text if text else ""

    def convert_pre(self, el, text, convert_as_inline):  # adapted for use with Anki
        if not text:
            return ""
        text = text.strip()
        code_language = self.options["code_language"]

        if self.options["code_language_callback"]:
            code_language = self.options["code_language_callback"](el) or code_language

        return "\n```%s\n%s\n```\n" % (code_language, text)

    def process_text(self, el):
        text = super().process_text(el=el)
        text = re.sub(  # Convert block LaTeX: \[ ... \] → $$ ... $$
            r"\\\[(.*?)\\\]", r"$$\1$$", text, flags=re.DOTALL
        )
        text = re.sub(  # Convert inline LaTeX: \( ... \) → $ ... $
            r"\\\((.*?)\\\)", r"$\1$", text, flags=re.DOTALL
        )
        return text

    def escape(self, text):
        if not text:
            return ""

        def escape_non_latex(part):
            if self.options["escape_misc"]:
                part = re.sub(r"([\\&<`[>~#=+|-])", r"\\\1", part)
                part = re.sub(r"([0-9])([.)])", r"\1\\\2", part)
            if self.options["escape_asterisks"]:
                part = part.replace("*", r"\*")
            if self.options["escape_underscores"]:
                part = part.replace("_", r"\_")
            return part

        latex_pattern = r"(\$.*?\$|\$\$.*?\$\$|\\\(.*?\\\)|\\\[.*?\\\])"
        parts = re.split(latex_pattern, text)

        escaped = "".join(
            part
            if re.match(latex_pattern, part)
            else escape_non_latex(part)
            for part in parts
        )

        return escaped

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
        block_equation_repl = r'\[\1\]'
        in_line_equation_pattern = r"\$(.+?)\$"
        in_line_equation_repl = r"\(\1\)"

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

