import os

from django import template

register = template.Library()


def _to_str(value):
    if value is None:
        return ""
    return str(value)


@register.filter(name="filename")
def filename(value):
    """Return the base file name from a path-like string."""
    return os.path.basename(_to_str(value))
