"""
Cache utilities for the application.
"""
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging
from datetime import datetime

from ..models import (
    Property, PropertyRentalInfo, PropertyInvoice,
    PropertyExpense, PropertyMaintenance
)

logger = logging.getLogger(__name__)

def get_cache_key(prefix, user_id):
    """Generate a cache key with prefix and user ID."""
    return f'{prefix}_{user_id}'

def invalidate_dashboard_cache(user_id):
    """Invalidate all dashboard-related cache for a user."""
    keys = [
        get_cache_key('dashboard_data', user_id),
        get_cache_key('dashboard_api_data', user_id),
        get_cache_key('property_performance', user_id),
        get_cache_key('expense_categories', user_id)
    ]
    
    for key in keys:
        cache.delete(key)
    
    logger.info(f"Invalidated dashboard cache for user {user_id}")

def log_cache_operation(operation, key, hit=None):
    """Log cache operations for monitoring."""
    timestamp = datetime.now().isoformat()
    log_data = {
        'timestamp': timestamp,
        'operation': operation,
        'key': key,
        'hit': hit
    }
    logger.info(f"Cache operation: {log_data}")

# Signal handlers for cache invalidation
@receiver([post_save, post_delete], sender=Property)
@receiver([post_save, post_delete], sender=PropertyRentalInfo)
@receiver([post_save, post_delete], sender=PropertyInvoice)
@receiver([post_save, post_delete], sender=PropertyExpense)
@receiver([post_save, post_delete], sender=PropertyMaintenance)
def invalidate_cache(sender, instance, **kwargs):
    """Invalidate cache when related models are modified."""
    try:
        if hasattr(instance, 'property_details'):
            user_id = instance.property_details.user.id
        elif hasattr(instance, 'user'):
            user_id = instance.user.id
        else:
            return
        
        invalidate_dashboard_cache(user_id)
        logger.info(f"Cache invalidated for {sender.__name__} change")
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}", exc_info=True)

class CacheMonitor:
    """Monitor cache operations and performance."""
    
    @staticmethod
    def get_cache_stats():
        """Get cache statistics."""
        try:
            stats = {
                'hits': cache.get('cache_hits', 0),
                'misses': cache.get('cache_misses', 0),
                'invalidations': cache.get('cache_invalidations', 0)
            }
            total = stats['hits'] + stats['misses']
            stats['hit_rate'] = (stats['hits'] / total * 100) if total > 0 else 0
            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def increment_hit():
        """Increment cache hit counter."""
        try:
            cache.incr('cache_hits', 1)
        except ValueError:
            cache.set('cache_hits', 1)
    
    @staticmethod
    def increment_miss():
        """Increment cache miss counter."""
        try:
            cache.incr('cache_misses', 1)
        except ValueError:
            cache.set('cache_misses', 1)
    
    @staticmethod
    def increment_invalidation():
        """Increment cache invalidation counter."""
        try:
            cache.incr('cache_invalidations', 1)
        except ValueError:
            cache.set('cache_invalidations', 1)
    
    @staticmethod
    def reset_stats():
        """Reset cache statistics."""
        cache.delete_many(['cache_hits', 'cache_misses', 'cache_invalidations']) 