from django import template
from django.utils.html import format_html, format_html_join

register = template.Library()


@register.simple_tag
def stars(value):
    if value is None:
        return format_html('<span class="meta">Not yet rated</span>')
    count = min(5, max(0, round(float(value))))
    icons = format_html_join(
        "",
        '<span class="{}" aria-hidden="true">★</span>',
        (("star-full" if i < count else "star-empty",) for i in range(5)),
    )
    return format_html(
        '<span class="stars" role="img" aria-label="{} out of 5 stars">{}</span>',
        round(float(value), 2),
        icons,
    )
