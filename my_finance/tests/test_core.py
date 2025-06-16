"""
Test suite for core modules.
This module contains tests for services, repositories, and validators.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import datetime

from ..core.models import (
    Property,
    PropertyRentalInfo,
    PropertyMaintenance,
    PropertyExpense,
    PropertyInvoice
)
from ..core.services import (
    PropertyService,
    MaintenanceService,
    ExpenseService,
    InvoiceService
)
from ..core.repositories import (
    PropertyRepository,
    MaintenanceRepository,
    ExpenseRepository,
    InvoiceRepository
)
from ..core.validators import (
    PropertyValidator,
    MaintenanceValidator,
    ExpenseValidator,
    InvoiceValidator
)

class BaseTestCase(TestCase):
    """Base test case with common setup."""
    
    def setUp(self):
        """Set up test data."""
        self.user_id = 1
        self.property_data = {
            'name': 'Test Property',
            'address': '123 Test St',
            'property_type': 'residential',
            'purchase_price': 100000,
            'current_value': 150000
        }
        self.rental_info_data = {
            'monthly_rent': 1500,
            'lease_start_date': '2024-01-01',
            'lease_end_date': '2024-12-31',
            'tenant_name': 'John Doe',
            'tenant_contact': 'john@example.com'
        }
        self.maintenance_data = {
            'title': 'Fix Leak',
            'description': 'Fix leaking pipe in bathroom',
            'priority': 'high',
            'cost': 500
        }
        self.expense_data = {
            'category': 'maintenance',
            'amount': 500,
            'date': '2024-01-15',
            'description': 'Plumbing repair'
        }
        self.invoice_data = {
            'invoice_number': 'INV-001',
            'amount': 1500,
            'due_date': '2024-02-01',
            'description': 'January Rent'
        }

class PropertyServiceTest(BaseTestCase):
    """Test cases for PropertyService."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.service = PropertyService()
    
    def test_create_property(self):
        """Test creating a property."""
        property = self.service.create_property(self.user_id, self.property_data)
        self.assertEqual(property.name, self.property_data['name'])
        self.assertEqual(property.address, self.property_data['address'])
        self.assertEqual(property.property_type, self.property_data['property_type'])
    
    def test_create_property_with_rental_info(self):
        """Test creating a property with rental info."""
        data = {**self.property_data, 'rental_info': self.rental_info_data}
        property = self.service.create_property(self.user_id, data)
        self.assertEqual(property.rental_info.monthly_rent, self.rental_info_data['monthly_rent'])
        self.assertEqual(property.rental_info.tenant_name, self.rental_info_data['tenant_name'])

class MaintenanceServiceTest(BaseTestCase):
    """Test cases for MaintenanceService."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.service = MaintenanceService()
        self.property = Property.objects.create(
            user_id=self.user_id,
            **self.property_data
        )
        self.maintenance_data['property_id'] = self.property.id
    
    def test_create_maintenance_request(self):
        """Test creating a maintenance request."""
        request = self.service.create_maintenance_request(
            self.user_id,
            self.maintenance_data
        )
        self.assertEqual(request.title, self.maintenance_data['title'])
        self.assertEqual(request.description, self.maintenance_data['description'])
        self.assertEqual(request.priority, self.maintenance_data['priority'])

class ExpenseServiceTest(BaseTestCase):
    """Test cases for ExpenseService."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.service = ExpenseService()
        self.property = Property.objects.create(
            user_id=self.user_id,
            **self.property_data
        )
        self.expense_data['property_id'] = self.property.id
    
    def test_create_expense(self):
        """Test creating an expense."""
        expense = self.service.create_expense(self.user_id, self.expense_data)
        self.assertEqual(expense.category, self.expense_data['category'])
        self.assertEqual(expense.amount, self.expense_data['amount'])
        self.assertEqual(expense.description, self.expense_data['description'])

