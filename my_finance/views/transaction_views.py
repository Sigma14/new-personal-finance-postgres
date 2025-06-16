"""
Transaction-related views for the personal finance application.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Sum, F, Q
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import logging
from datetime import datetime, timedelta

from ..models import Transaction, Account, Category, SubCategory
from ..forms import TransactionForm
from .base import BaseViewMixin, MessageMixin, APIViewMixin

logger = logging.getLogger(__name__)

class TransactionListView(BaseViewMixin, ListView):
    """View for listing all transactions."""
    model = Transaction
    template_name = 'transaction/list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        """Get transactions for the current user with filters."""
        queryset = Transaction.objects.filter(user=self.request.user).select_related(
            'account', 'categories', 'budgets', 'bill'
        ).order_by('-transaction_date')
        
        # Apply filters
        account_id = self.request.GET.get('account')
        category_id = self.request.GET.get('category')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        if category_id:
            queryset = queryset.filter(categories_id=category_id)
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context['accounts'] = Account.objects.filter(user=self.request.user)
        context['categories'] = Category.objects.filter(user=self.request.user)
        context['total_income'] = self.get_queryset().filter(in_flow=True).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        context['total_expense'] = self.get_queryset().filter(out_flow=True).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        return context

class TransactionCreateView(BaseViewMixin, MessageMixin, CreateView):
    """View for creating a new transaction."""
    model = Transaction
    form_class = TransactionForm
    template_name = 'transaction/create.html'
    success_url = reverse_lazy('transaction_list')
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            form.instance.user = self.request.user
            response = super().form_valid(form)
            
            # Update account balance
            account = form.instance.account
            if form.instance.in_flow:
                account.balance += form.instance.amount
            else:
                account.balance -= form.instance.amount
            account.save()
            
            self.add_success_message('Transaction created successfully.')
            return response
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while creating the transaction.')
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class TransactionUpdateView(BaseViewMixin, MessageMixin, UpdateView):
    """View for updating an existing transaction."""
    model = Transaction
    form_class = TransactionForm
    template_name = 'transaction/update.html'
    success_url = reverse_lazy('transaction_list')
    
    def get_queryset(self):
        """Get transaction for the current user."""
        return Transaction.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            old_transaction = self.get_object()
            old_amount = old_transaction.amount
            old_in_flow = old_transaction.in_flow
            
            response = super().form_valid(form)
            
            # Update account balance
            account = form.instance.account
            if old_in_flow:
                account.balance -= old_amount
            else:
                account.balance += old_amount
                
            if form.instance.in_flow:
                account.balance += form.instance.amount
            else:
                account.balance -= form.instance.amount
            account.save()
            
            self.add_success_message('Transaction updated successfully.')
            return response
        except Exception as e:
            logger.error(f"Error updating transaction: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while updating the transaction.')
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class TransactionDeleteView(BaseViewMixin, MessageMixin, DeleteView):
    """View for deleting a transaction."""
    model = Transaction
    success_url = reverse_lazy('transaction_list')
    
    def get_queryset(self):
        """Get transaction for the current user."""
        return Transaction.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Handle transaction deletion."""
        try:
            transaction = self.get_object()
            account = transaction.account
            
            # Update account balance
            if transaction.in_flow:
                account.balance -= transaction.amount
            else:
                account.balance += transaction.amount
            account.save()
            
            response = super().delete(request, *args, **kwargs)
            self.add_success_message('Transaction deleted successfully.')
            return response
        except Exception as e:
            logger.error(f"Error deleting transaction: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while deleting the transaction.')
            return redirect('transaction_list')

class TransactionDetailView(BaseViewMixin, DetailView):
    """View for displaying transaction details."""
    model = Transaction
    template_name = 'transaction/detail.html'
    context_object_name = 'transaction'
    
    def get_queryset(self):
        """Get transaction for the current user."""
        return Transaction.objects.filter(user=self.request.user).select_related(
            'account', 'categories', 'budgets', 'bill'
        )

class TransactionAPIView(APIViewMixin):
    """API view for transaction operations."""
    
    def get(self, request, *args, **kwargs):
        """Get transaction data."""
        try:
            transaction_id = kwargs.get('pk')
            if transaction_id:
                transaction = Transaction.objects.get(id=transaction_id, user=request.user)
                return self.json_response(self.serialize_transaction(transaction))
            
            # Get transactions with filters
            transactions = Transaction.objects.filter(user=request.user)
            
            # Apply filters
            account_id = request.GET.get('account')
            category_id = request.GET.get('category')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if account_id:
                transactions = transactions.filter(account_id=account_id)
            if category_id:
                transactions = transactions.filter(categories_id=category_id)
            if start_date:
                transactions = transactions.filter(transaction_date__gte=start_date)
            if end_date:
                transactions = transactions.filter(transaction_date__lte=end_date)
            
            return self.json_response({
                'transactions': [self.serialize_transaction(t) for t in transactions]
            })
            
        except Transaction.DoesNotExist:
            return self.error_response('Transaction not found.', status=404)
        except Exception as e:
            logger.error(f"Error getting transaction data: {str(e)}", exc_info=True)
            return self.error_response('An error occurred while fetching transaction data.')
    
    def serialize_transaction(self, transaction):
        """Serialize transaction object to dictionary."""
        return {
            'id': transaction.id,
            'amount': str(transaction.amount),
            'date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
            'category': transaction.categories.name if transaction.categories else None,
            'account': transaction.account.name if transaction.account else None,
            'payee': transaction.payee,
            'notes': transaction.notes,
            'in_flow': transaction.in_flow,
            'out_flow': transaction.out_flow,
            'cleared': transaction.cleared,
        } 