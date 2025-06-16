"""
Base view mixins and utilities for the personal finance application.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.db.models import Model
from django.core.cache import cache
from typing import Any, Dict, Optional
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

class BaseViewMixin(LoginRequiredMixin):
    """Base mixin for all views with common functionality."""
    
    def handle_exception(self, exc: Exception) -> JsonResponse:
        """Handle exceptions in a consistent way."""
        logger.error(f"Error in {self.__class__.__name__}: {str(exc)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(exc)
        }, status=500)

    def get_user_context(self) -> Dict[str, Any]:
        """Get common context data for all views."""
        return {
            'user': self.request.user,
            'is_authenticated': self.request.user.is_authenticated,
        }

    def check_object_permission(self, obj: Model) -> None:
        """Check if the user has permission to access the object."""
        if hasattr(obj, 'user') and obj.user != self.request.user:
            raise PermissionDenied("You don't have permission to access this resource.")

class MessageMixin:
    """Mixin for handling user messages."""
    
    def add_success_message(self, message: str) -> None:
        """Add a success message."""
        messages.success(self.request, message)

    def add_error_message(self, message: str) -> None:
        """Add an error message."""
        messages.error(self.request, message)

    def add_warning_message(self, message: str) -> None:
        """Add a warning message."""
        messages.warning(self.request, message)

    def add_info_message(self, message: str) -> None:
        """Add an info message."""
        messages.info(self.request, message)

class APIViewMixin:
    """Mixin for API views."""
    
    def json_response(self, data: Dict[str, Any], status: int = 200) -> JsonResponse:
        """Return a JSON response."""
        return JsonResponse(data, status=status)

    def error_response(self, message: str, status: int = 400) -> JsonResponse:
        """Return an error response."""
        return JsonResponse({
            'status': 'error',
            'message': message
        }, status=status)

class CacheMixin:
    """Mixin for caching view data."""
    
    CACHE_TIMEOUT = 300  # 5 minutes default timeout
    
    def get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key."""
        # Include user ID in cache key for user-specific data
        key_parts = [prefix, str(self.request.user.id)]
        
        # Add any additional args/kwargs to the key
        if args:
            key_parts.extend([str(arg) for arg in args])
        if kwargs:
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        
        # Create a unique key
        key_string = ":".join(key_parts)
        return f"view_cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get data from cache."""
        return cache.get(cache_key)
    
    def set_cached_data(self, cache_key: str, data: Any, timeout: Optional[int] = None) -> None:
        """Set data in cache."""
        if timeout is None:
            timeout = self.CACHE_TIMEOUT
        cache.set(cache_key, data, timeout)
    
    def invalidate_cache(self, prefix: str, *args, **kwargs) -> None:
        """Invalidate cache for a specific prefix."""
        cache_key = self.get_cache_key(prefix, *args, **kwargs)
        cache.delete(cache_key)
    
    def get_cached_queryset(self, queryset, cache_key: str, timeout: Optional[int] = None) -> Any:
        """Get or set cached queryset."""
        cached_data = self.get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # If not in cache, evaluate queryset and cache it
        data = list(queryset)
        self.set_cached_data(cache_key, data, timeout)
        return data
    
    def get_cached_aggregate(self, queryset, aggregate_func, cache_key: str, timeout: Optional[int] = None) -> Any:
        """Get or set cached aggregate result."""
        cached_data = self.get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # If not in cache, calculate aggregate and cache it
        data = aggregate_func(queryset)
        self.set_cached_data(cache_key, data, timeout)
        return data
    
    def get_cached_context(self, context_func, cache_key: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Get or set cached context data."""
        cached_data = self.get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # If not in cache, calculate context and cache it
        data = context_func()
        self.set_cached_data(cache_key, data, timeout)
        return data 