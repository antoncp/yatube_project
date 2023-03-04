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
        src_str = re.compile(f'({value})', re.IGNORECASE)
        str_replaced = src_str.sub(r"<span class='highlight'>\1</span>", text)
    else:
        str_replaced = ''

    sentences = str_replaced.split('.')
    for num, sentence in enumerate(sentences):
        if value.lower() in sentence.lower():
            if len(sentences) - num > 1:
                str_replaced = '.'.join(sentences[num:num + 3]) + '...'
            else:
                str_replaced = str(sentence) + '...'
            break

    return mark_safe(str_replaced)
