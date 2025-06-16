"""
Security middleware for the application.
This module provides:
- Rate limiting
- Security headers
- Request logging
- Audit logging
- IP blocking
- Session security
"""
from django.core.cache import cache
from django.http import HttpResponseTooManyRequests
from django.conf import settings
import logging
import json
from datetime import datetime, timedelta
import time
import re

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Base security middleware class."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)

class RateLimitMiddleware(SecurityMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.rate_limits = {
            'default': (100, 60),  # 100 requests per minute
            'api': (1000, 60),     # 1000 requests per minute
            'auth': (5, 60),       # 5 requests per minute
        }
    
    def __call__(self, request):
        # Skip rate limiting for certain paths
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Determine rate limit based on path
        if request.path.startswith('/api/'):
            limit, period = self.rate_limits['api']
        elif request.path.startswith('/auth/'):
            limit, period = self.rate_limits['auth']
        else:
            limit, period = self.rate_limits['default']
        
        # Check rate limit
        if not self.check_rate_limit(client_ip, limit, period):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return HttpResponseTooManyRequests('Rate limit exceeded')
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    def check_rate_limit(self, client_ip, limit, period):
        """Check if client has exceeded rate limit."""
        cache_key = f'rate_limit:{client_ip}'
        requests = cache.get(cache_key, [])
        
        # Remove old requests
        now = time.time()
        requests = [req for req in requests if now - req < period]
        
        if len(requests) >= limit:
            return False
        
        requests.append(now)
        cache.set(cache_key, requests, period)
        return True

class SecurityHeadersMiddleware(SecurityMiddleware):
    """Security headers middleware."""
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response

class RequestLoggingMiddleware(SecurityMiddleware):
    """Request logging middleware."""
    
    def __call__(self, request):
        # Log request
        self.log_request(request)
        
        response = self.get_response(request)
        
        # Log response
        self.log_response(request, response)
        
        return response
    
    def log_request(self, request):
        """Log request details."""
        if not self.should_log_request(request):
            return
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', '')
        }
        
        logger.info(f"Request: {log_data}")
    
    def log_response(self, request, response):
        """Log response details."""
        if not self.should_log_request(request):
            return
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'status_code': response.status_code,
            'path': request.path,
            'user': request.user.username if request.user.is_authenticated else 'anonymous'
        }
        
        logger.info(f"Response: {log_data}")
    
    def should_log_request(self, request):
        """Determine if request should be logged."""
        # Skip logging for static/media files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return False
        
        # Skip logging for health check endpoints
        if request.path == '/health/':
            return False
        
        return True
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class AuditLogMiddleware(SecurityMiddleware):
    """Audit logging middleware."""
    
    def __call__(self, request):
        # Log sensitive operations
        if self.is_sensitive_operation(request):
            self.log_audit(request)
        
        return self.get_response(request)
    
    def is_sensitive_operation(self, request):
        """Check if request is a sensitive operation."""
        sensitive_paths = [
            '/api/',
            '/auth/',
            '/property/create/',
            '/property/update/',
            '/property/delete/',
            '/maintenance/create/',
            '/maintenance/update/',
            '/maintenance/delete/',
            '/expense/create/',
            '/expense/update/',
            '/expense/delete/',
            '/invoice/create/',
            '/invoice/update/',
            '/invoice/delete/'
        ]
        
        return any(request.path.startswith(path) for path in sensitive_paths)
    
    def log_audit(self, request):
        """Log audit information."""
        audit_data = {
            'timestamp': datetime.now().isoformat(),
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'ip': self.get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'data': self.get_request_data(request)
        }
        
        logger.info(f"Audit: {audit_data}")
    
    def get_request_data(self, request):
        """Get request data for logging."""
        if request.method in ['POST', 'PUT', 'PATCH']:
            return request.POST.dict()
        return {}
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class IPBlockingMiddleware(SecurityMiddleware):
    """IP blocking middleware."""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.blocked_ips = set()
        self.suspicious_ips = {}
    
    def __call__(self, request):
        client_ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return HttpResponseTooManyRequests('IP blocked')
        
        # Check for suspicious activity
        if self.is_suspicious_activity(request):
            self.handle_suspicious_activity(client_ip)
        
        return self.get_response(request)
    
    def is_suspicious_activity(self, request):
        """Check for suspicious activity patterns."""
        # Check for SQL injection attempts
        sql_patterns = [
            r'(\%27)|(\')|(\-\-)|(\%23)|(#)',
            r'((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))',
            r'/\*.*\*/',
            r'exec\s+xp_cmdshell',
            r'select.*from',
            r'insert.*into',
            r'delete.*from',
            r'drop.*table',
            r'truncate.*table'
        ]
        
        # Check request path and data
        request_data = str(request.GET) + str(request.POST)
        return any(re.search(pattern, request_data, re.IGNORECASE) for pattern in sql_patterns)
    
    def handle_suspicious_activity(self, client_ip):
        """Handle suspicious activity."""
        if client_ip not in self.suspicious_ips:
            self.suspicious_ips[client_ip] = 1
        else:
            self.suspicious_ips[client_ip] += 1
        
        # Block IP after 5 suspicious activities
        if self.suspicious_ips[client_ip] >= 5:
            self.blocked_ips.add(client_ip)
            logger.warning(f"IP blocked due to suspicious activity: {client_ip}")
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class SessionSecurityMiddleware(SecurityMiddleware):
    """Session security middleware."""
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Check session age
            if 'last_activity' in request.session:
                last_activity = datetime.fromisoformat(request.session['last_activity'])
                if datetime.now() - last_activity > timedelta(hours=1):
                    # Session expired
                    request.session.flush()
                    return self.get_response(request)
            
            # Update last activity
            request.session['last_activity'] = datetime.now().isoformat()
            
            # Check for concurrent sessions
            if self.has_concurrent_sessions(request):
                request.session.flush()
                return self.get_response(request)
        
        return self.get_response(request)
    
    def has_concurrent_sessions(self, request):
        """Check for concurrent sessions."""
        session_key = request.session.session_key
        if not session_key:
            return False
        
        # Get all sessions for the user
        user_sessions = cache.get(f'user_sessions:{request.user.id}', set())
        
        # Add current session
        user_sessions.add(session_key)
        cache.set(f'user_sessions:{request.user.id}', user_sessions)
        
        # Check if user has too many active sessions
        return len(user_sessions) > 3  # Allow maximum 3 concurrent sessions 