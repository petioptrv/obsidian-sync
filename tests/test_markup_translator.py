from obsidian_sync.markup_translator import MarkupTranslator


def test_convert_html_with_latex_in_line_math_statement_to_markdown():
    markup_translator = MarkupTranslator()

    html_text = "<p>Some in-line math \\(x = 1\\)</p>"
    expected_markdown_text = "\nSome in\\-line math $x = 1$\n"
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
Some text with an in\\-line `{in_line_code}`\xa0


```
{block_code}
```


and a final line
"""

    markdown_text = markup_translator.translate_html_to_markdown(html=html_text)

    assert markdown_text == expected_markdown


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

