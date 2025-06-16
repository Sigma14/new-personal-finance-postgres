"""
Authentication views for the personal finance application.
"""
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
import logging
import hashlib
import time

from ..models import AppErrorLog
from .base import BaseViewMixin, MessageMixin

logger = logging.getLogger(__name__)

class CustomLoginView(LoginView):
    """Custom login view with rate limiting and security measures."""
    template_name = 'login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('dashboard')
    
    def form_valid(self, form):
        """Handle successful login."""
        response = super().form_valid(form)
        self.add_success_message('Successfully logged in.')
        return response
    
    def form_invalid(self, form):
        """Handle failed login attempts."""
        self.add_error_message('Invalid username or password.')
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    """Custom logout view with security measures."""
    next_page = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        """Handle logout with security measures."""
        try:
            response = super().dispatch(request, *args, **kwargs)
            self.add_success_message('Successfully logged out.')
            return response
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}", exc_info=True)
            return redirect('login')

class ChangePasswordView(BaseViewMixin, LoginRequiredMixin, MessageMixin):
    """View for changing user password."""
    template_name = 'change_password.html'
    
    def post(self, request, *args, **kwargs):
        """Handle password change."""
        try:
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not request.user.check_password(old_password):
                self.add_error_message('Current password is incorrect.')
                return redirect('change_password')
            
            if new_password != confirm_password:
                self.add_error_message('New passwords do not match.')
                return redirect('change_password')
            
            # Validate password strength
            if len(new_password) < 8:
                self.add_error_message('Password must be at least 8 characters long.')
                return redirect('change_password')
            
            if not any(c.isupper() for c in new_password):
                self.add_error_message('Password must contain at least one uppercase letter.')
                return redirect('change_password')
            
            if not any(c.islower() for c in new_password):
                self.add_error_message('Password must contain at least one lowercase letter.')
                return redirect('change_password')
            
            if not any(c.isdigit() for c in new_password):
                self.add_error_message('Password must contain at least one number.')
                return redirect('change_password')
            
            request.user.set_password(new_password)
            request.user.save()
            
            self.add_success_message('Password changed successfully.')
            return redirect('login')
            
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while changing password.')
            return redirect('change_password')

class PasswordResetView(BaseViewMixin, LoginRequiredMixin, MessageMixin):
    """View for resetting user password."""
    template_name = 'password_reset.html'
    
    def post(self, request, *args, **kwargs):
        """Handle password reset request."""
        try:
            email = request.POST.get('email')
            user = User.objects.filter(email=email).first()
            
            if not user:
                self.add_error_message('No user found with this email address.')
                return redirect('password_reset')
            
            # Generate and send reset token
            token = self.generate_reset_token(user)
            self.send_reset_email(user, token)
            
            self.add_success_message('Password reset instructions sent to your email.')
            return redirect('login')
            
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while processing your request.')
            return redirect('password_reset')
    
    def generate_reset_token(self, user):
        """Generate a secure reset token."""
        # Create a unique token using user data and timestamp
        timestamp = str(int(time.time()))
        random_string = get_random_string(32)
        token_data = f"{user.id}:{user.email}:{timestamp}:{random_string}"
        
        # Hash the token data
        token = hashlib.sha256(token_data.encode()).hexdigest()
        
        # Store token in cache with 1-hour expiration
        cache_key = f"password_reset_token_{user.id}"
        cache.set(cache_key, token, 3600)  # 1 hour expiration
        
        return token
    
    def send_reset_email(self, user, token):
        """Send password reset email."""
        reset_url = f"{settings.SITE_URL}/reset-password/{token}"
        
        # Render email template
        context = {
            'user': user,
            'reset_url': reset_url,
            'expiry_hours': 1
        }
        
        html_message = render_to_string('emails/password_reset.html', context)
        plain_message = render_to_string('emails/password_reset.txt', context)
        
        # Send email
        send_mail(
            subject='Password Reset Request',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )

class PasswordResetConfirmView(BaseViewMixin, LoginRequiredMixin, MessageMixin):
    """View for confirming password reset."""
    template_name = 'password_reset_confirm.html'
    
    def post(self, request, *args, **kwargs):
        """Handle password reset confirmation."""
        try:
            token = kwargs.get('token')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validate token
            user_id = self.validate_token(token)
            if not user_id:
                self.add_error_message('Invalid or expired reset token.')
                return redirect('password_reset')
            
            # Validate passwords
            if new_password != confirm_password:
                self.add_error_message('Passwords do not match.')
                return redirect('password_reset_confirm', token=token)
            
            # Validate password strength
            if len(new_password) < 8:
                self.add_error_message('Password must be at least 8 characters long.')
                return redirect('password_reset_confirm', token=token)
            
            if not any(c.isupper() for c in new_password):
                self.add_error_message('Password must contain at least one uppercase letter.')
                return redirect('password_reset_confirm', token=token)
            
            if not any(c.islower() for c in new_password):
                self.add_error_message('Password must contain at least one lowercase letter.')
                return redirect('password_reset_confirm', token=token)
            
            if not any(c.isdigit() for c in new_password):
                self.add_error_message('Password must contain at least one number.')
                return redirect('password_reset_confirm', token=token)
            
            # Update password
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            
            # Clear reset token
            cache.delete(f"password_reset_token_{user_id}")
            
            self.add_success_message('Password has been reset successfully.')
            return redirect('login')
            
        except Exception as e:
            logger.error(f"Error confirming password reset: {str(e)}", exc_info=True)
            self.add_error_message('An error occurred while resetting your password.')
            return redirect('password_reset')
    
    def validate_token(self, token):
        """Validate the reset token."""
        # Check all possible user tokens in cache
        for key in cache.keys("password_reset_token_*"):
            stored_token = cache.get(key)
            if stored_token == token:
                # Extract user ID from cache key
                user_id = key.split('_')[-1]
                return user_id
        return None 