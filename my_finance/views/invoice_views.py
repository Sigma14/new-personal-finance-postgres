"""
Views for handling property rental invoices.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
import logging

from ..models import PropertyInvoice, PropertyExpense
from ..forms import InvoiceForm
from ..permissions import InvoicePermissionMixin, get_user_invoices
from ..utils.query_builder import QueryBuilder
from ..utils.cache import get_cache_key, CacheMonitor
from .base import BaseViewMixin, APIViewMixin

logger = logging.getLogger(__name__)

class InvoiceListView(BaseViewMixin, ListView):
    """List all invoices for user's properties."""
    model = PropertyInvoice
    template_name = 'invoice/invoice_list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        """Get invoices with safe query."""
        try:
            return QueryBuilder.safe_filter(
                PropertyInvoice,
                {},
                user_id=self.request.user.id
            ).select_related(
                'property_details'
            ).order_by('-invoice_date')
        except Exception as e:
            logger.error(f"Error getting invoice list: {str(e)}", exc_info=True)
            return PropertyInvoice.objects.none()
    
    def get_context_data(self, **kwargs):
        """Get context data with statistics."""
        context = super().get_context_data(**kwargs)
        try:
            # Get invoice statistics
            stats = QueryBuilder.safe_aggregate(
                PropertyInvoice,
                {},
                user_id=self.request.user.id,
                total_invoices=Count('id'),
                paid_invoices=Count('id', filter=Q(invoice_paid_date__isnull=False)),
                overdue_invoices=Count('id', filter=Q(
                    invoice_due_date__lt=timezone.now(),
                    invoice_paid_date__isnull=True
                )),
                total_amount=Sum('item_amount')
            )
            
            # Get recent paid invoices
            recent_paid = QueryBuilder.safe_filter(
                PropertyInvoice,
                {'invoice_paid_date__isnull': False},
                user_id=self.request.user.id,
                order_by=['-invoice_paid_date'],
                limit=5
            ).select_related('property_details')
            
            context.update({
                'stats': stats,
                'recent_paid': recent_paid
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting invoice context: {str(e)}", exc_info=True)
            return context

class InvoiceCreateView(BaseViewMixin, CreateView):
    """Create a new invoice."""
    model = PropertyInvoice
    form_class = InvoiceForm
    template_name = 'invoice/invoice_form.html'
    success_url = reverse_lazy('invoice_list')
    
    def get_form_kwargs(self):
        """Add user context to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            form.instance.user = self.request.user
            form.instance.invoice_date = timezone.now()
            
            # Validate amount
            if form.cleaned_data.get('item_amount'):
                if form.cleaned_data['item_amount'] <= 0:
                    form.add_error('item_amount', 'Amount must be greater than zero')
                    return self.form_invalid(form)
            
            response = super().form_valid(form)
            messages.success(self.request, 'Invoice created successfully.')
            
            # Invalidate cache
            cache_key = get_cache_key('invoice_list', self.request.user.id)
            CacheMonitor.invalidate_cache(cache_key)
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}", exc_info=True)
            messages.error(self.request, 'An error occurred while creating the invoice.')
            return self.form_invalid(form)

class InvoiceUpdateView(BaseViewMixin, UpdateView):
    """Update an existing invoice."""
    model = PropertyInvoice
    form_class = InvoiceForm
    template_name = 'invoice/invoice_form.html'
    success_url = reverse_lazy('invoice_list')
    
    def get_queryset(self):
        """Get invoice with safe query."""
        return QueryBuilder.safe_filter(
            PropertyInvoice,
            {},
            user_id=self.request.user.id
        )
    
    def get_form_kwargs(self):
        """Add user context to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            # Prevent updating paid invoices
            if form.instance.invoice_paid_date:
                messages.error(self.request, 'Cannot update paid invoices.')
                return self.form_invalid(form)
            
            # Validate amount
            if form.cleaned_data.get('item_amount'):
                if form.cleaned_data['item_amount'] <= 0:
                    form.add_error('item_amount', 'Amount must be greater than zero')
                    return self.form_invalid(form)
            
            response = super().form_valid(form)
            messages.success(self.request, 'Invoice updated successfully.')
            
            # Invalidate cache
            cache_key = get_cache_key('invoice_list', self.request.user.id)
            CacheMonitor.invalidate_cache(cache_key)
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating invoice: {str(e)}", exc_info=True)
            messages.error(self.request, 'An error occurred while updating the invoice.')
            return self.form_invalid(form)

class InvoiceDeleteView(BaseViewMixin, DeleteView):
    """Delete an invoice."""
    model = PropertyInvoice
    template_name = 'invoice/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice_list')
    
    def get_queryset(self):
        """Get invoice with safe query."""
        return QueryBuilder.safe_filter(
            PropertyInvoice,
            {},
            user_id=self.request.user.id
        )
    
    def delete(self, request, *args, **kwargs):
        """Handle deletion with safety checks."""
        try:
            invoice = self.get_object()
            
            # Prevent deletion of paid invoices
            if invoice.invoice_paid_date:
                messages.error(request, 'Cannot delete paid invoices.')
                return self.handle_no_permission()
            
            response = super().delete(request, *args, **kwargs)
            messages.success(request, 'Invoice deleted successfully.')
            
            # Invalidate cache
            cache_key = get_cache_key('invoice_list', request.user.id)
            CacheMonitor.invalidate_cache(cache_key)
            
            return response
            
        except Exception as e:
            logger.error(f"Error deleting invoice: {str(e)}", exc_info=True)
            messages.error(request, 'An error occurred while deleting the invoice.')
            return self.handle_no_permission()

class InvoiceDetailView(BaseViewMixin, DetailView):
    """Show detailed information about an invoice."""
    model = PropertyInvoice
    template_name = 'invoice/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_queryset(self):
        """Get invoice with safe query."""
        return QueryBuilder.safe_filter(
            PropertyInvoice,
            {},
            user_id=self.request.user.id
        ).select_related('property_details')
    
    def get_context_data(self, **kwargs):
        """Get context data with related information."""
        context = super().get_context_data(**kwargs)
        try:
            invoice = self.get_object()
            
            # Get related expenses
            related_expenses = QueryBuilder.safe_filter(
                PropertyExpense,
                {
                    'property_details': invoice.property_details,
                    'expense_date__gte': invoice.invoice_date,
                    'expense_date__lte': invoice.invoice_due_date
                },
                user_id=self.request.user.id
            ).order_by('-expense_date')
            
            # Calculate net income
            total_expenses = related_expenses.aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            context.update({
                'related_expenses': related_expenses,
                'net_income': invoice.item_amount - total_expenses
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting invoice detail context: {str(e)}", exc_info=True)
            return context

class InvoiceAPIView(BaseViewMixin, APIViewMixin):
    """API view for invoice operations."""
    
    def get(self, request, *args, **kwargs):
        """Get invoice data in JSON format."""
        try:
            invoice_id = kwargs.get('pk')
            
            if invoice_id:
                # Get single invoice
                invoice = QueryBuilder.safe_get(
                    PropertyInvoice,
                    {'id': invoice_id},
                    user_id=request.user.id
                )
                
                if not invoice:
                    return self.error_response('Invoice not found.', status=404)
                
                data = {
                    'id': invoice.id,
                    'property': invoice.property_details.property_name,
                    'invoice_number': invoice.invoice_number,
                    'item_amount': str(invoice.item_amount),
                    'invoice_date': invoice.invoice_date.isoformat(),
                    'invoice_due_date': invoice.invoice_due_date.isoformat(),
                    'invoice_paid_date': invoice.invoice_paid_date.isoformat() if invoice.invoice_paid_date else None,
                    'status': 'paid' if invoice.invoice_paid_date else 'unpaid'
                }
                
            else:
                # Get list of invoices
                invoice_list = QueryBuilder.safe_filter(
                    PropertyInvoice,
                    {},
                    user_id=request.user.id
                ).select_related('property_details')
                
                data = [{
                    'id': i.id,
                    'property': i.property_details.property_name,
                    'invoice_number': i.invoice_number,
                    'item_amount': str(i.item_amount),
                    'invoice_date': i.invoice_date.isoformat(),
                    'invoice_due_date': i.invoice_due_date.isoformat(),
                    'invoice_paid_date': i.invoice_paid_date.isoformat() if i.invoice_paid_date else None,
                    'status': 'paid' if i.invoice_paid_date else 'unpaid'
                } for i in invoice_list]
            
            return self.json_response(data)
            
        except Exception as e:
            logger.error(f"Error in invoice API: {str(e)}", exc_info=True)
            return self.error_response('An error occurred while retrieving invoice data.') 