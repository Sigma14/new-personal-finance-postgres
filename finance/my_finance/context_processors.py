'''
    context_processor.py made for set configuration for Google Analytics key.
'''
from django.conf import settings

def google_analytics(request):
    return {
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS.get('google_analytics_id', None)
    }
