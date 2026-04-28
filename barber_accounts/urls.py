from django.urls import path

from barber_accounts.views import (
    BarberLoginView,
    BarberChangePasswordView,
    ChakmailView,
    ManageSessionsView,
    VerifyResetCodeView,
    ProfileView,
    
    BarberPortfolioView
)

from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [

    # =========================
    # 🔐 Auth
    # =========================
    path('login/', BarberLoginView.as_view()),
    path("sessions/", ManageSessionsView.as_view()),
    # =========================
    # 🔑 Password Reset
    # =========================
    path('check-email/', ChakmailView.as_view()),
    path('verify-code/', VerifyResetCodeView.as_view()),
    path('change-password/', BarberChangePasswordView.as_view()),

    # =========================
    # 👤 Profile
    # =========================
    path('profile/', ProfileView.as_view()),

    # =========================
    # 📸 Portfolio
    # =========================
    #path('portfolio/', BarberPortfolioUploadView.as_view()),
    path('portfolio/<int:barber_id>/', BarberPortfolioView.as_view()),


    path('token_refresh/', TokenRefreshView.as_view(),),
]