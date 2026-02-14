from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def items(dictionary):
    """Get dictionary items for iteration"""
    if dictionary:
        return dictionary.items()
    return []

