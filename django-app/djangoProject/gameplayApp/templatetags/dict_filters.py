from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Get dictionary value by key"""
    return dictionary.get(key)