from django.template import Library
import logging

register = Library()
logger = logging.getLogger(__name__)

# Filter to fetch values from dictionaries
@register.filter
def get_item(dictionary, key):
    if key not in dictionary:
        return 0
    else:
        return dictionary.get(key)

# Fetch list values
@register.filter
def get_list_item(list, index):
    try:
        value = list[index]
    except:
        value = '0.0'
    return value