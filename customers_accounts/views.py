import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from accounts.models import User, UserSession
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from notifications.models import FCMDevice
from customers_accounts.models import CustomerProfile
from notifications.services import NotificationService

from .serializers import (
    CustomerRegisterSerializer,
    CustomerLoginSerializer,
    CustomerProfileSerializer,
)

from accounts.utils import generate_verification_code, generate_reset_code


def get_location_from_coords(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"

        response = requests.get(url, headers={
            "User-Agent": "salonk_app"
        })

        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})

            country = address.get("country", "")
            city = address.get("city") or address.get("state") or address.get("town") or ""

            return country, city

    except Exception:
        pass

    return None, None

import requests

def get_location_from_ip(ip):
    try:
        url = f"https://ipapi.co/{ip}/json/"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            return data.get("country_name"), data.get("city")

    except Exception as e:
        print("❌ IP Location Error:", e)

    return None, None

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

# ===== Login =====
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

        # =========================
        # JWT
        # =========================
        refresh = RefreshToken.for_user(user)

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # =========================
        # LOCATION
        # =========================
        lat = request.data.get("lat")
        lng = request.data.get("lng")

        country, city = get_location_from_coords(lat, lng)

        # =========================
        # DEVICE INFO
        # =========================
        device_name = request.data.get(
            "device_name",
            "Unknown Device"
        )

        platform = request.data.get(
            "platform",
            "Unknown"
        )

        # =========================
        # UPDATE USER
        # =========================
        user.last_login_device = device_name
        user.save()

        # =========================
        # CREATE SESSION
        # =========================
        session = UserSession.objects.create(
            user=user,
            refresh_token=refresh_token,
            device_name=device_name,
            platform=platform,
            country=country or "Unknown",
            city=city or "Unknown"
        )
        # =========================
        # SAVE FCM TOKEN
        # =========================
        fcm_token = request.data.get("fcm_token")

        if fcm_token:

            FCMDevice.objects.update_or_create(

                fcm_token=fcm_token,

                defaults={

                    "user": user,

                    "device_type": platform,

                    "is_active": True,
                }
            )

            print("✅ FCM TOKEN SAVED")
        # =========================
        # SEND LOGIN NOTIFICATION
        # =========================
        try:

            NotificationService.send_notification(

                user=user,

                title="تم تسجيل دخول جديد",

                body=(
                    f"تم تسجيل الدخول من "
                    f"{device_name} - "
                    f"{city}, {country}"
                ),

                notification_type="security",

                category="login",

                reference_id=session.id,

                screen="security_sessions",

                extra_data={
                    "device_name": device_name,
                    "platform": platform,
                    "city": city,
                    "country": country,
                }
            )

        except Exception as e:

            print("LOGIN NOTIFICATION ERROR:", e)

        # =========================
        # RESPONSE
        # =========================
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
                {
                    "status": "failure",
                    "message": "بيانات ناقصة"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            user = User.objects.get(
                email=email,
                reset_code=reset_code
            )

        except User.DoesNotExist:

            return Response(
                {
                    "status": "failure",
                    "message": "بيانات غير صحيحة"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =========================
        # CHANGE PASSWORD
        # =========================
        user.set_password(new_password)

        user.reset_code = None

        user.save()

        # =========================
        # SEND EMAIL
        # =========================
        try:

            send_mail(

                subject="تم تغيير كلمة المرور",

                message=(
                    f"مرحبًا {user.name},\n\n"
                    f"تم تغيير كلمة المرور الخاصة بحسابك بنجاح.\n\n"
                    f"إذا لم تقم أنت بهذا التغيير "
                    f"يرجى التواصل مع الدعم فورًا."
                ),

                from_email=settings.DEFAULT_FROM_EMAIL,

                recipient_list=[user.email],

                fail_silently=False
            )

            print("✅ Password change email sent")

        except Exception as e:

            print("❌ EMAIL ERROR:", e)

        # =========================
        # PUSH NOTIFICATION
        # =========================
        try:

            NotificationService.send_notification(

                user=user,

                title="تم تغيير كلمة المرور",

                body=(
                    "تم تحديث كلمة المرور الخاصة بحسابك بنجاح"
                ),

                notification_type="security",

                category="password_changed",

                screen="security"
            )

        except Exception as e:

            print("❌ NOTIFICATION ERROR:", e)

        return Response({
            "status": "success"
        })
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
    

# =================================
# =================================
class ManageSessionsView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # =========================
    # 📥 GET → عرض الجلسات
    # =========================
    def get(self, request):

        user = request.user
        current_refresh = request.headers.get("Refresh-Token")

        sessions = UserSession.objects.filter(user=user).order_by("-created_at")

        data = []

        for s in sessions:
            data.append({
                "id": s.id,
                "device_name": s.device_name,
                "platform": s.platform,
                "ip_address": s.ip_address,
                "country": s.country,
                "city": s.city,
                "is_active": s.is_active,
                "is_current": str(s.refresh_token) == str(current_refresh),
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
            })

        return Response({
            "status": "success",
            "sessions": data
        })

    # =========================
    # 🚪 POST → Logout
    # =========================
    def post(self, request):

        action = request.data.get("action")

        # =========================
        # 🔥 Logout All
        # =========================
        if action == "logout_all":

            sessions = UserSession.objects.filter(user=request.user)

            for session in sessions:
                try:
                    RefreshToken(session.refresh_token).blacklist()
                except:
                    pass

            sessions.update(is_active=False)

            return Response({
                "status": "success",
                "message": "Logged out from all devices"
            })

        # =========================
        # 📱 Logout Single
        # =========================
        elif action == "logout_one":

            session_id = request.data.get("session_id")

            session = get_object_or_404(
                UserSession,
                id=session_id,
                user=request.user
            )

            try:
                RefreshToken(session.refresh_token).blacklist()
            except:
                pass

            session.is_active = False
            session.save()

            return Response({
                "status": "success",
                "message": "Logged out from this device"
            })

        # =========================
        # ❌ Invalid Action
        # =========================
        return Response({
            "status": "error",
            "message": "Invalid action"
        }, status=400)