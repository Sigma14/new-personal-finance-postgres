"""
Rental information views for managing property rentals.
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
    PropertyRentalInfo, PropertyInvoice, PropertyMaintenance,
    PropertyExpense, RentalPropertyModel
)
from ..forms import (
    PropertyRentalInfoForm, PropertyInvoiceForm,
    PropertyMaintenanceForm, PropertyExpenseForm
)
from ..permissions import RentalPermissionMixin, get_user_rentals
from ..validators import validate_rental_amount, sanitize_input
from .base import BaseViewMixin, MessageMixin, APIViewMixin

logger = logging.getLogger(__name__)

class RentalInfoListView(BaseViewMixin, ListView):
    """View for listing all rental information."""
    model = PropertyRentalInfo
    template_name = 'rental/list.html'
    context_object_name = 'rental_info'
    
    def get_queryset(self):
        """Get rental information for the current user's properties."""
        return PropertyRentalInfo.objects.filter(
            get_user_rentals(self.request.user)
        ).select_related('property_address').order_by('property_address__property_name')
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        rental_info = self.get_queryset()
        
        # Calculate total monthly rent
        context['total_monthly_rent'] = rental_info.aggregate(
            total=Sum('monthly_rent')
        )['total'] or Decimal('0.00')
        
        # Get recent invoices
        context['recent_invoices'] = PropertyInvoice.objects.filter(
            property_details__in=rental_info
        ).select_related(
            'property_details'
        ).order_by('-invoice_date')[:5]
        
        # Get recent maintenance requests
        context['recent_maintenance'] = PropertyMaintenance.objects.filter(
            property_details__in=rental_info
        ).select_related(
            'property_details'
        ).order_by('-created_at')[:5]
        
        return context

