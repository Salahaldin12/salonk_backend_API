from django.urls import path
from .views import (
    CustomerRegisterView,
    CustomerVerifyView,
    CustomerLoginView,
    CustomerProfileView,
    RequestPasswordResetView,
    ResetPasswordView,
    VerifyResetCodeView,
)

urlpatterns = [
    path('register/', CustomerRegisterView.as_view()),
    path('verify-code/', CustomerVerifyView.as_view()),
    path('login/', CustomerLoginView.as_view()),
    path("password-reset/request/", RequestPasswordResetView.as_view()),
    path('reset_code/', VerifyResetCodeView.as_view()),
    path("password-reset/confirm/", ResetPasswordView.as_view()),
    path('profile/', CustomerProfileView.as_view()),

]