"""
Service layer for the finance application.
This module contains business logic and orchestrates operations between repositories and validators.
"""
from typing import List, Optional, Dict, Any
from django.db.models import QuerySet
from django.utils import timezone
import logging

from .models import (
    Property,
    PropertyRentalInfo,
    PropertyMaintenance,
    PropertyExpense,
    PropertyInvoice
)
from .repositories import (
    PropertyRepository,
    MaintenanceRepository,
    ExpenseRepository,
    InvoiceRepository
)
from .validators import (
    PropertyValidator,
    MaintenanceValidator,
    ExpenseValidator,
    InvoiceValidator
)

logger = logging.getLogger(__name__)

class BaseService:
    """Base service class with common functionality."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

class PropertyService(BaseService):
    """Service for property-related operations."""
    
    def __init__(self):
        super().__init__()
        self.repository = PropertyRepository()
        self.validator = PropertyValidator()
    
    def get_properties(self, user_id: int) -> QuerySet:
        """
        Get all properties for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            QuerySet of properties
            
        Raises:
            Exception: If there's an error retrieving properties
        """
        try:
            return self.repository.get_by_user(user_id)
        except Exception as e:
            self.logger.error(f"Error getting properties for user {user_id}: {str(e)}")
            raise
    
    def create_property(self, user_id: int, data: Dict[str, Any]) -> Property:
        """
        Create a new property.
        
        Args:
            user_id: The ID of the user
            data: Property data
            
        Returns:
            Created property
            
        Raises:
            ValidationError: If data is invalid
            Exception: If there's an error creating property
        """
        try:
            # Validate data
            self.validator.validate_property_data(data)
            
            # Create property
            property = self.repository.create(user_id, data)
            
            # Create rental info if provided
            if 'rental_info' in data:
                self.validator.validate_rental_info(data['rental_info'])
                self.repository.create_rental_info(property, data['rental_info'])
            
            return property
            
        except Exception as e:
            self.logger.error(f"Error creating property for user {user_id}: {str(e)}")
            raise

class MaintenanceService(BaseService):
    """Service for maintenance-related operations."""
    
    def __init__(self):
        super().__init__()
        self.repository = MaintenanceRepository()
        self.validator = MaintenanceValidator()
    
    def get_maintenance_requests(self, user_id: int) -> QuerySet:
        """
        Get all maintenance requests for a user's properties.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            QuerySet of maintenance requests
            
        Raises:
            Exception: If there's an error retrieving requests
        """
        try:
            return self.repository.get_by_user(user_id)
        except Exception as e:
            self.logger.error(f"Error getting maintenance requests for user {user_id}: {str(e)}")
            raise
    
    def create_maintenance_request(self, user_id: int, data: Dict[str, Any]) -> PropertyMaintenance:
        """
        Create a new maintenance request.
        
        Args:
            user_id: The ID of the user
            data: Maintenance request data
            
        Returns:
            Created maintenance request
            
        Raises:
            ValidationError: If data is invalid
            Exception: If there's an error creating request
        """
        try:
            # Validate data
            self.validator.validate_maintenance_data(data)
            
            # Create request
            request = self.repository.create(user_id, data)
            
            return request
            
        except Exception as e:
            self.logger.error(f"Error creating maintenance request for user {user_id}: {str(e)}")
            raise

class ExpenseService(BaseService):
    """Service for expense-related operations."""
    
    def __init__(self):
        super().__init__()
        self.repository = ExpenseRepository()
        self.validator = ExpenseValidator()
    
    def get_expenses(self, user_id: int) -> QuerySet:
        """
        Get all expenses for a user's properties.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            QuerySet of expenses
            
        Raises:
            Exception: If there's an error retrieving expenses
        """
        try:
            return self.repository.get_by_user(user_id)
        except Exception as e:
            self.logger.error(f"Error getting expenses for user {user_id}: {str(e)}")
            raise
    
    def create_expense(self, user_id: int, data: Dict[str, Any]) -> PropertyExpense:
        """
        Create a new expense.
        
        Args:
            user_id: The ID of the user
            data: Expense data
            
        Returns:
            Created expense
            
        Raises:
            ValidationError: If data is invalid
            Exception: If there's an error creating expense
        """
        try:
            # Validate data
            self.validator.validate_expense_data(data)
            
            # Create expense
            expense = self.repository.create(user_id, data)
            
            return expense
            
        except Exception as e:
            self.logger.error(f"Error creating expense for user {user_id}: {str(e)}")
            raise

class InvoiceService(BaseService):
    """Service for invoice-related operations."""
    
    def __init__(self):
        super().__init__()
        self.repository = InvoiceRepository()
        self.validator = InvoiceValidator()
    
    def get_invoices(self, user_id: int) -> QuerySet:
        """
        Get all invoices for a user's properties.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            QuerySet of invoices
            
        Raises:
            Exception: If there's an error retrieving invoices
        """
        try:
            return self.repository.get_by_user(user_id)
        except Exception as e:
            self.logger.error(f"Error getting invoices for user {user_id}: {str(e)}")
            raise
    
    def create_invoice(self, user_id: int, data: Dict[str, Any]) -> PropertyInvoice:
        """
        Create a new invoice.
        
        Args:
            user_id: The ID of the user
            data: Invoice data
            
        Returns:
            Created invoice
            
        Raises:
            ValidationError: If data is invalid
            Exception: If there's an error creating invoice
        """
        try:
            # Validate data
            self.validator.validate_invoice_data(data)
            
            # Create invoice
            invoice = self.repository.create(user_id, data)
            
            return invoice
            
        except Exception as e:
            self.logger.error(f"Error creating invoice for user {user_id}: {str(e)}")
            raise 