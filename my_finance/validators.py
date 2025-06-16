"""
Custom validators for the personal finance application.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import re
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

def validate_amount(value: Any) -> None:
    """Validate monetary amount."""
    try:
        amount = Decimal(str(value))
        if amount < 0:
            raise ValidationError(_("Amount cannot be negative."))
        if amount > Decimal('999999999.99'):
            raise ValidationError(_("Amount exceeds maximum allowed value."))
    except (ValueError, TypeError) as e:
        logger.error(f"Amount validation failed: {str(e)}", exc_info=True)
        raise ValidationError(_("Invalid amount format."))

def validate_phone_number(value: str) -> None:
    """Validate phone number format."""
    if not re.match(r'^\+?1?\d{9,15}$', value):
        raise ValidationError(_("Invalid phone number format."))

def validate_email(value: str) -> None:
    """Validate email format."""
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
        raise ValidationError(_("Invalid email format."))

def validate_date_range(start_date: Any, end_date: Any) -> None:
    """Validate date range."""
    if start_date and end_date and start_date > end_date:
        raise ValidationError(_("Start date must be before end date."))

def validate_property_value(value: Any) -> None:
    """Validate property value."""
    try:
        amount = Decimal(str(value))
        if amount < 0:
            raise ValidationError(_("Property value cannot be negative."))
        if amount > Decimal('999999999999.99'):
            raise ValidationError(_("Property value exceeds maximum allowed value."))
    except (ValueError, TypeError) as e:
        logger.error(f"Property value validation failed: {str(e)}", exc_info=True)
        raise ValidationError(_("Invalid property value format."))

def validate_rental_amount(value: Any) -> None:
    """Validate rental amount."""
    try:
        amount = Decimal(str(value))
        if amount < 0:
            raise ValidationError(_("Rental amount cannot be negative."))
        if amount > Decimal('999999.99'):
            raise ValidationError(_("Rental amount exceeds maximum allowed value."))
    except (ValueError, TypeError) as e:
        logger.error(f"Rental amount validation failed: {str(e)}", exc_info=True)
        raise ValidationError(_("Invalid rental amount format."))

def sanitize_input(value: str) -> str:
    """Sanitize user input to prevent XSS."""
    if not isinstance(value, str):
        return str(value)
    # Remove potentially dangerous characters
    value = re.sub(r'[<>]', '', value)
    # Escape special characters
    value = value.replace('&', '&amp;')
    value = value.replace('"', '&quot;')
    value = value.replace("'", '&#x27;')
    return value

def validate_file_extension(value: Any, allowed_extensions: list) -> None:
    """Validate file extension."""
    if not hasattr(value, 'name'):
        raise ValidationError(_("Invalid file."))
    ext = value.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(_(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"))

def validate_file_size(value: Any, max_size: int) -> None:
    """Validate file size."""
    if not hasattr(value, 'size'):
        raise ValidationError(_("Invalid file."))
    if value.size > max_size:
        raise ValidationError(_(f"File size exceeds maximum allowed size of {max_size/1024/1024}MB.")) 