class InvoiceServiceTest(BaseTestCase):
    """Test cases for InvoiceService."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.service = InvoiceService()
        self.property = Property.objects.create(
            user_id=self.user_id,
            **self.property_data
        )
        self.invoice_data['property_id'] = self.property.id
    
    def test_create_invoice(self):
        """Test creating an invoice."""
        invoice = self.service.create_invoice(self.user_id, self.invoice_data)
        self.assertEqual(invoice.invoice_number, self.invoice_data['invoice_number'])
        self.assertEqual(invoice.amount, self.invoice_data['amount'])
        self.assertEqual(invoice.description, self.invoice_data['description'])

class PropertyValidatorTest(BaseTestCase):
    """Test cases for PropertyValidator."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.validator = PropertyValidator()
    
    def test_validate_property_data(self):
        """Test validating property data."""
        self.validator.validate_property_data(self.property_data)
    
    def test_validate_property_data_missing_required(self):
        """Test validating property data with missing required fields."""
        data = self.property_data.copy()
        del data['name']
        with self.assertRaises(ValidationError):
            self.validator.validate_property_data(data)
    
    def test_validate_property_data_invalid_type(self):
        """Test validating property data with invalid property type."""
        data = self.property_data.copy()
        data['property_type'] = 'invalid'
        with self.assertRaises(ValidationError):
            self.validator.validate_property_data(data)

class MaintenanceValidatorTest(BaseTestCase):
    """Test cases for MaintenanceValidator."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.validator = MaintenanceValidator()
        self.property = Property.objects.create(
            user_id=self.user_id,
            **self.property_data
        )
        self.maintenance_data['property_id'] = self.property.id
    
    def test_validate_maintenance_data(self):
        """Test validating maintenance data."""
        self.validator.validate_maintenance_data(self.maintenance_data)
    
    def test_validate_maintenance_data_missing_required(self):
        """Test validating maintenance data with missing required fields."""
        data = self.maintenance_data.copy()
        del data['title']
        with self.assertRaises(ValidationError):
            self.validator.validate_maintenance_data(data)
    
    def test_validate_maintenance_data_invalid_priority(self):
        """Test validating maintenance data with invalid priority."""
        data = self.maintenance_data.copy()
        data['priority'] = 'invalid'
        with self.assertRaises(ValidationError):
            self.validator.validate_maintenance_data(data)

class ExpenseValidatorTest(BaseTestCase):
    """Test cases for ExpenseValidator."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.validator = ExpenseValidator()
        self.property = Property.objects.create(
            user_id=self.user_id,
            **self.property_data
        )
        self.expense_data['property_id'] = self.property.id
    
    def test_validate_expense_data(self):
        """Test validating expense data."""
        self.validator.validate_expense_data(self.expense_data)
    
    def test_validate_expense_data_missing_required(self):
        """Test validating expense data with missing required fields."""
        data = self.expense_data.copy()
        del data['category']
        with self.assertRaises(ValidationError):
            self.validator.validate_expense_data(data)
    
    def test_validate_expense_data_invalid_category(self):
        """Test validating expense data with invalid category."""
        data = self.expense_data.copy()
        data['category'] = 'invalid'
        with self.assertRaises(ValidationError):
            self.validator.validate_expense_data(data)

class InvoiceValidatorTest(BaseTestCase):
    """Test cases for InvoiceValidator."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.validator = InvoiceValidator()
        self.property = Property.objects.create(
            user_id=self.user_id,
            **self.property_data
        )
        self.invoice_data['property_id'] = self.property.id
    
    def test_validate_invoice_data(self):
        """Test validating invoice data."""
        self.validator.validate_invoice_data(self.invoice_data)
    
    def test_validate_invoice_data_missing_required(self):
        """Test validating invoice data with missing required fields."""
        data = self.invoice_data.copy()
        del data['invoice_number']
        with self.assertRaises(ValidationError):
            self.validator.validate_invoice_data(data)
    
    def test_validate_invoice_data_invalid_number(self):
        """Test validating invoice data with invalid invoice number."""
        data = self.invoice_data.copy()
        data['invoice_number'] = 'INV@001'
        with self.assertRaises(ValidationError):
            self.validator.validate_invoice_data(data) 