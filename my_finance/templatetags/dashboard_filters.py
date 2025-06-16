"""
Custom template filters for dashboard calculations.
"""
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def div(value, arg):
    """Divide value by argument."""
    try:
        return Decimal(value) / Decimal(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return Decimal('0')

@register.filter
def mul(value, arg):
    """Multiply value by argument."""
    try:
        return Decimal(value) * Decimal(arg)
    except (ValueError, TypeError):
        return Decimal('0')

@register.filter
def sub(value, arg):
    """Subtract argument from value."""
    try:
        return Decimal(value) - Decimal(arg)
    except (ValueError, TypeError):
        return Decimal('0')

@register.filter
def add(value, arg):
    """Add value and argument."""
    try:
        return Decimal(value) + Decimal(arg)
    except (ValueError, TypeError):
        return Decimal('0')

@register.filter
def percentage(value, total):
    """Calculate percentage of total."""
    try:
        if not total:
            return Decimal('0')
        return (Decimal(value) / Decimal(total)) * Decimal('100')
    except (ValueError, TypeError, ZeroDivisionError):
        return Decimal('0')

@register.filter
def currency(value):
    """Format value as currency."""
    try:
        return f"${Decimal(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def percentage(value, total):
    """Calculate percentage of value relative to total."""
    try:
        if not total:
            return 0
        return (Decimal(str(value)) / Decimal(str(total))) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def format_currency(value):
    """Format value as currency."""
    try:
        return f"${Decimal(str(value)):,.2f}"
    except (ValueError, TypeError):
        return value

@register.filter
def status_class(value):
    """Return CSS class based on status."""
    status_classes = {
        'pending': 'pending',
        'completed': 'completed',
        'overdue': 'overdue',
        'paid': 'completed',
        'unpaid': 'overdue'
    }
    return status_classes.get(value.lower(), '')

@register.filter
def trend_indicator(value):
    """Return trend indicator based on value."""
    try:
        value = Decimal(str(value))
        if value > 0:
            return '↑'
        elif value < 0:
            return '↓'
        return '→'
    except (ValueError, TypeError):
        return '→'

@register.filter
def trend_class(value):
    """Return CSS class based on trend value."""
    try:
        value = Decimal(str(value))
        if value > 0:
            return 'positive'
        elif value < 0:
            return 'negative'
        return 'neutral'
    except (ValueError, TypeError):
        return 'neutral' 