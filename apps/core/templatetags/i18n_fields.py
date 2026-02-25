"""Template tags/filters for bilingual field access and language switching."""

import markdown as md
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

register = template.Library()


@register.filter(name="markdown")
def markdown_filter(value):
    """Render markdown text as HTML.

    Usage: {{ post.body|markdown }}
    """
    if not value:
        return ""
    return mark_safe(md.markdown(value, extensions=["extra", "nl2br"]))


@register.simple_tag
def trans_field(obj, field_name):
    """Return the Thai or English version of a field based on current language.

    Usage: {% trans_field tour "title" %}
    Returns tour.title_th if language is Thai, else tour.title
    """
    lang = get_language()
    if lang and lang.startswith("th"):
        th_value = getattr(obj, f"{field_name}_th", None)
        if th_value:
            return th_value
    return getattr(obj, field_name, "")


@register.filter(name="tf")
def trans_field_filter(obj, field_name):
    """Filter version of trans_field for use in template expressions.

    Usage: {{ tour|tf:"title" }}
    """
    lang = get_language()
    if lang and lang.startswith("th"):
        th_value = getattr(obj, f"{field_name}_th", None)
        if th_value:
            return th_value
    return getattr(obj, field_name, "")


@register.simple_tag(takes_context=True)
def switch_language_url(context, lang_code):
    """Build URL for switching to another language while staying on the same page.

    Usage: {% switch_language_url "en" %}
    Replaces current language prefix with the target language prefix.
    """
    request = context.get("request")
    if not request:
        return f"/{lang_code}/"

    path = request.path
    # Strip existing language prefix
    for code, _name in settings.LANGUAGES:
        prefix = f"/{code}/"
        if path.startswith(prefix):
            path = path[len(prefix) - 1 :]  # Keep leading /
            break

    return f"/{lang_code}{path}"
