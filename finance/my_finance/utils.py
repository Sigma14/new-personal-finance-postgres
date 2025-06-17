from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import AIUserFeatureUsage, AIUserSubscription


def compute_current_period(registration_date, now=None):
    if now is None:
        now = timezone.now()

    period_start = registration_date
    while period_start + relativedelta(months=1) <= now:
        period_start += relativedelta(months=1)

    period_end = period_start + relativedelta(months=1)
    return period_start, period_end


def get_or_create_usage_record(user, feature_name):
    try:
        user_subscription = AIUserSubscription.objects.get(user=user)
        if not user_subscription.is_active:
            return None, "Subscription expired. Please renew your subscription."

        period_start, period_end = compute_current_period(
            user_subscription.registration_date, timezone.now()
        )

        usage, created = AIUserFeatureUsage.objects.get_or_create(
            user_subscription=user_subscription,
            feature_name=feature_name,
            period_start=period_start,
            period_end=period_end,
            defaults={"usage_count": 0},
        )
        return usage, None
    except AIUserSubscription.DoesNotExist:
        return None, "No active subscription found. Please subscribe to a plan."


def process_ai_feature(user, feature_name):
    usage, error = get_or_create_usage_record(user, feature_name)
    if error:
        return {"error": error}

    user_subscription = AIUserSubscription.objects.get(user=user)
    if not user_subscription.is_active:
        return {"error": "Subscription expired. Please renew your subscription."}

    plan_name = user_subscription.plan.plan_name
    allowed_limit = settings.SUBSCRIPTION_PLANS.get(
        plan_name, {}).get(feature_name, 0)

    if usage.usage_count >= allowed_limit:
        return {"error": "Monthly usage limit reached for this feature."}

    with transaction.atomic():
        updated = AIUserFeatureUsage.objects.filter(
            id=usage.id, usage_count__lt=allowed_limit
        ).update(usage_count=F("usage_count") + 1)

        if not updated:
            return {"error": "Could not update usage count. Please try again."}

    return {
        "message": "AI feature executed successfully.",
        "remaining": allowed_limit - (usage.usage_count + 1),
    }


def check_subscription_status(user):
    try:
        subscription = AIUserSubscription.objects.get(user=user)
        if subscription.expiration_date < timezone.now():
            subscription.is_active = False
            subscription.save()
        return subscription
    except AIUserSubscription.DoesNotExist:
        return None
