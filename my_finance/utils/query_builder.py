"""
Query builder utility for safe database operations.
"""
from django.db import models
from django.db.models import Q
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class QueryBuilder:
    """Safe query builder for database operations."""
    
    @staticmethod
    def build_filter_query(
        model: models.Model,
        filters: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Q:
        """
        Build a safe filter query with user context.
        
        Args:
            model: Django model class
            filters: Dictionary of field-value pairs to filter by
            user_id: Optional user ID for access control
            
        Returns:
            Q object for filtering
        """
        try:
            query = Q()
            
            # Add user context if provided
            if user_id and hasattr(model, 'user'):
                query &= Q(user_id=user_id)
            
            # Build safe filters
            for field, value in filters.items():
                if hasattr(model, field):
                    query &= Q(**{field: value})
                else:
                    logger.warning(f"Invalid field {field} for model {model.__name__}")
            
            return query
            
        except Exception as e:
            logger.error(f"Error building query: {str(e)}", exc_info=True)
            return Q()
    
    @staticmethod
    def safe_get(
        model: models.Model,
        filters: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Optional[models.Model]:
        """
        Safely get a single object with filters.
        
        Args:
            model: Django model class
            filters: Dictionary of field-value pairs to filter by
            user_id: Optional user ID for access control
            
        Returns:
            Model instance or None
        """
        try:
            query = QueryBuilder.build_filter_query(model, filters, user_id)
            return model.objects.filter(query).first()
            
        except Exception as e:
            logger.error(f"Error in safe_get: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def safe_filter(
        model: models.Model,
        filters: Dict[str, Any],
        user_id: Optional[int] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> models.QuerySet:
        """
        Safely filter objects with pagination and ordering.
        
        Args:
            model: Django model class
            filters: Dictionary of field-value pairs to filter by
            user_id: Optional user ID for access control
            order_by: List of fields to order by
            limit: Maximum number of results
            
        Returns:
            QuerySet of filtered objects
        """
        try:
            query = QueryBuilder.build_filter_query(model, filters, user_id)
            queryset = model.objects.filter(query)
            
            if order_by:
                queryset = queryset.order_by(*order_by)
            
            if limit:
                queryset = queryset[:limit]
            
            return queryset
            
        except Exception as e:
            logger.error(f"Error in safe_filter: {str(e)}", exc_info=True)
            return model.objects.none()
    
    @staticmethod
    def safe_aggregate(
        model: models.Model,
        filters: Dict[str, Any],
        user_id: Optional[int] = None,
        **aggregations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Safely perform aggregations with filters.
        
        Args:
            model: Django model class
            filters: Dictionary of field-value pairs to filter by
            user_id: Optional user ID for access control
            **aggregations: Aggregation functions to apply
            
        Returns:
            Dictionary of aggregation results
        """
        try:
            query = QueryBuilder.build_filter_query(model, filters, user_id)
            return model.objects.filter(query).aggregate(**aggregations)
            
        except Exception as e:
            logger.error(f"Error in safe_aggregate: {str(e)}", exc_info=True)
            return {} 