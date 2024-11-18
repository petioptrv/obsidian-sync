from markdownify import ATX
from markdown import markdown

from obsidian_sync.markup_translator import ExtendedHTMLToMarkdownConverter


def test_adapted_markdown_converter_unescape():
    amc = ExtendedHTMLToMarkdownConverter(heading_style=ATX)

    original_texts = [
        "This is a test *text* with _underscores_ and special characters: <&>",
        "123. Example text with 4) a numbered item.",
        "Normal text without special escaping."
    ]

    for original in original_texts:
        escaped = amc.escape(original)
        unescaped = amc.unescape(escaped)
        assert unescaped == original


def test_formating_html_to_be_translatable():
    html_text = ("<br><br>This is one paragraph<br><br>and another one"
                 "")
    markdown_converter = ExtendedHTMLToMarkdownConverter(heading_style=ATX)

    markdown_from_html = markdown_converter.convert(html=html_text)
    html_from_markdown = markdown(text=markdown_from_html)
    markdown_from_html = markdown_converter.convert(html=html_from_markdown)

    final_html_from_markdown = markdown(text=markdown_from_html)

    markdown_from_final_html = markdown_converter.convert(html=final_html_from_markdown)

    assert final_html_from_markdown == markdown(text=markdown_from_final_html)


def test_formating_markdown_to_be_translatable():
    markdown_text = """

This is one paragraph

and another one
    """
    markdown_converter = ExtendedHTMLToMarkdownConverter(heading_style=ATX)

    html_from_markdown = markdown(text=markdown_text)
    markdown_from_html = markdown_converter.convert(html=html_from_markdown)
    html_from_markdown = markdown(text=markdown_from_html)

    final_markdown_from_html = markdown_converter.convert(html=html_from_markdown)

    html_from_markdown = markdown(text=final_markdown_from_html)

    assert final_markdown_from_html == markdown_converter.convert(html=html_from_markdown)


