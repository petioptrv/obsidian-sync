import pytest

from obsidian_sync.markup_translator import MarkupTranslator


def test_convert_html_with_latex_in_line_math_statement_to_markdown():
    markup_translator = MarkupTranslator()

    html_text = "<p>Some in-line math \\(x = 1\\)</p>"
    expected_markdown_text = "\nSome in-line math $x = 1$\n"
    markdown_text = markup_translator.translate_html_to_markdown(html=html_text)

    assert markdown_text == expected_markdown_text


def test_convert_html_with_latex_block_math_statement_to_markdown():
    markup_translator = MarkupTranslator()

    html_text = "<p>Some math block \\[x = 1\\]</p>"
    expected_markdown_text = "\nSome math block $$x = 1$$\n"
    markdown_text = markup_translator.translate_html_to_markdown(html=html_text)

    assert markdown_text == expected_markdown_text


def test_convert_html_with_code_block_to_markdown():
    markup_translator = MarkupTranslator()

    in_line_code = "code variable"
    block_code = "block code"
    html_text = f"""<p>Some text with an in-line <code>{in_line_code}</code>&nbsp;</p>
<pre><code>{block_code}
</code></pre>
<p>and a final line</p>"""
    expected_markdown = f"""
Some text with an in-line `{in_line_code}`\xa0


```
{block_code}
```


and a final line
"""

    markdown_text = markup_translator.translate_html_to_markdown(html=html_text)

    assert markdown_text == expected_markdown


def test_convert_obsidian_url_markdown_to_html():
    markup_translator = MarkupTranslator()

    markdown_text = "[Obsidian URL](obsidian://open?vault=Test%20Vault&file=Test%20File)"
    expected_html = """<p><a href="obsidian://open?vault=Test%20Vault&amp;file=Test%20File">Obsidian URL</a></p>"""

    html = markup_translator.translate_markdown_to_html(markdown=markdown_text)

    assert html == expected_html


def test_sanitizing_html_with_latex_in_line_math_statement():
    markup_translator = MarkupTranslator()

    original_html_text = "<p>Some in-line math \\(x = 1\\)</p>"
    sanitized_html_text = markup_translator.sanitize_html(html=original_html_text)

    assert sanitized_html_text == original_html_text


def test_sanitizing_html_with_latex_block_math_statement():
    markup_translator = MarkupTranslator()

    original_html_text = r"<p>Some in-line math \[x = 1\]</p>"
    sanitized_html_text = markup_translator.sanitize_html(html=original_html_text)

    assert sanitized_html_text == original_html_text


def test_sanitizing_html_with_url_as_the_displayed_text():
    markup_translator = MarkupTranslator()

    original_html_text = (
        "<p>This is a link: "
        "<a href=\"https://www.youtube.com/watch?v=KuXjwB4LzSA\">https://www.youtube.com/watch?v=KuXjwB4LzSA</a></p>"
    )
    sanitized_html_text = markup_translator.sanitize_html(html=original_html_text)

    assert sanitized_html_text == original_html_text


def test_escape_special_html_characters():
    markup_translator = MarkupTranslator()

    html_text = "<p>Some &lt;escaped&gt; HTML &amp; special characters</p>"
    expected_markdown = "\nSome <escaped> HTML & special characters\n"
    markdown_text = markup_translator.translate_html_to_markdown(html=html_text)

    assert markdown_text == expected_markdown


def test_nested_inline_code_blocks():
    markup_translator = MarkupTranslator()

    html_text = "<p>Code block with nested `<code>tags</code>`</p>"
    expected_markdown = "\nCode block with nested ``tags``\n"
    markdown_text = markup_translator.translate_html_to_markdown(html=html_text)

    assert markdown_text == expected_markdown
    assert markup_translator.translate_markdown_to_html(markdown=markdown_text) == html_text


def test_misaligned_latex_escape():
    markup_translator = MarkupTranslator()

    html_text = "<p>Unmatched LaTeX \\(x = 1</p>"
    expected_markdown = "\nUnmatched LaTeX \\(x = 1\n"
    markdown_text = markup_translator.translate_html_to_markdown(html=html_text)

    assert markdown_text == expected_markdown


@pytest.mark.skip
def test_convert_wikilinks_reference_to_html():
    markup_translator = MarkupTranslator()

    obsidian_url_with_section = "obsidian://open?vault=Test%20Vault&file=Test%20File%23Heading"
    alt_text = "alt text"
    markdown_text = f"Some [[{obsidian_url_with_section}|{alt_text}]] to convert"
    expected_html = f"""<p>Some <a href="{obsidian_url_with_section}" class="wikilink">{alt_text}</a> to convert</p>"""

    html = markup_translator.translate_markdown_to_html(markdown=markdown_text)

    assert html == expected_html

    raise NotImplementedError
