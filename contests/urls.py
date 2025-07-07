from django.urls import path
from .views import (
    ContestListView,
    ContestDetailView,
    ContestRegisterView,
    ContestLeaderboardView,
    ContestProblemSolveView, # NEW
)

app_name = 'contests'

urlpatterns = [
    path('list/', ContestListView.as_view(), name='list'),
    path('<int:pk>/', ContestDetailView.as_view(), name='detail'),

    path('<int:pk>/register/', ContestRegisterView.as_view(), name='register_for_contest'),
    path('<int:pk>/leaderboard/', ContestLeaderboardView.as_view(), name='contest_leaderboard'),
    path('<int:contest_pk>/solve/', ContestProblemSolveView.as_view(), name='solve_contest_problem_default'),
    path('<int:contest_pk>/solve/<int:problem_pk>/', ContestProblemSolveView.as_view(), name='solve_contest_problem'),
]