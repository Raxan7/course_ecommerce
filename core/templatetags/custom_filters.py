from django import template
from django.utils.html import escape

register = template.Library()

@register.filter
def replace_apostrophe(value):
    return value.replace("'", "&#39;")

@register.filter
def safe_apostrophe(value):
    return escape(value)