class RentalInfoCreateView(BaseViewMixin, MessageMixin, CreateView):
    """View for creating new rental information."""
    model = PropertyRentalInfo
    form_class = PropertyRentalInfoForm
    template_name = 'rental/create.html'
    success_url = reverse_lazy('rental_list')
    
    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            # Validate rental amount
            validate_rental_amount(form.cleaned_data['monthly_rent'])
            
            # Sanitize input
            form.cleaned_data['tenant_name'] = sanitize_input(form.cleaned_data['tenant_name'])
            form.cleaned_data['tenant_email'] = sanitize_input(form.cleaned_data['tenant_email'])
            form.cleaned_data['tenant_phone'] = sanitize_input(form.cleaned_data['tenant_phone'])
            
            response = super().form_valid(form)
            self.add_success_message('Rental information created successfully.')
            return response
        except Exception as e:
            logger.error(f"Error creating rental information: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while creating the rental information.')
            return self.form_invalid(form)

class RentalInfoUpdateView(BaseViewMixin, RentalPermissionMixin, MessageMixin, UpdateView):
    """View for updating rental information."""
    model = PropertyRentalInfo
    form_class = PropertyRentalInfoForm
    template_name = 'rental/update.html'
    success_url = reverse_lazy('rental_list')
    
    def get_queryset(self):
        """Get rental information for the current user's properties."""
        return PropertyRentalInfo.objects.filter(
            get_user_rentals(self.request.user)
        )
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            # Validate rental amount
            validate_rental_amount(form.cleaned_data['monthly_rent'])
            
            # Sanitize input
            form.cleaned_data['tenant_name'] = sanitize_input(form.cleaned_data['tenant_name'])
            form.cleaned_data['tenant_email'] = sanitize_input(form.cleaned_data['tenant_email'])
            form.cleaned_data['tenant_phone'] = sanitize_input(form.cleaned_data['tenant_phone'])
            
            response = super().form_valid(form)
            self.add_success_message('Rental information updated successfully.')
            return response
        except Exception as e:
            logger.error(f"Error updating rental information: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while updating the rental information.')
            return self.form_invalid(form)

class RentalInfoDeleteView(BaseViewMixin, RentalPermissionMixin, MessageMixin, DeleteView):
    """View for deleting rental information."""
    model = PropertyRentalInfo
    success_url = reverse_lazy('rental_list')
    
    def get_queryset(self):
        """Get rental information for the current user's properties."""
        return PropertyRentalInfo.objects.filter(
            get_user_rentals(self.request.user)
        )
    
    def delete(self, request, *args, **kwargs):
        """Handle rental information deletion."""
        try:
            obj = self.get_object()
            
            # Check for related records
            if PropertyInvoice.objects.filter(property_details=obj).exists():
                self.add_error_message('Cannot delete rental information with existing invoices.')
                return redirect('rental_list')
            
            if PropertyMaintenance.objects.filter(property_details=obj).exists():
                self.add_error_message('Cannot delete rental information with existing maintenance requests.')
                return redirect('rental_list')
            
            response = super().delete(request, *args, **kwargs)
            self.add_success_message('Rental information deleted successfully.')
            return response
        except Exception as e:
            logger.error(f"Error deleting rental information: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while deleting the rental information.')
            return redirect('rental_list')

class RentalInfoDetailView(BaseViewMixin, RentalPermissionMixin, DetailView):
    """View for displaying rental information details."""
    model = PropertyRentalInfo
    template_name = 'rental/detail.html'
    context_object_name = 'rental_info'
    
    def get_queryset(self):
        """Get rental information for the current user's properties."""
        return PropertyRentalInfo.objects.filter(
            get_user_rentals(self.request.user)
        ).select_related('property_address')
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        rental_info = self.get_object()
        
        # Get recent invoices
        context['recent_invoices'] = PropertyInvoice.objects.filter(
            property_details=rental_info
        ).select_related(
            'property_details'
        ).order_by('-invoice_date')[:5]
        
        # Get recent maintenance requests
        context['recent_maintenance'] = PropertyMaintenance.objects.filter(
            property_details=rental_info
        ).select_related(
            'property_details'
        ).order_by('-created_at')[:5]
        
        # Calculate monthly income and expenses
        monthly_income = rental_info.monthly_rent or Decimal('0.00')
        monthly_expense = PropertyExpense.objects.filter(
            property_details=rental_info
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        context['monthly_income'] = monthly_income
        context['monthly_expense'] = monthly_expense
        context['monthly_net'] = monthly_income - monthly_expense
        
        return context

class RentalInfoAPIView(BaseViewMixin, APIViewMixin):
    """API view for rental information operations."""
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests."""
        try:
            if 'pk' in kwargs:
                # Get single rental info
                rental_info = PropertyRentalInfo.objects.filter(
                    get_user_rentals(request.user)
                ).select_related(
                    'property_address'
                ).get(pk=kwargs['pk'])
                
                return self.json_response({
                    'id': rental_info.id,
                    'property_name': rental_info.property_address.property_name,
                    'tenant_name': rental_info.tenant_name,
                    'monthly_rent': str(rental_info.monthly_rent),
                    'lease_start': rental_info.lease_start.isoformat(),
                    'lease_end': rental_info.lease_end.isoformat() if rental_info.lease_end else None
                })
            else:
                # Get all rental info
                rental_info = PropertyRentalInfo.objects.filter(
                    get_user_rentals(request.user)
                ).select_related(
                    'property_address'
                ).order_by('property_address__property_name')
                
                return self.json_response({
                    'rental_info': [{
                        'id': ri.id,
                        'property_name': ri.property_address.property_name,
                        'tenant_name': ri.tenant_name,
                        'monthly_rent': str(ri.monthly_rent),
                        'lease_start': ri.lease_start.isoformat(),
                        'lease_end': ri.lease_end.isoformat() if ri.lease_end else None
                    } for ri in rental_info]
                })
        except PropertyRentalInfo.DoesNotExist:
            return self.error_response('Rental information not found.', status=404)
        except Exception as e:
            logger.error(f"Error in rental info API: {str(e)}", exc_info=True)
            return self.error_response('An error occurred while retrieving rental information.') 