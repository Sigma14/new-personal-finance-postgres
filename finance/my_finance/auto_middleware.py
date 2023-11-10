import threading

from my_finance.helper import request_budget, request_bill


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
        print("Calling middleware")
        create_budget_request()
        create_bill_request()
        response = self.get_response(request)
        return response
