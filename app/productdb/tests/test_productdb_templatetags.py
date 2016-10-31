from django.template import Context
from django.template import Template


def test_custom_markdown_filter():
    test_context_variable = """\
My Markdown Text
================

A paragraph with **bold** text and *italic* text.


Another paragraph. <strong>HTML Tag</strong>
"""
    expected_result = """\
<h1>My Markdown Text</h1>
<p>A paragraph with <strong>bold</strong> text and <em>italic</em> text.</p>
<p>Another paragraph. <strong>HTML Tag</strong></p>"""

    t = Template("{% load markdown %}{{ markdown_content|render_markdown }}")
    c = Context({"markdown_content": test_context_variable})
    result = t.render(c)

    assert result == expected_result

