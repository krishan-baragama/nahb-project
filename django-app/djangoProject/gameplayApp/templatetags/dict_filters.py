from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Get dictionary value by key"""
    return dictionary.get(key)

@register.filter
def items(dictionary):
    """Get dictionary items for iteration"""
    if dictionary:
        return dictionary.items()
    return []