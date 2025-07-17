# problems/urls.py

from django.urls import path
from . import views

app_name = 'problems' # Namespace for this app's URLs

urlpatterns = [
    path('', views.problem_list_view, name='list'),
    path('create/', views.CreateProblemView.as_view(), name='create'),
    path('<int:problem_id>/edit/', views.EditProblemView.as_view(), name='edit'),
    path('<int:problem_id>/', views.problem_detail_view, name='detail'),
    path('api/test-custom-input/', views.test_with_custom_input, name='test_custom_input'),  # Changed to be under /api/
    path('api/ai-assistant/', views.ai_assistant_chat, name='ai_assistant_chat'),  # New AI assistant endpoint
]