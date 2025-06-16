"""
Property-related views for the personal finance application.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Sum, F, Q
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import logging
from datetime import datetime, timedelta

from ..models import (
    Property, PropertyRentalInfo, PropertyInvoice,
    PropertyMaintenance, PropertyExpense, RentalPropertyModel
)
from ..forms import (
    PropertyForm, PropertyRentalInfoForm, PropertyInvoiceForm,
    PropertyMaintenanceForm, PropertyExpenseForm
)
from ..permissions import PropertyPermissionMixin, get_user_properties
from ..validators import validate_property_value, sanitize_input
from .base import BaseViewMixin, MessageMixin, APIViewMixin

logger = logging.getLogger(__name__)

class PropertyListView(BaseViewMixin, ListView):
    """View for listing all properties."""
    model = Property
    template_name = 'property/list.html'
    context_object_name = 'properties'
    
    def get_queryset(self):
        """Get properties for the current user."""
        return Property.objects.filter(
            get_user_properties(self.request.user)
        ).select_related(
            'property_rental_info'
        ).order_by('property_name')
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        properties = self.get_queryset()
        
        # Calculate total value
        context['total_value'] = properties.filter(
            include_net_worth=True
        ).aggregate(
            total=Sum('value')
        )['total'] or Decimal('0.00')
        
        # Calculate total monthly rent
        context['total_monthly_rent'] = properties.aggregate(
            total=Sum('property_rental_info__monthly_rent')
        )['total'] or Decimal('0.00')
        
        # Get recent maintenance requests
        context['recent_maintenance'] = PropertyMaintenance.objects.filter(
            property_details__in=properties
        ).select_related(
            'property_details'
        ).order_by('-created_at')[:5]
        
        return context

class PropertyCreateView(BaseViewMixin, MessageMixin, CreateView):
    """View for creating a new property."""
    model = Property
    form_class = PropertyForm
    template_name = 'property/create.html'
    success_url = reverse_lazy('property_list')
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            # Validate property value
            validate_property_value(form.cleaned_data['value'])
            
            # Sanitize input
            form.cleaned_data['property_name'] = sanitize_input(form.cleaned_data['property_name'])
            form.cleaned_data['address'] = sanitize_input(form.cleaned_data['address'])
            form.cleaned_data['description'] = sanitize_input(form.cleaned_data['description'])
            
            form.instance.user = self.request.user
            response = super().form_valid(form)
            self.add_success_message('Property created successfully.')
            return response
        except Exception as e:
            logger.error(f"Error creating property: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while creating the property.')
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class PropertyUpdateView(BaseViewMixin, PropertyPermissionMixin, MessageMixin, UpdateView):
    """View for updating an existing property."""
    model = Property
    form_class = PropertyForm
    template_name = 'property/update.html'
    success_url = reverse_lazy('property_list')
    
    def get_queryset(self):
        """Get properties for the current user."""
        return Property.objects.filter(
            get_user_properties(self.request.user)
        )
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            # Validate property value
            validate_property_value(form.cleaned_data['value'])
            
            # Sanitize input
            form.cleaned_data['property_name'] = sanitize_input(form.cleaned_data['property_name'])
            form.cleaned_data['address'] = sanitize_input(form.cleaned_data['address'])
            form.cleaned_data['description'] = sanitize_input(form.cleaned_data['description'])
            
            response = super().form_valid(form)
            self.add_success_message('Property updated successfully.')
            return response
        except Exception as e:
            logger.error(f"Error updating property: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while updating the property.')
            return self.form_invalid(form)

class PropertyDeleteView(BaseViewMixin, PropertyPermissionMixin, MessageMixin, DeleteView):
    """View for deleting a property."""
    model = Property
    success_url = reverse_lazy('property_list')
    
    def get_queryset(self):
        """Get properties for the current user."""
        return Property.objects.filter(
            get_user_properties(self.request.user)
        )
    
    def delete(self, request, *args, **kwargs):
        """Handle property deletion."""
        try:
            obj = self.get_object()
            
            # Check for related records
            if PropertyRentalInfo.objects.filter(property_address=obj).exists():
                self.add_error_message('Cannot delete property with existing rental information.')
                return redirect('property_list')
            
            if PropertyInvoice.objects.filter(property_details=obj).exists():
                self.add_error_message('Cannot delete property with existing invoices.')
                return redirect('property_list')
            
            if PropertyMaintenance.objects.filter(property_details=obj).exists():
                self.add_error_message('Cannot delete property with existing maintenance requests.')
                return redirect('property_list')
            
            if PropertyExpense.objects.filter(property_details=obj).exists():
                self.add_error_message('Cannot delete property with existing expenses.')
                return redirect('property_list')
            
            response = super().delete(request, *args, **kwargs)
            self.add_success_message('Property deleted successfully.')
            return response
        except Exception as e:
            logger.error(f"Error deleting property: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while deleting the property.')
            return redirect('property_list')

class PropertyDetailView(BaseViewMixin, PropertyPermissionMixin, DetailView):
    """View for displaying property details."""
    model = Property
    template_name = 'property/detail.html'
    context_object_name = 'property'
    
    def get_queryset(self):
        """Get properties for the current user."""
        return Property.objects.filter(
            get_user_properties(self.request.user)
        ).select_related('property_rental_info')
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        property_obj = self.get_object()
        
        # Get rental information
        context['rental_info'] = PropertyRentalInfo.objects.filter(
            property_address=property_obj
        ).first()
        
        # Get recent invoices
        context['recent_invoices'] = PropertyInvoice.objects.filter(
            property_details=property_obj
        ).select_related(
            'property_details'
        ).order_by('-invoice_date')[:5]
        
        # Get recent maintenance requests
        context['recent_maintenance'] = PropertyMaintenance.objects.filter(
            property_details=property_obj
        ).select_related(
            'property_details'
        ).order_by('-created_at')[:5]
        
        # Get recent expenses
        context['recent_expenses'] = PropertyExpense.objects.filter(
            property_details=property_obj
        ).select_related(
            'property_details'
        ).order_by('-expense_date')[:5]
        
        # Calculate monthly totals
        today = timezone.now()
        first_day = today.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_income = PropertyInvoice.objects.filter(
            property_details=property_obj,
            invoice_paid_date__gte=first_day,
            invoice_paid_date__lte=last_day
        ).aggregate(total=Sum('item_amount'))['total'] or Decimal('0.00')
        
        monthly_expense = PropertyExpense.objects.filter(
            property_details=property_obj,
            expense_date__gte=first_day,
            expense_date__lte=last_day
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        context['monthly_income'] = monthly_income
        context['monthly_expense'] = monthly_expense
        context['monthly_net'] = monthly_income - monthly_expense
        
        return context

class PropertyAPIView(BaseViewMixin, APIViewMixin):
    """API view for property operations."""
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests."""
        try:
            if 'pk' in kwargs:
                # Get single property
                property_obj = Property.objects.filter(
                    get_user_properties(request.user)
                ).select_related(
                    'property_rental_info'
                ).get(pk=kwargs['pk'])
                
                return self.json_response({
                    'id': property_obj.id,
                    'property_name': property_obj.property_name,
                    'address': property_obj.address,
                    'value': str(property_obj.value),
                    'include_net_worth': property_obj.include_net_worth,
                    'description': property_obj.description,
                    'rental_info': {
                        'tenant_name': property_obj.property_rental_info.tenant_name,
                        'monthly_rent': str(property_obj.property_rental_info.monthly_rent),
                        'lease_start': property_obj.property_rental_info.lease_start.isoformat(),
                        'lease_end': property_obj.property_rental_info.lease_end.isoformat() if property_obj.property_rental_info.lease_end else None
                    } if hasattr(property_obj, 'property_rental_info') else None
                })
            else:
                # Get all properties
                properties = Property.objects.filter(
                    get_user_properties(request.user)
                ).select_related(
                    'property_rental_info'
                ).order_by('property_name')
                
                return self.json_response({
                    'properties': [{
                        'id': p.id,
                        'property_name': p.property_name,
                        'address': p.address,
                        'value': str(p.value),
                        'include_net_worth': p.include_net_worth,
                        'description': p.description,
                        'rental_info': {
                            'tenant_name': p.property_rental_info.tenant_name,
                            'monthly_rent': str(p.property_rental_info.monthly_rent),
                            'lease_start': p.property_rental_info.lease_start.isoformat(),
                            'lease_end': p.property_rental_info.lease_end.isoformat() if p.property_rental_info.lease_end else None
                        } if hasattr(p, 'property_rental_info') else None
                    } for p in properties]
                })
        except Property.DoesNotExist:
            return self.error_response('Property not found.', status=404)
        except Exception as e:
            logger.error(f"Error in property API: {str(e)}", exc_info=True)
            return self.error_response('An error occurred while retrieving property information.') 