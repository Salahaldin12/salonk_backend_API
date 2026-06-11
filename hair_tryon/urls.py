from django.urls import path
from .views import generate_haircut_view

urlpatterns = [
    # المسار الخاص بتوليد قصة الشعر بالذكاء الاصطناعي
    path('generate/', generate_haircut_view),
]