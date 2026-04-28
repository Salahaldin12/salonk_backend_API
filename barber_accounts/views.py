from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User, UserSession
from accounts.utils import generate_reset_code
from .serializers import BarberLoginSerializer, EditProfileSerializer
from .models import (
    BarberProfile,
    WorkingTime,
    BarberPortfolio,
    BarberPortfolioImage
)
import requests

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

# =========================
# 🌍 Get Client IP
# =========================
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# =========================
# 🔐 Login
# =========================
class BarberLoginView(APIView):

    def post(self, request):

        serializer = BarberLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data

        if not hasattr(user, "barber"):
            return Response({"error": "هذا الحساب ليس حلاق"}, status=403)

        if not user.is_active:
            return Response({"message": "الحساب غير مفعل"}, status=403)

        refresh = RefreshToken.for_user(user)

        ip = get_client_ip(request)
        device_name = request.data.get("device_name", "Unknown")
        platform = request.data.get("platform", "Unknown")

        # تحديث بيانات المستخدم
        user.last_login_ip = ip
        user.last_login_device = device_name
        user.save()

        # 🔥 إنشاء Session
        UserSession.objects.create(
            user=user,
            refresh_token=str(refresh),
            device_name=device_name,
            platform=platform,
            ip_address=ip,
            lat=request.data.get("lat"),
            lng=request.data.get("lng")
        )

        return Response({
            "status": "success",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": "barber",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "shop_name": user.barber.shop_name,
                "is_verified": user.barber.is_verified
            }
        })


# =========================
# 📧 Check Mail
# =========================
class ChakmailView(APIView):

    def post(self, request):

        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "البريد غير مسجل"}, status=404)

        code = generate_reset_code()
        user.reset_code = code
        user.save()

        send_mail(
            "Reset Password",
            f"Your code is: {code}",
            settings.EMAIL_HOST_USER,
            [email],
        )

        return Response({"message": "تم إرسال الكود"})


# =========================
# 🔢 Verify Code
# =========================
class VerifyResetCodeView(APIView):

    def post(self, request):

        email = request.data.get("email")
        code = request.data.get("reset_code")


        if not User.objects.filter(email=email, reset_code=code).exists():
            return Response({"error": "كود غير صحيح"}, status=400)

        return Response({"status": "success"})


# =========================
# 🔑 Change Password
# =========================
class BarberChangePasswordView(APIView):

    def post(self, request):

        email = request.data.get("email")
        password = request.data.get("new_password")

        user = get_object_or_404(User, email=email)

        if not hasattr(user, "barber"):
            return Response({"error": "غير مصرح"}, status=403)

        user.set_password(password)
        user.save()

        return Response({"status": "success"})



# =========================
# 👤 Profile
# =========================
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class ProfileView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # =========================
    # 📥 GET PROFILE
    # =========================
    def get(self, request):

        user = request.user
        serializer = EditProfileSerializer(user)

        data = serializer.data

        if hasattr(user, "barber"):
            barber = user.barber

            data["barber_id"] = barber.id
            data["branch_id"] = barber.branch.id 

            data["working_times"] = [
                {
                    "id": wt.id,
                    "branch_id": wt.branch.id,
                    "date": wt.date,
                    "start_time": wt.start_time,
                    "end_time": wt.end_time,
                    "clients_per_hour": wt.clients_per_hour
                }
                for wt in barber.working_times.all()
            ]

            portfolio = getattr(barber, "portfolio", None)

            data["portfolio"] = {
                "bio": portfolio.bio if portfolio else "",
                "experience_years": portfolio.experience_years if portfolio else 0,
                "specialization": portfolio.specialization if portfolio else ""
            }

        return Response({
            "status": "success",
            "data": data
        })

    # =========================
    # ✏️ UPDATE PROFILE (NEW)
    # =========================
    def patch(self, request):

        user = request.user

        serializer = EditProfileSerializer(
            user,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        barber = getattr(user, "barber", None)

        # =========================
        # 🕒 تحديث مواعيد العمل
        # =========================
        working_times = request.data.get("working_times", [])

        if barber and working_times:

            # ❌ حذف القديم (اختياري حسب نظامك)
            barber.working_times.all().delete()

            # ✔ إضافة الجديد
            for wt in working_times:
                from branches.models import Branch

                branch = Branch.objects.get(id=wt["branch_id"])

                barber.working_times.create(
                    branch=branch,
                    date=wt["date"],
                    start_time=wt["start_time"],
                    end_time=wt["end_time"],
                    clients_per_hour=wt.get("clients_per_hour", 1)
                )

        return Response({
            "status": "success",
            "message": "Profile updated successfully"
        })
    

# =========================
# 👁 Portfolio View
# =========================
class BarberPortfolioView(APIView):

    def get(self, request, barber_id):

        barber = get_object_or_404(BarberProfile, id=barber_id)

        portfolio = getattr(barber, "portfolio", None)

        images = [
            request.build_absolute_uri(img.image.url)
            for img in barber.portfolio_images.all()
        ]

        sessions = UserSession.objects.filter(
            user=barber.user
        ).order_by("-created_at")[:5]

        return Response({
            "name": barber.user.name,
            "bio": portfolio.bio if portfolio else "",
            "images": images,
            "last_sessions": [
                {
                    "device_name": s.device_name,
                    "platform": s.platform,
                    "ip_address": s.ip_address,
                    "lat": s.lat,
                    "lng": s.lng
                }
                for s in sessions
            ]
        })


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

        sessions = UserSession.objects.filter(user=user)\
            .order_by("-created_at")

        data = []

        for s in sessions:
            country, city = get_location_from_coords(s.lat, s.lng)

            data.append({
                "id": s.id,
                "device_name": s.device_name,
                "platform": s.platform,
                "ip_address": s.ip_address,
                "country": country,
                "city": city,
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