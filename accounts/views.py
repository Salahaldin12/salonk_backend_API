from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail

from accounts.models import User
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .utils import generate_verification_code
from .utils import generate_reset_code
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .utils import generate_verification_code

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            code = generate_verification_code()
            user.verification_code = code
            user.save()

            send_mail(
                'كود التحقق من حسابك',
                f'كود التحقق الخاص بك هو: {code}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    def post(self, request):
        email = request.data.get("email")
        verification_code = request.data.get("verification_code")

        print("📩 Email from Flutter:", email)
        print("📩 Code from Flutter:", verification_code)

        try:
            user = User.objects.get(email=email, verification_code=verification_code)
        except Exception as e:
            print("❌ Error:", e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        #user.verification_code = None
        user.save()

        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)



class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'status': 'success',
                'token': token.key,
                'data': {
                    'id': user.id,
                    'username': user.name,
                    'email': user.email,
                    'phone': user.phone
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "البريد غير مسجل"}, status=status.HTTP_404_NOT_FOUND)

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

        return Response({"message": "تم إرسال الكود إلى بريدك الإلكتروني"}, status=status.HTTP_200_OK)


class RestCodeView(APIView):
    def post(self, request):
        email = request.data.get("email")
        reset_code = request.data.get("verification_code")

        print("📩 Email from Flutter:", email)
        print("📩 Code from Flutter:", reset_code)

        try:
            user = User.objects.get(email=email, reset_code=reset_code)
        except Exception as e:
            print("❌ Error:", e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        #user.verification_code = None
        user.save()

        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)



# 2️⃣ إعادة تعيين كلمة المرور
class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get("email")
        new_password = request.data.get("new_password")

        if not email or not new_password:
            return Response({"error": "يجب إدخال البريد وكلمة المرور الجديدة"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "البريد غير صحيح"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"status": "success"}, status=status.HTTP_200_OK)