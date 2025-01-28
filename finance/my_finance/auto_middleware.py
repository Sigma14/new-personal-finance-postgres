import threading

from my_finance.helper import request_budget, request_bill
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from my_finance.models import AppErrorLog

def create_bill_request():
    """
    Create bill request log
    """
    # Get a list of all alive threads
    alive_threads = threading.enumerate()
    bills_thread1 = False
    for thread in alive_threads:
        if thread.name == 'bills_thread1':
            bills_thread1 = True

    if not bills_thread1:
        t1 = threading.Thread(target=request_bill, name='bills_thread1')
        t1.start()


def create_budget_request():
    """
    Create budget request log
    """
    # Get a list of all alive threads
    alive_threads = threading.enumerate()
    budget_thread1 = False
    for thread in alive_threads:
        if thread.name == 'budget_thread1':
            budget_thread1 = True

    if not budget_thread1:
        t1 = threading.Thread(target=request_budget, name='budget_thread1')
        t1.start()


class AutoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # call deduct_credit() function
        create_budget_request()
        create_bill_request()
        response = self.get_response(request)
        return response


class AppErrorLogMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        print("Middleware triggered")

        # Extract exception details
        exception_type = type(exception).__name__
        error_message = str(exception)
        tb = traceback.format_exc()
        request_path = request.path
        user = request.user if request.user.is_authenticated else None

        # Determine status code (default to 500 for server errors)
        code = 500  # Default to internal server error
        if hasattr(exception, 'status_code'):
            code = exception.status_code

        # Check for an existing similar error
        existing_error = AppErrorLog.objects.filter(
            exception_type=exception_type,
            error_message=error_message,
            traceback=tb,
            request_path=request_path,
            code=code,
        ).first()

        if existing_error:
            # Increment the count if the error already exists
            existing_error.count += 1
            existing_error.save()
            # Add the user to the ManyToManyField if authenticated
            if user and not existing_error.users.filter(id=user.id).exists():
                existing_error.users.add(user)
        else:
            # Create a new error log
            new_error = AppErrorLog.objects.create(
                            exception_type=exception_type,
                            error_message=error_message,
                            traceback=tb,
                            request_path=request_path,
                            code=code,
                        )
            # Add the user to the ManyToManyField if authenticated
            if user:
                new_error.users.add(user)
        
        return None
