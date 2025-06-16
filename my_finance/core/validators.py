"""
Validator layer for the finance application.
This module handles input validation and data sanitization.
"""
from typing import Dict, Any
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
import logging

logger = logging.getLogger(__name__)

class BaseValidator:
    """Base validator class with common functionality."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]):
        """
        Validate that all required fields are present.
        
        Args:
            data: The data to validate
            required_fields: List of required field names
            
        Raises:
            ValidationError: If any required field is missing
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def sanitize_string(self, value: str) -> str:
        """
        Sanitize a string value.
        
        Args:
            value: The string to sanitize
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        return re.sub(r'[<>]', '', value.strip())

class PropertyValidator(BaseValidator):
    """Validator for property-related data."""
    
    def validate_property_data(self, data: Dict[str, Any]):
        """
        Validate property data.
        
        Args:
            data: Property data to validate
            
        Raises:
            ValidationError: If data is invalid
        """
        required_fields = ['name', 'address', 'property_type']
        self.validate_required_fields(data, required_fields)
        
        # Validate string fields
        data['name'] = self.sanitize_string(data['name'])
        data['address'] = self.sanitize_string(data['address'])
        
        # Validate property type
        valid_types = ['residential', 'commercial', 'industrial']
        if data['property_type'] not in valid_types:
            raise ValidationError(f"Invalid property type. Must be one of: {', '.join(valid_types)}")
        
        # Validate numeric fields
        if 'purchase_price' in data and data['purchase_price'] is not None:
            if not isinstance(data['purchase_price'], (int, float)) or data['purchase_price'] < 0:
                raise ValidationError("Purchase price must be a non-negative number")
        
        if 'current_value' in data and data['current_value'] is not None:
            if not isinstance(data['current_value'], (int, float)) or data['current_value'] < 0:
                raise ValidationError("Current value must be a non-negative number")
    
    def validate_rental_info(self, data: Dict[str, Any]):
        """
        Validate rental info data.
        
        Args:
            data: Rental info data to validate
            
        Raises:
            ValidationError: If data is invalid
        """
        required_fields = ['monthly_rent', 'lease_start_date']
        self.validate_required_fields(data, required_fields)
        
        # Validate monthly rent
        if not isinstance(data['monthly_rent'], (int, float)) or data['monthly_rent'] < 0:
            raise ValidationError("Monthly rent must be a non-negative number")
        
        # Validate dates
        try:
            data['lease_start_date'] = timezone.datetime.strptime(
                data['lease_start_date'], '%Y-%m-%d'
            ).date()
        except ValueError:
            raise ValidationError("Invalid lease start date format. Use YYYY-MM-DD")
        
        if 'lease_end_date' in data and data['lease_end_date']:
            try:
                data['lease_end_date'] = timezone.datetime.strptime(
                    data['lease_end_date'], '%Y-%m-%d'
                ).date()
                if data['lease_end_date'] < data['lease_start_date']:
                    raise ValidationError("Lease end date must be after start date")
            except ValueError:
                raise ValidationError("Invalid lease end date format. Use YYYY-MM-DD")

class MaintenanceValidator(BaseValidator):
    """Validator for maintenance-related data."""
    
    def validate_maintenance_data(self, data: Dict[str, Any]):
        """
        Validate maintenance request data.
        
        Args:
            data: Maintenance request data to validate
            
        Raises:
            ValidationError: If data is invalid
        """
        required_fields = ['property_id', 'title', 'description', 'priority']
        self.validate_required_fields(data, required_fields)
        
        # Validate string fields
        data['title'] = self.sanitize_string(data['title'])
        data['description'] = self.sanitize_string(data['description'])
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if data['priority'] not in valid_priorities:
            raise ValidationError(f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")
        
        # Validate status if provided
        if 'status' in data:
            valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
            if data['status'] not in valid_statuses:
                raise ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Validate cost if provided
        if 'cost' in data and data['cost'] is not None:
            if not isinstance(data['cost'], (int, float)) or data['cost'] < 0:
                raise ValidationError("Cost must be a non-negative number")

class ExpenseValidator(BaseValidator):
    """Validator for expense-related data."""
    
    def validate_expense_data(self, data: Dict[str, Any]):
        """
        Validate expense data.
        
        Args:
            data: Expense data to validate
            
        Raises:
            ValidationError: If data is invalid
        """
        required_fields = ['property_id', 'category', 'amount', 'date']
        self.validate_required_fields(data, required_fields)
        
        # Validate category
        valid_categories = [
            'mortgage', 'tax', 'insurance', 'utilities', 'maintenance',
            'repairs', 'improvements', 'management', 'other'
        ]
        if data['category'] not in valid_categories:
            raise ValidationError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
        
        # Validate amount
        if not isinstance(data['amount'], (int, float)) or data['amount'] < 0:
            raise ValidationError("Amount must be a non-negative number")
        
        # Validate date
        try:
            data['date'] = timezone.datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")
        
        # Validate description if provided
        if 'description' in data:
            data['description'] = self.sanitize_string(data['description'])

class InvoiceValidator(BaseValidator):
    """Validator for invoice-related data."""
    
    def validate_invoice_data(self, data: Dict[str, Any]):
        """
        Validate invoice data.
        
        Args:
            data: Invoice data to validate
            
        Raises:
            ValidationError: If data is invalid
        """
        required_fields = ['property_id', 'invoice_number', 'amount', 'due_date']
        self.validate_required_fields(data, required_fields)
        
        # Validate invoice number
        data['invoice_number'] = self.sanitize_string(data['invoice_number'])
        if not re.match(r'^[A-Za-z0-9-]+$', data['invoice_number']):
            raise ValidationError("Invoice number can only contain letters, numbers, and hyphens")
        
        # Validate amount
        if not isinstance(data['amount'], (int, float)) or data['amount'] < 0:
            raise ValidationError("Amount must be a non-negative number")
        
        # Validate due date
        try:
            data['due_date'] = timezone.datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Invalid due date format. Use YYYY-MM-DD")
        
        # Validate status if provided
        if 'status' in data:
            valid_statuses = ['pending', 'paid', 'overdue', 'cancelled']
            if data['status'] not in valid_statuses:
                raise ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Validate description if provided
        if 'description' in data:
            data['description'] = self.sanitize_string(data['description']) 