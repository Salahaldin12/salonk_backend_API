from django.urls import path
from .views import ProfileView, RegisterView, LoginView, RequestPasswordResetView, ResetPasswordView , VerifyCodeView, VerifyResetCodeView
urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('verify-code/', VerifyCodeView.as_view()),  # التحقق من كود الـ 6 أرقام
    #path('resend-code/', ResendCodeView.as_view()),
    path("password-reset/request/", RequestPasswordResetView.as_view()),
    path('reset_code/', VerifyResetCodeView.as_view()),
    path("password-reset/confirm/", ResetPasswordView.as_view()),
    path('profile/', ProfileView.as_view()),
]