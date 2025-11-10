from django.urls import path
from .views import RegisterView, LoginView, RequestPasswordResetView, ResetPasswordView, RestCodeView , VerifyCodeView
urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('verify-code/', VerifyCodeView.as_view()),  # التحقق من كود الـ 6 أرقام
    #path('resend-code/', ResendCodeView.as_view()),
    path("password-reset/request/", RequestPasswordResetView.as_view()),
    path('reset_code/', RestCodeView.as_view()),
    path("password-reset/confirm/", ResetPasswordView.as_view()),
]