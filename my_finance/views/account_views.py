"""
Account-related views for the personal finance application.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Sum, F, Q
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import logging
from datetime import datetime, timedelta

from ..models import Account, Transaction, PlaidItem
from ..forms import AccountForm
from .base import BaseViewMixin, MessageMixin, APIViewMixin

logger = logging.getLogger(__name__)

class AccountListView(BaseViewMixin, ListView):
    """View for listing all accounts."""
    model = Account
    template_name = 'account/list.html'
    context_object_name = 'accounts'
    
    def get_queryset(self):
        """Get accounts for the current user."""
        return Account.objects.filter(user=self.request.user).select_related(
            'item'
        ).order_by('name')
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        accounts = self.get_queryset()
        
        # Calculate total balance
        context['total_balance'] = accounts.aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0.00')
        
        # Calculate total available balance
        context['total_available'] = accounts.aggregate(
            total=Sum('available_balance')
        )['total'] or Decimal('0.00')
        
        # Get recent transactions for each account
        for account in accounts:
            account.recent_transactions = Transaction.objects.filter(
                account=account
            ).order_by('-transaction_date')[:5]
        
        return context

class AccountCreateView(BaseViewMixin, MessageMixin, CreateView):
    """View for creating a new account."""
    model = Account
    form_class = AccountForm
    template_name = 'account/create.html'
    success_url = reverse_lazy('account_list')
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            form.instance.user = self.request.user
            response = super().form_valid(form)
            self.add_success_message('Account created successfully.')
            return response
        except Exception as e:
            logger.error(f"Error creating account: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while creating the account.')
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class AccountUpdateView(BaseViewMixin, MessageMixin, UpdateView):
    """View for updating an existing account."""
    model = Account
    form_class = AccountForm
    template_name = 'account/update.html'
    success_url = reverse_lazy('account_list')
    
    def get_queryset(self):
        """Get account for the current user."""
        return Account.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            response = super().form_valid(form)
            self.add_success_message('Account updated successfully.')
            return response
        except Exception as e:
            logger.error(f"Error updating account: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while updating the account.')
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class AccountDeleteView(BaseViewMixin, MessageMixin, DeleteView):
    """View for deleting an account."""
    model = Account
    success_url = reverse_lazy('account_list')
    
    def get_queryset(self):
        """Get account for the current user."""
        return Account.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Handle account deletion."""
        try:
            account = self.get_object()
            
            # Check if account has transactions
            if Transaction.objects.filter(account=account).exists():
                self.add_error_message('Cannot delete account with existing transactions.')
                return redirect('account_list')
            
            response = super().delete(request, *args, **kwargs)
            self.add_success_message('Account deleted successfully.')
            return response
        except Exception as e:
            logger.error(f"Error deleting account: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while deleting the account.')
            return redirect('account_list')

class AccountDetailView(BaseViewMixin, DetailView):
    """View for displaying account details."""
    model = Account
    template_name = 'account/detail.html'
    context_object_name = 'account'
    
    def get_queryset(self):
        """Get account for the current user."""
        return Account.objects.filter(user=self.request.user).select_related('item')
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        account = self.get_object()
        
        # Get recent transactions
        context['recent_transactions'] = Transaction.objects.filter(
            account=account
        ).select_related('categories').order_by('-transaction_date')[:10]
        
        # Get monthly totals
        today = timezone.now()
        first_day = today.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_income = Transaction.objects.filter(
            account=account,
            transaction_date__gte=first_day,
            transaction_date__lte=last_day,
            in_flow=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        monthly_expense = Transaction.objects.filter(
            account=account,
            transaction_date__gte=first_day,
            transaction_date__lte=last_day,
            out_flow=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        context['monthly_income'] = monthly_income
        context['monthly_expense'] = monthly_expense
        context['monthly_net'] = monthly_income - monthly_expense
        
        return context

class AccountAPIView(APIViewMixin):
    """API view for account operations."""
    
    def get(self, request, *args, **kwargs):
        """Get account data."""
        try:
            account_id = kwargs.get('pk')
            if account_id:
                account = Account.objects.get(id=account_id, user=request.user)
                return self.json_response(self.serialize_account(account))
            
            accounts = Account.objects.filter(user=request.user)
            return self.json_response({
                'accounts': [self.serialize_account(a) for a in accounts]
            })
            
        except Account.DoesNotExist:
            return self.error_response('Account not found.', status=404)
        except Exception as e:
            logger.error(f"Error getting account data: {str(e)}", exc_info=True)
            return self.error_response('An error occurred while fetching account data.')
    
    def serialize_account(self, account):
        """Serialize account object to dictionary."""
        return {
            'id': account.id,
            'name': account.name,
            'type': account.account_type,
            'balance': str(account.balance),
            'available_balance': str(account.available_balance),
            'currency': account.currency,
            'include_net_worth': account.include_net_worth,
            'plaid_account_id': account.plaid_account_id,
            'mask': account.mask,
            'subtype': account.subtype,
        } 