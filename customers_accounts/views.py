from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings

from accounts.models import User, UserSession
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from customers_accounts.models import CustomerProfile

from .serializers import (
    CustomerRegisterSerializer,
    CustomerLoginSerializer,
    CustomerProfileSerializer,
)

from accounts.utils import generate_verification_code, generate_reset_code


# =========================
# Helper: Get Client IP
# =========================
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# ===== Register =====
class CustomerRegisterView(APIView):
    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        user.is_active = False
        user.save()

        CustomerProfile.objects.get_or_create(
            user=user,
            defaults={'is_customer': True}
        )

        code = generate_verification_code()
        user.verification_code = code
        user.save()

        send_mail(
            "كود تفعيل حسابك",
            f"كود التفعيل: {code}",
            settings.EMAIL_HOST_USER,
            [user.email],
        )

        return Response({"status": "success"}, status=status.HTTP_201_CREATED)


# ===== Verify =====
class CustomerVerifyView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("verification_code")

        try:
            user = User.objects.get(
                email=email,
                verification_code=code,
            )
        except User.DoesNotExist:
            return Response(
                {"message": "كود التحقق غير صحيح"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.verification_code = None
        user.save()

        return Response({"status": "success"})


# ===== Login (🔥 تم التعديل) =====
class CustomerLoginView(APIView):
    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data

        if not user.is_active:
            return Response(
                {"message": "الحساب غير مفعل"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🔥 Generate JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # 🌍 IP
        ip = get_client_ip(request)

        # 📱 Device info
        device_name = request.data.get("device_name", "Unknown")
        platform = request.data.get("platform", "Unknown")

        # 🔐 تحديث بيانات المستخدم
        user.last_login_ip = ip
        user.last_login_device = device_name
        user.save()

        # 🔥 إنشاء Session
        UserSession.objects.create(
            user=user,
            refresh_token=refresh_token,
            device_name=device_name,
            platform=platform,
            ip_address=ip,
            country="Egypt",  # مؤقت
            city="Cairo"
        )

        return Response({
            "status": "success",
            "access": access_token,
            "refresh": refresh_token,
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
            }
        })


# ===================== Request Password Reset =====================
class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"status": "failure", "message": "البريد الإلكتروني مطلوب"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"status": "failure", "message": "البريد الإلكتروني غير مسجل"},
                status=status.HTTP_404_NOT_FOUND
            )

        code = generate_reset_code()
        user.reset_code = code
        user.save()

        send_mail(
            "إعادة تعيين كلمة المرور",
            f"كود إعادة التعيين الخاص بك هو: {code}",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return Response(
            {"status": "success", "message": "تم إرسال الكود"},
            status=status.HTTP_200_OK
        )


# ===================== Verify Reset Code =====================
class VerifyResetCodeView(APIView):
    def post(self, request):
        email = request.data.get("email")
        reset_code = request.data.get("reset_code")

        try:
            user = User.objects.get(email=email, reset_code=reset_code)
        except User.DoesNotExist:
            return Response(
                {"status": "failure", "message": "كود غير صحيح"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"status": "success"})


# ===================== Reset Password =====================
class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        reset_code = request.data.get("reset_code")
        new_password = request.data.get("new_password")

        if not email or not new_password or not reset_code:
            return Response(
                {"status": "failure", "message": "بيانات ناقصة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email, reset_code=reset_code)
        except User.DoesNotExist:
            return Response(
                {"status": "failure", "message": "بيانات غير صحيحة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.reset_code = None
        user.save()

        return Response({"status": "success"})


# ===== Profile =====
class CustomerProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomerProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = CustomerProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "updated"})


# ===== Logout (🔥 جديد) =====
class CustomerLogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"message": "Refresh token مطلوب"},
                status=status.HTTP_400_BAD_REQUEST
            )

        UserSession.objects.filter(
            refresh_token=refresh_token
        ).update(is_active=False)

        return Response({"status": "logged out"})