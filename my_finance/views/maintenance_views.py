"""
Views for handling property maintenance requests.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
import logging

from ..models import PropertyMaintenance, PropertyExpense
from ..forms import MaintenanceForm
from ..permissions import MaintenancePermissionMixin, get_user_maintenance
from ..utils.query_builder import QueryBuilder
from ..utils.cache import get_cache_key, CacheMonitor
from .base import BaseViewMixin, APIViewMixin

logger = logging.getLogger(__name__)

class MaintenanceListView(BaseViewMixin, ListView):
    """List all maintenance requests for user's properties."""
    model = PropertyMaintenance
    template_name = 'maintenance/maintenance_list.html'
    context_object_name = 'maintenance_requests'
    
    def get_queryset(self):
        """Get maintenance requests with safe query."""
        try:
            return QueryBuilder.safe_filter(
                PropertyMaintenance,
                {},
                user_id=self.request.user.id
            ).select_related(
                'property_details'
            ).order_by('-request_date')
        except Exception as e:
            logger.error(f"Error getting maintenance list: {str(e)}", exc_info=True)
            return PropertyMaintenance.objects.none()
    
    def get_context_data(self, **kwargs):
        """Get context data with statistics."""
        context = super().get_context_data(**kwargs)
        try:
            # Get maintenance statistics
            stats = QueryBuilder.safe_aggregate(
                PropertyMaintenance,
                {},
                user_id=self.request.user.id,
                total_requests=Count('id'),
                pending_requests=Count('id', filter=Q(status='pending')),
                completed_requests=Count('id', filter=Q(status='completed')),
                total_cost=Sum('cost')
            )
            
            # Get recent completed requests
            recent_completed = QueryBuilder.safe_filter(
                PropertyMaintenance,
                {'status': 'completed'},
                user_id=self.request.user.id,
                order_by=['-completion_date'],
                limit=5
            ).select_related('property_details')
            
            context.update({
                'stats': stats,
                'recent_completed': recent_completed
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting maintenance context: {str(e)}", exc_info=True)
            return context

class MaintenanceCreateView(BaseViewMixin, CreateView):
    """Create a new maintenance request."""
    model = PropertyMaintenance
    form_class = MaintenanceForm
    template_name = 'maintenance/maintenance_form.html'
    success_url = reverse_lazy('maintenance_list')
    
    def get_form_kwargs(self):
        """Add user context to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle valid form submission."""
        try:
            form.instance.user = self.request.user
            form.instance.status = 'pending'
            form.instance.request_date = timezone.now()
            
            # Validate cost
            if form.cleaned_data.get('cost'):
                if form.cleaned_data['cost'] < 0:
                    form.add_error('cost', 'Cost cannot be negative')
                    return self.form_invalid(form)
            
            response = super().form_valid(form)
            messages.success(self.request, 'Maintenance request created successfully.')
            
            # Invalidate cache
            cache_key = get_cache_key('maintenance_list', self.request.user.id)
            CacheMonitor.invalidate_cache(cache_key)
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating maintenance request: {str(e)}", exc_info=True)
            messages.error(self.request, 'An error occurred while creating the maintenance request.')
            return self.form_invalid(form)

class MaintenanceUpdateView(BaseViewMixin, UpdateView):
    """Update an existing maintenance request."""
    model = PropertyMaintenance
    form_class = MaintenanceForm
    template_name = 'maintenance/maintenance_form.html'
    success_url = reverse_lazy('maintenance_list')
    
    def get_queryset(self):
        """Get maintenance request with safe query."""
        return QueryBuilder.safe_filter(
            PropertyMaintenance,
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
            # Set completion date if status changed to completed
            if form.instance.status != form.cleaned_data['status'] and form.cleaned_data['status'] == 'completed':
                form.instance.completion_date = timezone.now()
            
            # Validate cost
            if form.cleaned_data.get('cost'):
                if form.cleaned_data['cost'] < 0:
                    form.add_error('cost', 'Cost cannot be negative')
                    return self.form_invalid(form)
            
            response = super().form_valid(form)
            messages.success(self.request, 'Maintenance request updated successfully.')
            
            # Invalidate cache
            cache_key = get_cache_key('maintenance_list', self.request.user.id)
            CacheMonitor.invalidate_cache(cache_key)
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating maintenance request: {str(e)}", exc_info=True)
            messages.error(self.request, 'An error occurred while updating the maintenance request.')
            return self.form_invalid(form)

class MaintenanceDeleteView(BaseViewMixin, DeleteView):
    """Delete a maintenance request."""
    model = PropertyMaintenance
    template_name = 'maintenance/maintenance_confirm_delete.html'
    success_url = reverse_lazy('maintenance_list')
    
    def get_queryset(self):
        """Get maintenance request with safe query."""
        return QueryBuilder.safe_filter(
            PropertyMaintenance,
            {},
            user_id=self.request.user.id
        )
    
    def delete(self, request, *args, **kwargs):
        """Handle deletion with safety checks."""
        try:
            maintenance = self.get_object()
            
            # Prevent deletion of completed requests
            if maintenance.status == 'completed':
                messages.error(request, 'Cannot delete completed maintenance requests.')
                return self.handle_no_permission()
            
            # Check for related expenses
            related_expenses = QueryBuilder.safe_filter(
                PropertyExpense,
                {'maintenance_request': maintenance},
                user_id=request.user.id
            ).exists()
            
            if related_expenses:
                messages.error(request, 'Cannot delete maintenance request with related expenses.')
                return self.handle_no_permission()
            
            response = super().delete(request, *args, **kwargs)
            messages.success(request, 'Maintenance request deleted successfully.')
            
            # Invalidate cache
            cache_key = get_cache_key('maintenance_list', request.user.id)
            CacheMonitor.invalidate_cache(cache_key)
            
            return response
            
        except Exception as e:
            logger.error(f"Error deleting maintenance request: {str(e)}", exc_info=True)
            messages.error(request, 'An error occurred while deleting the maintenance request.')
            return self.handle_no_permission()

class MaintenanceDetailView(BaseViewMixin, DetailView):
    """Show detailed information about a maintenance request."""
    model = PropertyMaintenance
    template_name = 'maintenance/maintenance_detail.html'
    context_object_name = 'maintenance'
    
    def get_queryset(self):
        """Get maintenance request with safe query."""
        return QueryBuilder.safe_filter(
            PropertyMaintenance,
            {},
            user_id=self.request.user.id
        ).select_related('property_details')
    
    def get_context_data(self, **kwargs):
        """Get context data with related information."""
        context = super().get_context_data(**kwargs)
        try:
            maintenance = self.get_object()
            
            # Get related expenses
            related_expenses = QueryBuilder.safe_filter(
                PropertyExpense,
                {'maintenance_request': maintenance},
                user_id=self.request.user.id
            ).order_by('-expense_date')
            
            # Get similar maintenance requests
            similar_requests = QueryBuilder.safe_filter(
                PropertyMaintenance,
                {
                    'property_details': maintenance.property_details,
                    'id__ne': maintenance.id
                },
                user_id=self.request.user.id,
                order_by=['-request_date'],
                limit=5
            ).select_related('property_details')
            
            context.update({
                'related_expenses': related_expenses,
                'similar_requests': similar_requests
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting maintenance detail context: {str(e)}", exc_info=True)
            return context

class MaintenanceAPIView(BaseViewMixin, APIViewMixin):
    """API view for maintenance operations."""
    
    def get(self, request, *args, **kwargs):
        """Get maintenance data in JSON format."""
        try:
            maintenance_id = kwargs.get('pk')
            
            if maintenance_id:
                # Get single maintenance request
                maintenance = QueryBuilder.safe_get(
                    PropertyMaintenance,
                    {'id': maintenance_id},
                    user_id=request.user.id
                )
                
                if not maintenance:
                    return self.error_response('Maintenance request not found.', status=404)
                
                data = {
                    'id': maintenance.id,
                    'property': maintenance.property_details.property_name,
                    'description': maintenance.description,
                    'status': maintenance.status,
                    'request_date': maintenance.request_date.isoformat(),
                    'completion_date': maintenance.completion_date.isoformat() if maintenance.completion_date else None,
                    'cost': str(maintenance.cost) if maintenance.cost else None
                }
                
            else:
                # Get list of maintenance requests
                maintenance_list = QueryBuilder.safe_filter(
                    PropertyMaintenance,
                    {},
                    user_id=request.user.id
                ).select_related('property_details')
                
                data = [{
                    'id': m.id,
                    'property': m.property_details.property_name,
                    'description': m.description,
                    'status': m.status,
                    'request_date': m.request_date.isoformat(),
                    'completion_date': m.completion_date.isoformat() if m.completion_date else None,
                    'cost': str(m.cost) if m.cost else None
                } for m in maintenance_list]
            
            return self.json_response(data)
            
        except Exception as e:
            logger.error(f"Error in maintenance API: {str(e)}", exc_info=True)
            return self.error_response('An error occurred while retrieving maintenance data.') 