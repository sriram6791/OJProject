# users/urls.py

from django.urls import path
from .views import (
    UserRegisterAPIView, 
    UserLoginAPIView, 
    UserLogoutAPIView, 
    UserProfileAPIView,
    register_view,
    login_view,
    logout_view,
    profile_view,
    AuthorizeProblemSettersView
)

app_name = 'users'  # Namespace for both API and template URLs

urlpatterns = [
    # Template-based views
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('authorize-problem-setters/', AuthorizeProblemSettersView.as_view(), name='authorize_problem_setters'),

    # API views
    path('api/register/', UserRegisterAPIView.as_view(), name='register_api'),
    path('api/login/', UserLoginAPIView.as_view(), name='login_api'),
    path('api/logout/', UserLogoutAPIView.as_view(), name='logout_api'),
    path('api/profile/', UserProfileAPIView.as_view(), name='profile_api'),
]