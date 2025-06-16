"""
Views for handling property expenses.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
import logging

from ..models import PropertyExpense, PropertyMaintenance
from ..forms import ExpenseForm
from ..permissions import ExpensePermissionMixin, get_user_expenses
from ..utils.query_builder import QueryBuilder
from ..utils.cache import get_cache_key, CacheMonitor
from .base import BaseViewMixin, APIViewMixin

logger = logging.getLogger(__name__)

class ExpenseListView(BaseViewMixin, ListView):
    """List all expenses for user's properties."""
    model = PropertyExpense
    template_name = 'expense/expense_list.html'
    context_object_name = 'expenses'
    
    def get_queryset(self):
        """Get expenses with safe query."""
        try:
            return QueryBuilder.safe_filter(
                PropertyExpense,
                {},
                user_id=self.request.user.id
            ).select_related(
                'property_details',
                'maintenance_request'
            ).order_by('-expense_date')
        except Exception as e:
            logger.error(f"Error getting expense list: {str(e)}", exc_info=True)
            return PropertyExpense.objects.none()
    
    def get_context_data(self, **kwargs):
        """Get context data with statistics."""
        context = super().get_context_data(**kwargs)
        try:
            # Get expense statistics
            stats = QueryBuilder.safe_aggregate(
                PropertyExpense,
                {},
                user_id=self.request.user.id,
                total_expenses=Count('id'),
                total_amount=Sum('amount'),
                monthly_amount=Sum('amount', filter=Q(
                    expense_date__gte=timezone.now().replace(day=1)
                ))
            )
            
            # Get expense categories
            categories = QueryBuilder.safe_filter(
                PropertyExpense,
                {},
                user_id=self.request.user.id
            ).values(
                'expense_category'
            ).annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('-total')
            
            # Get recent expenses
            recent_expenses = QueryBuilder.safe_filter(
                PropertyExpense,
                {},
                user_id=self.request.user.id,
                order_by=['-expense_date'],
                limit=5
            ).select_related('property_details')
            
            context.update({
                'stats': stats,
                'categories': categories,
                'recent_expenses': recent_expenses
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting expense context: {str(e)}", exc_info=True)
            return context

class ExpenseCreateView(BaseViewMixin, CreateView):
    """Create a new expense."""
    model = PropertyExpense
    form_class = ExpenseForm
    template_name = 'expense/expense_form.html'
    success_url = reverse_lazy('expense_list')
    
    def get_form_kwargs(self):
        """Add user context to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            form.instance.user = self.request.user
            form.instance.expense_date = timezone.now()
            
            # Validate amount
            if form.cleaned_data.get('amount'):
                if form.cleaned_data['amount'] <= 0:
                    form.add_error('amount', 'Amount must be greater than zero')
                    return self.form_invalid(form)
            
            # Validate maintenance request if provided
            if form.cleaned_data.get('maintenance_request'):
                maintenance = form.cleaned_data['maintenance_request']
                if maintenance.property_details != form.cleaned_data['property_details']:
                    form.add_error('maintenance_request', 'Maintenance request must be for the same property')
                    return self.form_invalid(form)
            
            response = super().form_valid(form)
            messages.success(self.request, 'Expense created successfully.')
            
            # Invalidate cache
            cache_key = get_cache_key('expense_list', self.request.user.id)
            CacheMonitor.invalidate_cache(cache_key)
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating expense: {str(e)}", exc_info=True)
            messages.error(self.request, 'An error occurred while creating the expense.')
            return self.form_invalid(form)

class ExpenseUpdateView(BaseViewMixin, UpdateView):
    """Update an existing expense."""
    model = PropertyExpense
    form_class = ExpenseForm
    template_name = 'expense/expense_form.html'
    success_url = reverse_lazy('expense_list')
    
    def get_queryset(self):
        """Get expense with safe query."""
        return QueryBuilder.safe_filter(
            PropertyExpense,
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
            # Validate amount
            if form.cleaned_data.get('amount'):
                if form.cleaned_data['amount'] <= 0:
                    form.add_error('amount', 'Amount must be greater than zero')
                    return self.form_invalid(form)
            
            # Validate maintenance request if provided
            if form.cleaned_data.get('maintenance_request'):
                maintenance = form.cleaned_data['maintenance_request']
                if maintenance.property_details != form.cleaned_data['property_details']:
                    form.add_error('maintenance_request', 'Maintenance request must be for the same property')
                    return self.form_invalid(form)
            
            response = super().form_valid(form)
            messages.success(self.request, 'Expense updated successfully.')
            
            # Invalidate cache
            cache_key = get_cache_key('expense_list', self.request.user.id)
            CacheMonitor.invalidate_cache(cache_key)
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating expense: {str(e)}", exc_info=True)
            messages.error(self.request, 'An error occurred while updating the expense.')
            return self.form_invalid(form)

class ExpenseDeleteView(BaseViewMixin, DeleteView):
    """Delete an expense."""
    model = PropertyExpense
    template_name = 'expense/expense_confirm_delete.html'
    success_url = reverse_lazy('expense_list')
    
    def get_queryset(self):
        """Get expense with safe query."""
        return QueryBuilder.safe_filter(
            PropertyExpense,
            {},
            user_id=self.request.user.id
        )
    
    def delete(self, request, *args, **kwargs):
        """Handle deletion with safety checks."""
        try:
            expense = self.get_object()
            
            # Check for related maintenance requests
            if expense.maintenance_request:
                messages.error(request, 'Cannot delete expense related to a maintenance request.')
                return self.handle_no_permission()
            
            response = super().delete(request, *args, **kwargs)
            messages.success(request, 'Expense deleted successfully.')
            
            # Invalidate cache
            cache_key = get_cache_key('expense_list', request.user.id)
            CacheMonitor.invalidate_cache(cache_key)
            
            return response
            
        except Exception as e:
            logger.error(f"Error deleting expense: {str(e)}", exc_info=True)
            messages.error(request, 'An error occurred while deleting the expense.')
            return self.handle_no_permission()

class ExpenseDetailView(BaseViewMixin, DetailView):
    """Show detailed information about an expense."""
    model = PropertyExpense
    template_name = 'expense/expense_detail.html'
    context_object_name = 'expense'
    
    def get_queryset(self):
        """Get expense with safe query."""
        return QueryBuilder.safe_filter(
            PropertyExpense,
            {},
            user_id=self.request.user.id
        ).select_related('property_details', 'maintenance_request')
    
    def get_context_data(self, **kwargs):
        """Get context data with related information."""
        context = super().get_context_data(**kwargs)
        try:
            expense = self.get_object()
            
            # Get similar expenses
            similar_expenses = QueryBuilder.safe_filter(
                PropertyExpense,
                {
                    'property_details': expense.property_details,
                    'expense_category': expense.expense_category,
                    'id__ne': expense.id
                },
                user_id=self.request.user.id,
                order_by=['-expense_date'],
                limit=5
            ).select_related('property_details')
            
            # Get monthly category totals
            monthly_totals = QueryBuilder.safe_filter(
                PropertyExpense,
                {
                    'property_details': expense.property_details,
                    'expense_date__year': expense.expense_date.year,
                    'expense_date__month': expense.expense_date.month
                },
                user_id=self.request.user.id
            ).values(
                'expense_category'
            ).annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            context.update({
                'similar_expenses': similar_expenses,
                'monthly_totals': monthly_totals
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting expense detail context: {str(e)}", exc_info=True)
            return context

class ExpenseAPIView(BaseViewMixin, APIViewMixin):
    """API view for expense operations."""
    
    def get(self, request, *args, **kwargs):
        """Get expense data in JSON format."""
        try:
            expense_id = kwargs.get('pk')
            
            if expense_id:
                # Get single expense
                expense = QueryBuilder.safe_get(
                    PropertyExpense,
                    {'id': expense_id},
                    user_id=request.user.id
                )
                
                if not expense:
                    return self.error_response('Expense not found.', status=404)
                
                data = {
                    'id': expense.id,
                    'property': expense.property_details.property_name,
                    'expense_category': expense.expense_category,
                    'amount': str(expense.amount),
                    'expense_date': expense.expense_date.isoformat(),
                    'description': expense.description,
                    'maintenance_request': expense.maintenance_request.id if expense.maintenance_request else None
                }
                
            else:
                # Get list of expenses
                expense_list = QueryBuilder.safe_filter(
                    PropertyExpense,
                    {},
                    user_id=request.user.id
                ).select_related('property_details', 'maintenance_request')
                
                data = [{
                    'id': e.id,
                    'property': e.property_details.property_name,
                    'expense_category': e.expense_category,
                    'amount': str(e.amount),
                    'expense_date': e.expense_date.isoformat(),
                    'description': e.description,
                    'maintenance_request': e.maintenance_request.id if e.maintenance_request else None
                } for e in expense_list]
            
            return self.json_response(data)
            
        except Exception as e:
            logger.error(f"Error in expense API: {str(e)}", exc_info=True)
            return self.error_response('An error occurred while retrieving expense data.') 