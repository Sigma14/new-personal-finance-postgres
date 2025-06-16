"""
Test suite for all views in the application.
This module contains tests for:
- Dashboard views
- Property views
- Maintenance views
- Expense views
- Invoice views
- Authentication views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json

from ..models import (
    Property, PropertyRentalInfo, PropertyMaintenance,
    PropertyExpense, PropertyInvoice
)
from ..utils.query_builder import QueryBuilder
from ..utils.cache import CacheMonitor

User = get_user_model()

class BaseViewTestCase(TestCase):
    """Base test case with common setup."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test property
        self.property = Property.objects.create(
            user=self.user,
            property_name='Test Property',
            property_value=Decimal('100000.00'),
            property_type='residential'
        )
        
        # Create rental info
        self.rental_info = PropertyRentalInfo.objects.create(
            property_details=self.property,
            monthly_rent=Decimal('1000.00'),
            occupancy_rate=Decimal('95.00')
        )
        
        # Create test client
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

class DashboardViewTests(BaseViewTestCase):
    """Tests for dashboard views."""
    
    def test_dashboard_view(self):
        """Test main dashboard view."""
        # Create test data
        PropertyMaintenance.objects.create(
            property_details=self.property,
            request_description='Test maintenance',
            status='pending',
            cost=Decimal('100.00')
        )
        
        PropertyExpense.objects.create(
            property_details=self.property,
            expense_category='utilities',
            amount=Decimal('50.00'),
            expense_date=timezone.now()
        )
        
        PropertyInvoice.objects.create(
            property_details=self.property,
            invoice_number='INV-001',
            amount=Decimal('1000.00'),
            due_date=timezone.now()
        )
        
        # Test dashboard view
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertIn('property_stats', response.context)
        self.assertIn('maintenance_stats', response.context)
        self.assertIn('expense_stats', response.context)
        self.assertIn('invoice_stats', response.context)
        
        # Verify statistics
        self.assertEqual(
            response.context['property_stats']['total_properties'],
            1
        )
        self.assertEqual(
            response.context['maintenance_stats']['total_requests'],
            1
        )
    
    def test_dashboard_api(self):
        """Test dashboard API endpoint."""
        response = self.client.get(reverse('dashboard_api'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('monthly_income', data)
        self.assertIn('monthly_expenses', data)
        self.assertIn('maintenance_stats', data)
        self.assertIn('total_properties', data)

class PropertyViewTests(BaseViewTestCase):
    """Tests for property views."""
    
    def test_property_list(self):
        """Test property list view."""
        response = self.client.get(reverse('property_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('properties', response.context)
        self.assertEqual(len(response.context['properties']), 1)
    
    def test_property_create(self):
        """Test property creation."""
        data = {
            'property_name': 'New Property',
            'property_value': '200000.00',
            'property_type': 'commercial'
        }
        response = self.client.post(reverse('property_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Property.objects.filter(property_name='New Property').exists()
        )
    
    def test_property_update(self):
        """Test property update."""
        data = {
            'property_name': 'Updated Property',
            'property_value': '150000.00',
            'property_type': 'residential'
        }
        response = self.client.post(
            reverse('property_update', kwargs={'pk': self.property.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)
        self.property.refresh_from_db()
        self.assertEqual(self.property.property_name, 'Updated Property')

class MaintenanceViewTests(BaseViewTestCase):
    """Tests for maintenance views."""
    
    def test_maintenance_list(self):
        """Test maintenance list view."""
        PropertyMaintenance.objects.create(
            property_details=self.property,
            request_description='Test maintenance',
            status='pending'
        )
        
        response = self.client.get(reverse('maintenance_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('maintenance_requests', response.context)
        self.assertEqual(len(response.context['maintenance_requests']), 1)
    
    def test_maintenance_create(self):
        """Test maintenance request creation."""
        data = {
            'property_details': self.property.pk,
            'request_description': 'New maintenance request',
            'status': 'pending'
        }
        response = self.client.post(reverse('maintenance_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PropertyMaintenance.objects.filter(
                request_description='New maintenance request'
            ).exists()
        )

class ExpenseViewTests(BaseViewTestCase):
    """Tests for expense views."""
    
    def test_expense_list(self):
        """Test expense list view."""
        PropertyExpense.objects.create(
            property_details=self.property,
            expense_category='utilities',
            amount=Decimal('50.00'),
            expense_date=timezone.now()
        )
        
        response = self.client.get(reverse('expense_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('expenses', response.context)
        self.assertEqual(len(response.context['expenses']), 1)
    
    def test_expense_create(self):
        """Test expense creation."""
        data = {
            'property_details': self.property.pk,
            'expense_category': 'utilities',
            'amount': '75.00',
            'expense_date': timezone.now().strftime('%Y-%m-%d')
        }
        response = self.client.post(reverse('expense_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PropertyExpense.objects.filter(
                expense_category='utilities',
                amount=Decimal('75.00')
            ).exists()
        )

class InvoiceViewTests(BaseViewTestCase):
    """Tests for invoice views."""
    
    def test_invoice_list(self):
        """Test invoice list view."""
        PropertyInvoice.objects.create(
            property_details=self.property,
            invoice_number='INV-001',
            amount=Decimal('1000.00'),
            due_date=timezone.now()
        )
        
        response = self.client.get(reverse('invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('invoices', response.context)
        self.assertEqual(len(response.context['invoices']), 1)
    
    def test_invoice_create(self):
        """Test invoice creation."""
        data = {
            'property_details': self.property.pk,
            'invoice_number': 'INV-002',
            'amount': '1200.00',
            'due_date': timezone.now().strftime('%Y-%m-%d')
        }
        response = self.client.post(reverse('invoice_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PropertyInvoice.objects.filter(
                invoice_number='INV-002',
                amount=Decimal('1200.00')
            ).exists()
        )

class SecurityTests(BaseViewTestCase):
    """Tests for security features."""
    
    def test_unauthorized_access(self):
        """Test unauthorized access to views."""
        # Logout user
        self.client.logout()
        
        # Try accessing protected views
        views = [
            'dashboard',
            'property_list',
            'maintenance_list',
            'expense_list',
            'invoice_list'
        ]
        
        for view in views:
            response = self.client.get(reverse(view))
            self.assertEqual(response.status_code, 302)
    
    def test_cross_user_access(self):
        """Test cross-user data access prevention."""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create property for other user
        other_property = Property.objects.create(
            user=other_user,
            property_name='Other Property',
            property_value=Decimal('200000.00')
        )
        
        # Try accessing other user's property
        response = self.client.get(
            reverse('property_detail', kwargs={'pk': other_property.pk})
        )
        self.assertEqual(response.status_code, 404)
    
    def test_query_builder_security(self):
        """Test QueryBuilder security features."""
        # Try to inject SQL
        malicious_query = {
            'property_name__startswith': "'; DROP TABLE my_finance_property; --"
        }
        
        # This should not affect the database
        QueryBuilder.safe_filter(Property, malicious_query, self.user.id)
        self.assertTrue(Property.objects.filter(pk=self.property.pk).exists())

class CacheTests(BaseViewTestCase):
    """Tests for caching functionality."""
    
    def test_dashboard_cache(self):
        """Test dashboard caching."""
        # First request should cache data
        response1 = self.client.get(reverse('dashboard'))
        self.assertEqual(response1.status_code, 200)
        
        # Second request should use cache
        response2 = self.client.get(reverse('dashboard'))
        self.assertEqual(response2.status_code, 200)
        
        # Verify cache stats
        stats = CacheMonitor.get_cache_stats()
        self.assertGreater(stats['hits'], 0)
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        # Get initial dashboard data
        self.client.get(reverse('dashboard'))
        
        # Create new property
        Property.objects.create(
            user=self.user,
            property_name='New Property',
            property_value=Decimal('300000.00')
        )
        
        # Get dashboard data again
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Verify new property is included
        self.assertEqual(
            response.context['property_stats']['total_properties'],
            2
        ) 