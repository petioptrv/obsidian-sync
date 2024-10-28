from markdownify import markdownify
from markdown import markdown


def test_formating_html_to_be_translatable():
    html_text = "<br><br>This is one paragraph<br><br>and another one"

    markdown_from_html = markdownify(html=html_text)
    html_from_markdown = markdown(text=markdown_from_html)
    markdown_from_html = markdownify(html=html_from_markdown)

    final_html_from_markdown = markdown(text=markdown_from_html)

    markdown_from_final_html = markdownify(html=final_html_from_markdown)

    assert final_html_from_markdown == markdown(text=markdown_from_final_html)


def test_formating_markdown_to_be_translatable():
    markdown_text = """

This is one paragraph

and another one
    """

    html_from_markdown = markdown(text=markdown_text)
    markdown_from_html = markdownify(html=html_from_markdown)
    html_from_markdown = markdown(text=markdown_from_html)

    final_markdown_from_html = markdownify(html=html_from_markdown)

    html_from_markdown = markdown(text=final_markdown_from_html)

    assert final_markdown_from_html == markdownify(html=html_from_markdown)


