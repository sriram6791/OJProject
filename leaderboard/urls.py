# leaderboard/urls.py

from django.urls import path
from . import views

app_name = 'leaderboard' # Namespace for this app's URLs

urlpatterns = [
    path('', views.leaderboard_view, name='main'),
]