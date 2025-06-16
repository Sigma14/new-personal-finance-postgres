"""
Tests for dashboard views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from ..models import (
    User, Property, PropertyRentalInfo,
    PropertyInvoice, PropertyExpense, PropertyMaintenance
)

class DashboardViewTests(TestCase):
    """Test cases for dashboard views."""
    
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
            property_value=Decimal('200000.00'),
            property_address='123 Test St',
            property_city='Test City',
            property_state='TS',
            property_zip='12345'
        )
        
        # Create rental info
        self.rental_info = PropertyRentalInfo.objects.create(
            property_details=self.property,
            monthly_rent=Decimal('1500.00'),
            security_deposit=Decimal('1500.00'),
            lease_start_date=timezone.now().date(),
            lease_end_date=timezone.now().date() + timedelta(days=365)
        )
        
        # Create test invoices
        self.invoice = PropertyInvoice.objects.create(
            property_details=self.property,
            item_description='Test Invoice',
            item_amount=Decimal('1500.00'),
            invoice_date=timezone.now().date(),
            invoice_due_date=timezone.now().date() + timedelta(days=7),
            invoice_paid_date=timezone.now().date()
        )
        
        # Create test expenses
        self.expense = PropertyExpense.objects.create(
            property_details=self.property,
            expense_description='Test Expense',
            amount=Decimal('500.00'),
            expense_date=timezone.now().date(),
            expense_category='Maintenance'
        )
        
        # Create test maintenance request
        self.maintenance = PropertyMaintenance.objects.create(
            property_details=self.property,
            description='Test Maintenance',
            status='pending',
            request_date=timezone.now().date(),
            cost=Decimal('200.00')
        )
        
        # Set up client
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_dashboard_view(self):
        """Test dashboard view."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertIn('total_property_value', response.context)
        self.assertIn('monthly_income', response.context)
        self.assertIn('monthly_expenses', response.context)
        self.assertIn('net_monthly_income', response.context)
        self.assertIn('maintenance_stats', response.context)
        self.assertIn('recent_maintenance', response.context)
        self.assertIn('overdue_invoices', response.context)
        self.assertIn('expense_categories', response.context)
        self.assertIn('property_performance', response.context)
        
        # Check values
        self.assertEqual(response.context['total_property_value'], Decimal('200000.00'))
        self.assertEqual(response.context['monthly_income'], Decimal('1500.00'))
        self.assertEqual(response.context['monthly_expenses'], Decimal('500.00'))
        self.assertEqual(response.context['net_monthly_income'], Decimal('1000.00'))
    
    def test_dashboard_api_view(self):
        """Test dashboard API view."""
        response = self.client.get(reverse('dashboard_api'))
        self.assertEqual(response.status_code, 200)
        
        # Check response data
        data = response.json()
        self.assertIn('monthly_income', data)
        self.assertIn('monthly_expenses', data)
        self.assertIn('maintenance_stats', data)
        self.assertIn('total_properties', data)
        
        # Check values
        self.assertEqual(Decimal(data['monthly_income']), Decimal('1500.00'))
        self.assertEqual(Decimal(data['monthly_expenses']), Decimal('500.00'))
        self.assertEqual(data['total_properties'], 1)
    
    def test_dashboard_view_with_no_data(self):
        """Test dashboard view with no data."""
        # Create new user with no data
        user = User.objects.create_user(
            username='emptyuser',
            email='empty@example.com',
            password='testpass123'
        )
        self.client.login(username='emptyuser', password='testpass123')
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check default values
        self.assertEqual(response.context['total_property_value'], Decimal('0.00'))
        self.assertEqual(response.context['monthly_income'], Decimal('0.00'))
        self.assertEqual(response.context['monthly_expenses'], Decimal('0.00'))
        self.assertEqual(response.context['net_monthly_income'], Decimal('0.00'))
    
    def test_dashboard_view_with_overdue_invoice(self):
        """Test dashboard view with overdue invoice."""
        # Create overdue invoice
        overdue_invoice = PropertyInvoice.objects.create(
            property_details=self.property,
            item_description='Overdue Invoice',
            item_amount=Decimal('1000.00'),
            invoice_date=timezone.now().date() - timedelta(days=30),
            invoice_due_date=timezone.now().date() - timedelta(days=7)
        )
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check overdue invoice in context
        self.assertIn(overdue_invoice, response.context['overdue_invoices'])
    
    def test_dashboard_view_with_completed_maintenance(self):
        """Test dashboard view with completed maintenance."""
        # Create completed maintenance request
        completed_maintenance = PropertyMaintenance.objects.create(
            property_details=self.property,
            description='Completed Maintenance',
            status='completed',
            request_date=timezone.now().date() - timedelta(days=7),
            completed_date=timezone.now().date(),
            cost=Decimal('300.00')
        )
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check maintenance stats
        self.assertEqual(response.context['maintenance_stats']['completed_requests'], 1)
        self.assertEqual(response.context['maintenance_stats']['total_cost'], Decimal('500.00'))
    
    def test_dashboard_view_with_multiple_expense_categories(self):
        """Test dashboard view with multiple expense categories."""
        # Create expenses in different categories
        PropertyExpense.objects.create(
            property_details=self.property,
            expense_description='Utility Expense',
            amount=Decimal('200.00'),
            expense_date=timezone.now().date(),
            expense_category='Utilities'
        )
        
        PropertyExpense.objects.create(
            property_details=self.property,
            expense_description='Tax Expense',
            amount=Decimal('300.00'),
            expense_date=timezone.now().date(),
            expense_category='Taxes'
        )
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check expense categories
        categories = response.context['expense_categories']
        self.assertEqual(len(categories), 3)  # Maintenance, Utilities, Taxes
        
        # Check total expenses
        total_expenses = sum(category['total'] for category in categories)
        self.assertEqual(total_expenses, Decimal('1000.00')) 