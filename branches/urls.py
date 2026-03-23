from django.urls import path
from .views import NearbyBranches

urlpatterns = [
    path('nearby/', NearbyBranches.as_view()),
]
