from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Return dictionary[key], falling back to key itself if not found."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, key)
    return key
