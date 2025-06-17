from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from my_finance.models import (
    AIFeatureLimits,
    AISubscriptionPlan,
    AIUserFeatureUsage,
    AIUserSubscription,
)
from my_finance.utils import check_subscription_status, process_ai_feature


def user_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_page")
        return redirect("user_page")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect("admin_page")
            return redirect("user_page")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("index")

    return redirect("index")


def index(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_page")
        return redirect("user_page")
    return render(request, "index.html")


def user_logout(request):
    logout(request)
    return redirect("index")


@login_required
def user_page(request):
    if request.user.is_superuser:
        return redirect("admin_page")

    try:
        subscription = check_subscription_status(request.user)

        if not subscription:
            try:
                basic_plan = SubscriptionPlan.objects.get(plan_name="basic")
                subscription = UserSubscription.objects.create(
                    user=request.user,
                    plan=basic_plan,
                    registration_date=timezone.now(),
                    expiration_date=timezone.now()
                    + timedelta(days=basic_plan.duration_days),
                    is_active=True,
                )
                messages.info(
                    request, "You've been automatically subscribed to our Basic plan"
                )
            except SubscriptionPlan.DoesNotExist:
                messages.error(
                    request, "No subscription plans available. Please contact admin."
                )
                return redirect("index")

        usage_records = UserFeatureUsage.objects.filter(
            user_subscription=subscription)
        feature_limits = FeatureLimits.objects.filter(plan=subscription.plan)
        limits = {fl.feature_name: fl.usage_limit for fl in feature_limits}

        days_remaining = (
            max((subscription.expiration_date - timezone.now()).days, 0)
            if subscription.is_active
            else 0
        )

        features = []
        for feature, limit in limits.items():
            try:
                usage = usage_records.get(feature_name=feature)
                remaining = max(limit - usage.usage_count, 0)
            except UserFeatureUsage.DoesNotExist:
                remaining = limit

            features.append(
                {
                    "name": feature,
                    "limit": limit,
                    "remaining": remaining,
                    "percentage": (remaining / limit) * 100 if limit > 0 else 0,
                }
            )

        available_plans = (
            SubscriptionPlan.objects.exclude(id=subscription.plan.id)
            if subscription.plan
            else SubscriptionPlan.objects.all()
        )

        return render(
            request,
            "user.html",
            {
                "user": request.user,
                "subscription": subscription,
                "features": features,
                "plans": available_plans,
                "days_remaining": days_remaining,
                "is_subscription_active": subscription.is_active,
            },
        )

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect("index")


@login_required
def choose_subscription(request, plan_id):
    if request.method == "POST":
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            subscription, created = UserSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    "plan": plan,
                    "registration_date": timezone.now(),
                    "expiration_date": timezone.now()
                    + timedelta(days=plan.duration_days),
                    "is_active": True,
                },
            )
            messages.success(
                request, f"You've successfully subscribed to {plan.plan_name} plan"
            )
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, "Invalid subscription plan selected")

    return redirect("user_page")


@user_passes_test(lambda u: u.is_superuser)
def admin_page(request):
    plans = SubscriptionPlan.objects.all()
    plan_stats = []
    for plan in plans:
        count = UserSubscription.objects.filter(plan=plan).count()
        active_count = UserSubscription.objects.filter(
            plan=plan, is_active=True
        ).count()
        plan_stats.append(
            {
                "name": plan.plan_name,
                "count": count,
                "active_count": active_count,
                "price": plan.price,
                "duration": plan.duration_days,
            }
        )

    feature_limits = FeatureLimits.objects.select_related("plan").all()

    return render(
        request,
        "admin.html",
        {
            "plan_stats": plan_stats,
            "feature_limits": feature_limits,
            "all_plans": plans,
        },
    )


@user_passes_test(lambda u: u.is_superuser)
def update_feature_limit(request):
    if request.method == "POST":
        plan_id = request.POST.get("plan_id")
        feature_name = request.POST.get("feature_name")
        new_limit = request.POST.get("new_limit")

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            limit, created = FeatureLimits.objects.get_or_create(
                plan=plan,
                feature_name=feature_name,
                defaults={"usage_limit": new_limit},
            )
            if not created:
                limit.usage_limit = new_limit
                limit.save()
            messages.success(request, "Feature limit updated successfully")
        except Exception as e:
            messages.error(request, f"Error updating feature limit: {str(e)}")

    return redirect("admin_page")


@login_required
def use_feature(request, feature_name):
    subscription = check_subscription_status(request.user)
    if not subscription or not subscription.is_active:
        return JsonResponse(
            {
                "error": "Your subscription is not active. Please renew your subscription."
            },
            status=403,
        )

    try:
        response = process_ai_feature(request.user, feature_name)
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def signup(request):
    if request.user.is_authenticated:
        return redirect("user_page")

    plans = SubscriptionPlan.objects.all()
    return render(request, "signup.html", {"plans": plans})


def register_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email", "")
        plan_id = request.POST.get("plan_id")

        if not username or not password:
            messages.error(request, "Username and password are required")
            return redirect("signup")

        try:
            user = User.objects.create_user(username, email, password)

            try:
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except SubscriptionPlan.DoesNotExist:
                messages.error(request, "Invalid subscription plan selected")
                return redirect("signup")

            UserSubscription.objects.create(
                user=user,
                plan=plan,
                registration_date=timezone.now(),
                expiration_date=timezone.now() + timedelta(days=plan.duration_days),
                is_active=True,
            )

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("user_page")

        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return redirect("signup")

    return redirect("signup")
