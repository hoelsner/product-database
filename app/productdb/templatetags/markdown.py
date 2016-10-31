import markdown
from django import template
from django.template.defaultfilters import stringfilter, safe

register = template.Library()


@register.filter
@stringfilter
def render_markdown(value):
    return safe(markdown.markdown(value, output_format="html5", safe=False))
