from django.urls import path

from barber_accounts.views import ProfileView
from .views import (
    BarberLoginView,
    BarberChangePasswordView,
    ChakmailView,
    VerifyResetCodeView,
    
)

urlpatterns = [
    path('login/', BarberLoginView.as_view()),
    path('change-password/', BarberChangePasswordView.as_view()),
    path('ChakmailView/', ChakmailView.as_view()),
    path('verify/', VerifyResetCodeView.as_view()),
    path('profile/', ProfileView.as_view()),
]


#ChakmailView   VerifyResetCodeView