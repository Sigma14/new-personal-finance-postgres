from django.utils.functional import SimpleLazyObject
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

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