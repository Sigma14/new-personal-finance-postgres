from django.template import Library
import logging

register = Library()
logger = logging.getLogger(__name__)

# Filter to fetch values from dictionaries
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)