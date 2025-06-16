from django.utils.functional import SimpleLazyObject
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

def get_user_from_jwt(request):
    """
    Get user from JWT token in cookie.
    """
    # Get the token from the cookie
    access_token = request.COOKIES.get('access_token')
    
    if not access_token:
        return None
    
    # Create a JWT authentication instance
    jwt_auth = JWTAuthentication()
    
    try:
        # Validate the token
        validated_token = jwt_auth.get_validated_token(access_token)
        # Get the user from the token
        user = jwt_auth.get_user(validated_token)
        return user
    except (InvalidToken, TokenError):
        return None

class JWTCookieMiddleware:
    """
    Middleware to authenticate users via JWT tokens in cookies for both
    Django views and DRF views.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Process the request before the view is called
        
        # If user is not authenticated via session, try JWT
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            # Ensure that we don't have recursion when setting the user
            if request.user is None:
                request.user = SimpleLazyObject(lambda: get_user_from_jwt(request) or None)
        
        # Call the next middleware or view
        response = self.get_response(request)
        
        return response

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add security headers to all responses."""
    
    def process_response(self, request, response):
        """Add security headers to the response."""
        try:
            # Content Security Policy
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self';"
            )
            
            # X-Frame-Options
            response['X-Frame-Options'] = 'DENY'
            
            # X-Content-Type-Options
            response['X-Content-Type-Options'] = 'nosniff'
            
            # X-XSS-Protection
            response['X-XSS-Protection'] = '1; mode=block'
            
            # Referrer-Policy
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions-Policy
            response['Permissions-Policy'] = (
                "accelerometer=(), "
                "camera=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "payment=(), "
                "usb=()"
            )
            
            # Strict-Transport-Security
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding security headers: {str(e)}", exc_info=True)
            return response

class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log request information."""
    
    def process_request(self, request):
        """Log request information."""
        try:
            # Log request method and path
            logger.info(
                f"Request: {request.method} {request.path}",
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'ip': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')
                }
            )
        except Exception as e:
            logger.error(f"Error logging request: {str(e)}", exc_info=True)
    
    def process_response(self, request, response):
        """Log response information."""
        try:
            # Log response status
            logger.info(
                f"Response: {response.status_code}",
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'ip': self.get_client_ip(request),
                    'path': request.path
                }
            )
        except Exception as e:
            logger.error(f"Error logging response: {str(e)}", exc_info=True)
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ErrorLoggingMiddleware(MiddlewareMixin):
    """Middleware to log errors."""
    
    def process_exception(self, request, exception):
        """Log exception information."""
        try:
            from ..models import AppErrorLog
            
            # Log to database
            AppErrorLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                error_type=type(exception).__name__,
                error_message=str(exception),
                stack_trace=self.get_stack_trace(exception),
                request_path=request.path,
                request_method=request.method,
                request_data=self.get_request_data(request)
            )
            
            # Log to file
            logger.error(
                f"Error: {type(exception).__name__}: {str(exception)}",
                exc_info=True,
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'path': request.path,
                    'method': request.method
                }
            )
            
        except Exception as e:
            logger.error(f"Error logging exception: {str(e)}", exc_info=True)
    
    def get_stack_trace(self, exception):
        """Get formatted stack trace."""
        import traceback
        return ''.join(traceback.format_tb(exception.__traceback__))
    
    def get_request_data(self, request):
        """Get request data for logging."""
        data = {
            'GET': dict(request.GET.items()),
            'POST': dict(request.POST.items()),
            'FILES': list(request.FILES.keys()),
            'COOKIES': dict(request.COOKIES.items()),
            'META': {
                k: v for k, v in request.META.items()
                if k.startswith('HTTP_') or k in ('REMOTE_ADDR', 'REQUEST_METHOD')
            }
        }
        
        # Remove sensitive data
        if 'password' in data['POST']:
            data['POST']['password'] = '********'
        if 'HTTP_AUTHORIZATION' in data['META']:
            data['META']['HTTP_AUTHORIZATION'] = '********'
        
        return data

# # Create a file in your app directory, e.g., my_finance/middleware.py

# from django.utils.functional import SimpleLazyObject
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

# def get_user_from_jwt(request):
#     """
#     Get user from JWT token in cookie.
#     """
#     # Get the token from the cookie
#     access_token = request.COOKIES.get('access_token')
    
#     if not access_token:
#         return None
    
#     # Create a JWT authentication instance
#     jwt_auth = JWTAuthentication()
    
#     try:
#         # Validate the token
#         validated_token = jwt_auth.get_validated_token(access_token)
#         # Get the user from the token
#         user = jwt_auth.get_user(validated_token)
#         return user
#     except (InvalidToken, TokenError):
#         return None

# class JWTCookieMiddleware:
#     """
#     Middleware to authenticate users via JWT tokens in cookies for both
#     Django views and DRF views.
#     """
#     def __init__(self, get_response):
#         self.get_response = get_response
        
#     def __call__(self, request):
#         # Process the request before the view is called
        
#         # If user is not authenticated via session, try JWT
#         if not hasattr(request, 'user') or not request.user.is_authenticated:
#             request.user = SimpleLazyObject(lambda: get_user_from_jwt(request) or request.user)
        
#         # Call the next middleware or view
#         response = self.get_response(request)
        
#         return response