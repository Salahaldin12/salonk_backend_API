from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_booking),
    path('waiting-count/', views.get_waiting_count),
    path('cancel/', views.cancel_booking),
    path("list/", views.list_bookings),
    path("complete/<int:booking_id>/", views.complete_booking),
    path('update/<int:booking_id>/', views.update_booking_status),
]