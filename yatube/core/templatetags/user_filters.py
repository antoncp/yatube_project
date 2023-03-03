import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})


@register.filter()
def highlight(text, value):
    if text is not None:
        text = str(text)
        src_str = re.compile(value, re.IGNORECASE)
        str_replaced = src_str.sub(f"<span class=\"highlight\">{value}</span>", text)
    else:
        str_replaced = ''

    return mark_safe(str_replaced)