# screen_app/templatetags/__init__.py
# (empty file, just needs to exist)

# screen_app/templatetags/custom_filters.py
from django import template
import json

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''
    
@register.filter
def jsonify(value):
    return json.dumps(value)
    