from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings

from accounts.models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    EditProfileSerializer,
)
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .utils import generate_verification_code, generate_reset_code


# ===================== Register =====================
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            code = generate_verification_code()
            user.verification_code = code
            user.is_active = False
            user.save()

            send_mail(
                "كود التحقق من حسابك",
                f"كود التحقق الخاص بك هو: {code}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            return Response(
                {"status": "success"},
                status=status.HTTP_201_CREATED
            )

        # 🔴 أخطاء التحقق
        errors = serializer.errors

        if "phone" in errors:
            return Response(
                {
                    "status": "failure",
                    "field": "phone",
                    "message": "رقم الهاتف مسجل بالفعل"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if "email" in errors:
            return Response(
                {
                    "status": "failure",
                    "field": "email",
                    "message": "البريد الإلكتروني مسجل بالفعل"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "status": "failure",
                "field": None,
                "message": "بيانات غير صحيحة"
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# ===================== Verify Code =====================
class VerifyCodeView(APIView):
    def post(self, request):
        email = request.data.get("email")
        verification_code = request.data.get("verification_code")

        try:
            user = User.objects.get(
                email=email,
                verification_code=verification_code
            )
        except User.DoesNotExist:
            return Response(
                {
                    "status": "failure",
                    "message": "كود التحقق غير صحيح"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.verification_code = None
        user.save()

        return Response(
            {"status": "success"},
            status=status.HTTP_200_OK
        )


# ===================== Login =====================
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)

            return Response(
                {
                    "status": "success",
                    "token": token.key,
                    "data": {
                        "id": user.id,
                        "username": user.name,
                        "email": user.email,
                        "phone": user.phone,
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": "failure",
                "message": "بيانات الدخول غير صحيحة"
            },
            status=status.HTTP_400_BAD_REQUEST
        )


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
            {"status": "success", "message": "تم إرسال الكود إلى بريدك الإلكتروني"},
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
                {"status": "failure", "message": "كود التحقق غير صحيح"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"status": "success"},
            status=status.HTTP_200_OK
        )

# ===================== Reset Password =====================
class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        reset_code = request.data.get("reset_code")
        new_password = request.data.get("new_password")

        if not email or not new_password or not reset_code:
            return Response(
                {"status": "failure", "message": "يجب إدخال البريد والكود وكلمة المرور الجديدة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email, reset_code=reset_code)
        except User.DoesNotExist:
            return Response(
                {"status": "failure", "message": "الكود أو البريد غير صحيح"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.reset_code = None
        user.save()

        return Response(
            {"status": "success"},
            status=status.HTTP_200_OK
        )

# ===================== Profile =====================
class ProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = EditProfileSerializer(request.user)
        return Response(
            {
                "status": "success",
                "data": serializer.data
            }
        )

    def put(self, request):
        serializer = EditProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": "تم تحديث البيانات بنجاح",
                    "data": serializer.data
                }
            )

        return Response(
            {
                "status": "failure",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
