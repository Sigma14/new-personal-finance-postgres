from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .utils import process_ai_feature, check_subscription_status
from .models import AIUserSubscription, AIUserFeatureUsage, AISubscriptionPlan, AIFeatureLimits
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

def ai_user_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('ai-admin_page')
        return redirect('ai-user_page')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('ai-admin_page')
            return redirect('ai-user_page')
        else:
            messages.error(request, "Invalid username or password")
            return redirect('ai-index')
    
    return redirect('ai-index')

def ai_index(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('ai-admin_page')
        return redirect('ai-user_page')
    return render(request, 'ai_index.html')

def ai_user_logout(request):
    logout(request)
    return redirect('ai-index')

@login_required
def ai_user_page(request):
    if request.user.is_superuser:
        return redirect('ai-admin_page')
    
    try:
        subscription = check_subscription_status(request.user)
        
        if not subscription:
            try:
                basic_plan = AISubscriptionPlan.objects.get(plan_name='basic')
                subscription = AIUserSubscription.objects.create(
                    user=request.user,
                    plan=basic_plan,
                    registration_date=timezone.now(),
                    expiration_date=timezone.now() + timedelta(days=basic_plan.duration_days),
                    is_active=True
                )
                messages.info(request, "You've been automatically subscribed to our Basic plan")
            except AISubscriptionPlan.DoesNotExist:
                messages.error(request, "No subscription plans available. Please contact admin.")
                return redirect('ai-index')
        
        usage_records = AIUserFeatureUsage.objects.filter(user_subscription=subscription)
        feature_limits = AIFeatureLimits.objects.filter(plan=subscription.plan)
        limits = {fl.feature_name: fl.usage_limit for fl in feature_limits}
        
        days_remaining = max((subscription.expiration_date - timezone.now()).days, 0) if subscription.is_active else 0
        
        features = []
        for feature, limit in limits.items():
            try:
                usage = usage_records.get(feature_name=feature)
                remaining = max(limit - usage.usage_count, 0)
            except AIUserFeatureUsage.DoesNotExist:
                remaining = limit
            
            features.append({
                'name': feature,
                'limit': limit,
                'remaining': remaining,
                'percentage': (remaining / limit) * 100 if limit > 0 else 0
            })
        
        available_plans = AISubscriptionPlan.objects.exclude(id=subscription.plan.id) if subscription.plan else AISubscriptionPlan.objects.all()
        
        return render(request, 'ai_user.html', {
            'user': request.user,
            'subscription': subscription,
            'features': features,
            'plans': available_plans,
            'days_remaining': days_remaining,
            'is_subscription_active': subscription.is_active,
        })
        
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('index')

@login_required
def ai_choose_subscription(request, plan_id):
    if request.method == 'POST':
        try:
            plan = AISubscriptionPlan.objects.get(id=plan_id)
            subscription, created = AIUserSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'registration_date': timezone.now(),
                    'expiration_date': timezone.now() + timedelta(days=plan.duration_days),
                    'is_active': True
                }
            )
            messages.success(request, f"You've successfully subscribed to {plan.plan_name} plan")
        except AISubscriptionPlan.DoesNotExist:
            messages.error(request, "Invalid subscription plan selected")
    
    return redirect('ai-user_page')

@user_passes_test(lambda u: u.is_superuser)
def ai_admin_page(request):
    plans = AISubscriptionPlan.objects.all()
    plan_stats = []
    for plan in plans:
        count = AIUserSubscription.objects.filter(plan=plan).count()
        active_count = AIUserSubscription.objects.filter(plan=plan, is_active=True).count()
        plan_stats.append({
            'name': plan.plan_name,
            'count': count,
            'active_count': active_count,
            'price': plan.price,
            'duration': plan.duration_days
        })
    
    feature_limits = AIFeatureLimits.objects.select_related('plan').all()
    
    return render(request, 'ai_admin.html', {
        'plan_stats': plan_stats,
        'feature_limits': feature_limits,
        'all_plans': plans
    })

@user_passes_test(lambda u: u.is_superuser)
def ai_update_feature_limit(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        feature_name = request.POST.get('feature_name')
        new_limit = request.POST.get('new_limit')
        
        try:
            plan = AISubscriptionPlan.objects.get(id=plan_id)
            limit, created = AIFeatureLimits.objects.get_or_create(
                plan=plan,
                feature_name=feature_name,
                defaults={'usage_limit': new_limit}
            )
            if not created:
                limit.usage_limit = new_limit
                limit.save()
            messages.success(request, "Feature limit updated successfully")
        except Exception as e:
            messages.error(request, f"Error updating feature limit: {str(e)}")
    
    return redirect('ai-admin_page')

@login_required
def ai_use_feature(request, feature_name):
    subscription = check_subscription_status(request.user)
    if not subscription or not subscription.is_active:
        return JsonResponse({"error": "Your subscription is not active. Please renew your subscription."}, status=403)
    
    try:
        response = process_ai_feature(request.user, feature_name)
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def ai_signup(request):
    if request.user.is_authenticated:
        return redirect('ai-user_page')
    
    plans = AISubscriptionPlan.objects.all()
    return render(request, 'ai_signup.html', {'plans': plans})

def ai_register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email', '')
        plan_id = request.POST.get('plan_id')
        
        if not username or not password:
            messages.error(request, 'Username and password are required')
            return redirect('ai-signup')
        
        try:
            user = User.objects.create_user(username, email, password)
            
            try:
                plan = AISubscriptionPlan.objects.get(id=plan_id)
            except AISubscriptionPlan.DoesNotExist:
                messages.error(request, 'Invalid subscription plan selected')
                return redirect('ai-signup')
            
            AIUserSubscription.objects.create(
                user=user,
                plan=plan,
                registration_date=timezone.now(),
                expiration_date=timezone.now() + timedelta(days=plan.duration_days),
                is_active=True
            )
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('ai-user_page')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('ai-signup')
    
    return redirect('ai-signup')