"""
Budget-related views for the personal finance application.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Sum, F, Q
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import logging

from ..models import Budget, UserBudgets, Category, SubCategory, Transaction
from ..forms import BudgetForm, UserBudgetsForm
from .base import BaseViewMixin, MessageMixin, APIViewMixin

logger = logging.getLogger(__name__)

class BudgetListView(BaseViewMixin, ListView):
    """View for listing all budgets."""
    model = Budget
    template_name = 'budget/list.html'
    context_object_name = 'budgets'
    
    def get_queryset(self):
        """Get budgets for the current user."""
        return Budget.objects.filter(user=self.request.user).select_related(
            'category', 'account', 'user_budget'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context['total_budget'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        return context

class BudgetCreateView(BaseViewMixin, MessageMixin, CreateView):
    """View for creating a new budget."""
    model = Budget
    form_class = BudgetForm
    template_name = 'budget/create.html'
    success_url = reverse_lazy('budget_list')
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            form.instance.user = self.request.user
            response = super().form_valid(form)
            self.add_success_message('Budget created successfully.')
            return response
        except Exception as e:
            logger.error(f"Error creating budget: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while creating the budget.')
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class BudgetUpdateView(BaseViewMixin, MessageMixin, UpdateView):
    """View for updating an existing budget."""
    model = Budget
    form_class = BudgetForm
    template_name = 'budget/update.html'
    success_url = reverse_lazy('budget_list')
    
    def get_queryset(self):
        """Get budget for the current user."""
        return Budget.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            response = super().form_valid(form)
            self.add_success_message('Budget updated successfully.')
            return response
        except Exception as e:
            logger.error(f"Error updating budget: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while updating the budget.')
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class BudgetDeleteView(BaseViewMixin, MessageMixin, DeleteView):
    """View for deleting a budget."""
    model = Budget
    success_url = reverse_lazy('budget_list')
    
    def get_queryset(self):
        """Get budget for the current user."""
        return Budget.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Handle budget deletion."""
        try:
            response = super().delete(request, *args, **kwargs)
            self.add_success_message('Budget deleted successfully.')
            return response
        except Exception as e:
            logger.error(f"Error deleting budget: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while deleting the budget.')
            return redirect('budget_list')

class BudgetDetailView(BaseViewMixin, DetailView):
    """View for displaying budget details."""
    model = Budget
    template_name = 'budget/detail.html'
    context_object_name = 'budget'
    
    def get_queryset(self):
        """Get budget for the current user."""
        return Budget.objects.filter(user=self.request.user).select_related(
            'category', 'account', 'user_budget'
        )
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        budget = self.get_object()
        
        # Get transactions for this budget
        transactions = Transaction.objects.filter(
            budgets=budget
        ).select_related('account', 'categories').order_by('-transaction_date')
        
        context['transactions'] = transactions
        context['total_spent'] = transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return context

class BudgetAPIView(APIViewMixin):
    """API view for budget operations."""
    
    def get(self, request, *args, **kwargs):
        """Get budget data."""
        try:
            budget_id = kwargs.get('pk')
            if budget_id:
                budget = Budget.objects.get(id=budget_id, user=request.user)
                return self.json_response(self.serialize_budget(budget))
            
            budgets = Budget.objects.filter(user=request.user)
            return self.json_response({
                'budgets': [self.serialize_budget(b) for b in budgets]
            })
            
        except Budget.DoesNotExist:
            return self.error_response('Budget not found.', status=404)
        except Exception as e:
            logger.error(f"Error getting budget data: {str(e)}", exc_info=True)
            return self.error_response('An error occurred while fetching budget data.')
    
    def serialize_budget(self, budget):
        """Serialize budget object to dictionary."""
        return {
            'id': budget.id,
            'name': budget.name,
            'amount': str(budget.amount),
            'spent': str(budget.budget_spent),
            'left': str(budget.budget_left),
            'category': budget.category.name if budget.category else None,
            'period': budget.budget_period,
            'start_date': budget.start_date.isoformat() if budget.start_date else None,
            'end_date': budget.end_date.isoformat() if budget.end_date else None,
        } 