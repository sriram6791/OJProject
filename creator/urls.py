from django.urls import path
from .views import CreatorPortalView

app_name = 'creator'

urlpatterns = [
    path('', CreatorPortalView.as_view(), name='portal'),
]
