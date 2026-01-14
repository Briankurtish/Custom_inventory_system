from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return ''

@register.filter
def dict_get(dictionary, key):
    """Get value from dictionary by key"""
    try:
        return dictionary.get(key, '')
    except (AttributeError, TypeError):
        return ''
