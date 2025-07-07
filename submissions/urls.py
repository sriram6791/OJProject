# submissions/urls.py

from django.urls import path
from . import views
from .views import (
    # Your existing views like SubmissionCreateView, SubmissionDetailView, SubmissionStatusAPIView
    ContestSubmissionCreateAPIView, # NEW
    ContestSubmissionStatusAPIView, # NEW
)

app_name = 'submissions'

urlpatterns = [
    path('submit/<int:problem_id>/', views.submit_code_view, name='submit_code'),
    path('api/status/<int:submission_id>/', views.get_submission_status_api, name='api_status'), # New API endpoint
     path('<int:submission_id>/', views.submission_detail_view, name='detail'), # New URL for submission detail
     path('contest_submit/<int:contest_pk>/<int:problem_pk>/', ContestSubmissionCreateAPIView.as_view(), name='submit_contest_code'),
    path('api/contest_status/<int:pk>/', ContestSubmissionStatusAPIView.as_view(), name='api_contest_submission_status'),
]