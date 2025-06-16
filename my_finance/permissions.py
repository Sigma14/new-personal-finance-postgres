"""
Custom permissions for the personal finance application.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class PropertyPermissionMixin(UserPassesTestMixin):
    """Mixin to handle property-related permissions."""
    
    def test_func(self) -> bool:
        """Test if user has permission to access the property."""
        try:
            obj = self.get_object()
            return obj.user == self.request.user
        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}", exc_info=True)
            return False

    def handle_no_permission(self) -> None:
        """Handle failed permission check."""
        raise PermissionDenied("You don't have permission to access this resource.")

class RentalPermissionMixin(UserPassesTestMixin):
    """Mixin to handle rental-related permissions."""
    
    def test_func(self) -> bool:
        """Test if user has permission to access the rental info."""
        try:
            obj = self.get_object()
            return obj.property_address.user == self.request.user
        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}", exc_info=True)
            return False

    def handle_no_permission(self) -> None:
        """Handle failed permission check."""
        raise PermissionDenied("You don't have permission to access this resource.")

class MaintenancePermissionMixin(UserPassesTestMixin):
    """Mixin to handle maintenance-related permissions."""
    
    def test_func(self) -> bool:
        """Test if user has permission to access the maintenance request."""
        try:
            obj = self.get_object()
            return obj.property_details.user == self.request.user
        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}", exc_info=True)
            return False

    def handle_no_permission(self) -> None:
        """Handle failed permission check."""
        raise PermissionDenied("You don't have permission to access this resource.")

class InvoicePermissionMixin(UserPassesTestMixin):
    """Mixin to handle invoice-related permissions."""
    
    def test_func(self) -> bool:
        """Test if user has permission to access the invoice."""
        try:
            obj = self.get_object()
            return obj.property_details.user == self.request.user
        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}", exc_info=True)
            return False

    def handle_no_permission(self) -> None:
        """Handle failed permission check."""
        raise PermissionDenied("You don't have permission to access this resource.")

def get_user_properties(user: Any) -> Q:
    """Get query filter for user's properties."""
    return Q(user=user)

def get_user_rentals(user: Any) -> Q:
    """Get query filter for user's rental properties."""
    return Q(property_address__user=user)

def get_user_maintenance(user: Any) -> Q:
    """Get query filter for user's maintenance requests."""
    return Q(property_details__user=user)

def get_user_invoices(user: Any) -> Q:
    """Get query filter for user's invoices."""
    return Q(property_details__user=user) 