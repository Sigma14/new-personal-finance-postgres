"""
Views for the dashboard functionality.
"""
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from django.core.cache import cache
import logging

from ..models import (
    Property, PropertyRentalInfo, PropertyMaintenance,
    PropertyExpense, PropertyInvoice
)
from ..utils.query_builder import QueryBuilder
from ..utils.cache import get_cache_key, CacheMonitor
from .base import BaseViewMixin, APIViewMixin

logger = logging.getLogger(__name__)

class DashboardView(BaseViewMixin, TemplateView):
    """Main dashboard view showing property overview."""
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        """Get dashboard data with caching."""
        context = super().get_context_data(**kwargs)
        try:
            # Try to get cached data
            cache_key = get_cache_key('dashboard', self.request.user.id)
            cached_data = cache.get(cache_key)
            
            if cached_data:
                CacheMonitor.increment_hit('dashboard')
                return {**context, **cached_data}
            
            CacheMonitor.increment_miss('dashboard')
            
            # Get property statistics
            property_stats = QueryBuilder.safe_aggregate(
                Property,
                {},
                user_id=self.request.user.id,
                total_properties=Count('id'),
                total_value=Sum('property_value'),
                total_monthly_rent=Sum('property_rental_info__monthly_rent')
            )
            
            # Get maintenance statistics
            maintenance_stats = QueryBuilder.safe_aggregate(
                PropertyMaintenance,
                {},
                user_id=self.request.user.id,
                total_requests=Count('id'),
                pending_requests=Count('id', filter=Q(status='pending')),
                completed_requests=Count('id', filter=Q(status='completed')),
                total_cost=Sum('cost')
            )
            
            # Get expense statistics
            expense_stats = QueryBuilder.safe_aggregate(
                PropertyExpense,
                {},
                user_id=self.request.user.id,
                total_expenses=Count('id'),
                total_amount=Sum('amount'),
                monthly_amount=Sum('amount', filter=Q(
                    expense_date__gte=timezone.now().replace(day=1)
                ))
            )
            
            # Get invoice statistics
            invoice_stats = QueryBuilder.safe_aggregate(
                PropertyInvoice,
                {},
                user_id=self.request.user.id,
                total_invoices=Count('id'),
                total_amount=Sum('amount'),
                overdue_amount=Sum('amount', filter=Q(
                    due_date__lt=timezone.now(),
                    status='pending'
                ))
            )
            
            # Get recent maintenance requests
            recent_maintenance = QueryBuilder.safe_filter(
                PropertyMaintenance,
                {},
                user_id=self.request.user.id,
                order_by=['-request_date'],
                limit=5
            ).select_related('property_details')
            
            # Get recent expenses
            recent_expenses = QueryBuilder.safe_filter(
                PropertyExpense,
                {},
                user_id=self.request.user.id,
                order_by=['-expense_date'],
                limit=5
            ).select_related('property_details')
            
            # Get recent invoices
            recent_invoices = QueryBuilder.safe_filter(
                PropertyInvoice,
                {},
                user_id=self.request.user.id,
                order_by=['-invoice_date'],
                limit=5
            ).select_related('property_details')
            
            # Get property performance metrics
            property_performance = QueryBuilder.safe_filter(
                Property,
                {},
                user_id=self.request.user.id
            ).annotate(
                total_income=Sum('property_rental_info__monthly_rent'),
                total_expenses=Sum('property_expense__amount'),
                total_maintenance=Sum('property_maintenance__cost'),
                occupancy_rate=Avg('property_rental_info__occupancy_rate')
            ).order_by('-total_income')
            
            # Calculate net monthly income
            net_monthly_income = (
                property_stats.get('total_monthly_rent', 0) -
                expense_stats.get('monthly_amount', 0)
            )
            
            # Prepare context data
            dashboard_data = {
                'property_stats': property_stats,
                'maintenance_stats': maintenance_stats,
                'expense_stats': expense_stats,
                'invoice_stats': invoice_stats,
                'recent_maintenance': recent_maintenance,
                'recent_expenses': recent_expenses,
                'recent_invoices': recent_invoices,
                'property_performance': property_performance,
                'net_monthly_income': net_monthly_income
            }
            
            # Cache the data
            cache.set(cache_key, dashboard_data, timeout=300)  # 5 minutes
            
            return {**context, **dashboard_data}
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}", exc_info=True)
            return context

class DashboardAPIView(BaseViewMixin, APIViewMixin):
    """API view for dashboard data."""
    
    def get(self, request, *args, **kwargs):
        """Get dashboard data in JSON format."""
        try:
            # Try to get cached data
            cache_key = get_cache_key('dashboard_api', request.user.id)
            cached_data = cache.get(cache_key)
            
            if cached_data:
                CacheMonitor.increment_hit('dashboard_api')
                return self.json_response(cached_data)
            
            CacheMonitor.increment_miss('dashboard_api')
            
            # Get monthly income
            monthly_income = QueryBuilder.safe_aggregate(
                PropertyRentalInfo,
                {},
                user_id=request.user.id,
                total=Sum('monthly_rent')
            )
            
            # Get monthly expenses
            monthly_expenses = QueryBuilder.safe_aggregate(
                PropertyExpense,
                {
                    'expense_date__gte': timezone.now().replace(day=1)
                },
                user_id=request.user.id,
                total=Sum('amount')
            )
            
            # Get maintenance statistics
            maintenance_stats = QueryBuilder.safe_aggregate(
                PropertyMaintenance,
                {},
                user_id=request.user.id,
                total_requests=Count('id'),
                pending_requests=Count('id', filter=Q(status='pending')),
                completed_requests=Count('id', filter=Q(status='completed'))
            )
            
            # Get total properties
            total_properties = QueryBuilder.safe_aggregate(
                Property,
                {},
                user_id=request.user.id,
                total=Count('id')
            )
            
            # Prepare response data
            data = {
                'monthly_income': monthly_income.get('total', 0),
                'monthly_expenses': monthly_expenses.get('total', 0),
                'maintenance_stats': maintenance_stats,
                'total_properties': total_properties.get('total', 0)
            }
            
            # Cache the data
            cache.set(cache_key, data, timeout=300)  # 5 minutes
            
            return self.json_response(data)
            
        except Exception as e:
            logger.error(f"Error in dashboard API: {str(e)}", exc_info=True)
            return self.error_response('An error occurred while retrieving dashboard data.') 