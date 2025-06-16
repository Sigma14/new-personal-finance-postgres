from django.contrib import admin
from django.urls import path
from ai_feature import views

urlpatterns = [
    path('', ai_feature.views.index, name='index'),
    path('login/', ai_feature.views.user_login, name='login'),
    path('signup/', ai_feature.views.signup, name='signup'),
    path('register/', ai_feature.views.register_user, name='register'),
    path('logout/', ai_feature.views.user_logout, name='logout'),
    path('user/', ai_feature.views.user_page, name='user_page'),
    path('admin/', ai_feature.views.admin_page, name='admin_page'),
    path('use-feature/<str:feature_name>/', ai_feature.views.use_feature, name='use_feature'),
    path('admin/update-feature-limit/', ai_feature.views.update_feature_limit, name='update_feature_limit'),
    path('choose-subscription/<int:plan_id>/', ai_feature.views.choose_subscription, name='choose_subscription'),
]