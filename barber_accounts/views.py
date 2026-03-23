from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .serializers import BarberLoginSerializer, EditProfileSerializer
from accounts.utils import generate_reset_code

from django.core.mail import send_mail
from django.conf import settings

from .models import WorkingTime



# ===== Login =====
class BarberLoginView(APIView):

    def post(self, request):

        serializer = BarberLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "status": "success",
            "token": token.key,
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            }
        })


# ===== Check Mail =====
class ChakmailView(APIView):

    def post(self, request):

        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "البريد غير مسجل"},
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
            {"message": "تم إرسال الكود إلى بريدك الإلكتروني"},
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



# ===== Change Password =====
class BarberChangePasswordView(APIView):

    def post(self, request):

        email = request.data.get("email")
        new_password = request.data.get("new_password")

        # تحقق من البيانات
        if not email or not new_password:
            return Response(
                {"message": "الرجاء إدخال البريد الإلكتروني وكلمة المرور الجديدة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            if not user.barber:
                return Response(
                    {"error": "غير مصرح"},
                    status=status.HTTP_403_FORBIDDEN
                )

            user.set_password(new_password)
            user.save()

            return Response({
                "status": "success",
                "message": "تم تغيير كلمة المرور بنجاح"
            })

        except User.DoesNotExist:
            return Response(
                {"message": "المستخدم غير موجود"},
                status=status.HTTP_404_NOT_FOUND
            )


# ===== Profile =====
class ProfileView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # ===== Get Profile =====
    def get(self, request):

        user = request.user

        serializer = EditProfileSerializer(user)

        response_data = {
            "status": "success",
            "data": serializer.data
        }

        # لو المستخدم حلاق
        if hasattr(user, "barber"):

            working_times = WorkingTime.objects.filter(
                barber=user.barber
            )

            working_serializer = [
                {
                    "branch_id": wt.branch.id,
                    "date": wt.date,
                    "start_time": wt.start_time,
                    "end_time": wt.end_time,
                    "clients_per_hour": wt.clients_per_hour
                }
                for wt in working_times
            ]

            response_data["data"]["working_times"] = working_serializer

        return Response(response_data)

    # ===== Update Profile =====
    def put(self, request):

        user = request.user

        serializer = EditProfileSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": "success",
                "message": "Profile updated successfully"
            })

        return Response({
            "status": "error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)