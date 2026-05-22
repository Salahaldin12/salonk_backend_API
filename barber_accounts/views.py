from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings

from rest_framework.views import APIView, csrf_exempt
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from barber_accounts.models import BarberPortfolio, BarberPortfolioImage
from accounts.models import User, UserSession
from accounts.utils import generate_reset_code
from booking.models import Booking, Review
from notifications.models import FCMDevice
from notifications.services import NotificationService
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

        # =========================
        # Validate Barber
        # =========================
        if not hasattr(user, "barber"):

            return Response({
                "error": "هذا الحساب ليس حلاق"
            }, status=403)

        # =========================
        # Validate Active
        # =========================
        if not user.is_active:

            return Response({
                "message": "الحساب غير مفعل"
            }, status=403)

        # =========================
        # Generate JWT
        # =========================
        refresh = RefreshToken.for_user(user)

        ip = get_client_ip(request)

        device_name = request.data.get(
            "device_name",
            "Unknown"
        )

        platform = request.data.get(
            "platform",
            "Unknown"
        )

        # =========================
        # Update User Login Info
        # =========================
        user.last_login_ip = ip
        user.last_login_device = device_name
        user.save()
        # =========================
        # 🔔 Save FCM Token
        # =========================
        fcm_token = request.data.get("fcm_token")

        if fcm_token:

            FCMDevice.objects.update_or_create(

                user=user,

                defaults={
                    "fcm_token": fcm_token,
                    "is_active": True
                }
            )

            print("✅ FCM TOKEN SAVED:", fcm_token)

        # =========================
        # Create Session
        # =========================
        UserSession.objects.create(
            user=user,
            refresh_token=str(refresh),
            device_name=device_name,
            platform=platform,
            ip_address=ip,
            lat=request.data.get("lat"),
            lng=request.data.get("lng")
        )

        # =========================
        # 🔔 Login Notification
        # =========================
        NotificationService.send_notification(
            user=user,
            title="تم تسجيل الدخول بنجاح",
            body=f"تم تسجيل الدخول من جهاز {device_name}",
            notification_type="login",
            category="security",
            screen="profile"
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

        # =========================
        # Get User
        # =========================
        user = get_object_or_404(
            User,
            email=email
        )

        # =========================
        # Validate Barber
        # =========================
        if not hasattr(user, "barber"):

            return Response({
                "error": "غير مصرح"
            }, status=403)

        # =========================
        # Change Password
        # =========================
        user.set_password(password)

        user.save()

        # =========================
        # 🔔 Push Notification
        # =========================
        NotificationService.send_notification(
            user=user,
            title="تم تغيير كلمة المرور",
            body="تم تحديث كلمة المرور الخاصة بحسابك بنجاح",
            notification_type="security",
            category="security",
            screen="profile"
        )

        # =========================
        # 📧 Success Email
        # =========================
        send_mail(

            subject="تم تغيير كلمة المرور بنجاح",

            message=(
                f"مرحباً {user.name},\n\n"
                "تم تغيير كلمة المرور الخاصة بحسابك بنجاح.\n\n"
                "إذا لم تقم بهذا التغيير، يرجى التواصل مع الدعم الفني فوراً."
            ),

            from_email=settings.EMAIL_HOST_USER,

            recipient_list=[user.email],

            fail_silently=False,
        )

        return Response({
            "status": "success"
        })


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
            data["branch_id"] = barber.branch.id if barber.branch else None

            # 🕒 Working times
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

            # 🧠 Portfolio
            portfolio = getattr(barber, "portfolio", None)

            data["portfolio"] = {
                "bio": portfolio.bio if portfolio else "",
                "experience_years": portfolio.experience_years if portfolio else 0,
                "specialization": portfolio.specialization if portfolio else ""
            }

            # 📸 Images
            data["images"] = [
                request.build_absolute_uri(img.image.url)
                for img in barber.portfolio_images.all()
            ]

        return Response({
            "status": "success",
            "data": data
        })

    # =========================
    # ✏️ UPDATE PROFILE
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
        # 🧠 Portfolio Update
        # =========================
        if barber:

            from barber_accounts.models import BarberPortfolio, BarberPortfolioImage

            portfolio, created = BarberPortfolio.objects.get_or_create(barber=barber)

            portfolio.bio = request.data.get("bio", portfolio.bio)
            portfolio.experience_years = int(
                request.data.get("experience_years", portfolio.experience_years)
            )
            portfolio.specialization = request.data.get(
                "specialization",
                portfolio.specialization
            )

            portfolio.save()

        # =========================
        # 📸 Upload Images
        # =========================
        images = request.FILES.getlist("images")

        if barber and images:
            for img in images:
                BarberPortfolioImage.objects.create(
                    barber=barber,
                    image=img
                )

        # =========================
        # 🕒 Working Times
        # =========================
        import json

        working_times = request.data.get("working_times", [])

        # 🔥 الحل هنا
        if isinstance(working_times, str):
            working_times = json.loads(working_times)

        if barber and working_times:

            barber.working_times.all().delete()

            from branches.models import Branch

            for wt in working_times:
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

class BarberPortfolioPublicView(APIView):

    def get(self, request, barber_id):

        barber = get_object_or_404(BarberProfile, id=barber_id)

        portfolio = getattr(barber, "portfolio", None)

        # الصور
        images = [
            request.build_absolute_uri(img.image.url)
            for img in barber.portfolio_images.all()
        ]
        profile_image = None

        if barber.user.profile_image:
            profile_image = request.build_absolute_uri(
                barber.user.profile_image.url
            )

        return Response({
            # ===== Basic Info =====
            "profile_image": profile_image,
            "barber_id": barber.id,
            "name": barber.user.name,
            "phone": barber.user.phone,

            # ===== Portfolio Info =====
            "bio": portfolio.bio if portfolio else "",
            "experience_years": portfolio.experience_years if portfolio else 0,

            # ===== Portfolio Images =====
            "images": images
        })

# =====================================
# =====================================

class DeletePortfolioImageView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):

        user = request.user

        barber = getattr(user, "barber", None)

        if not barber:
            return Response({
                "error": "Barber profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

        image_url = request.data.get("image")

        if not image_url:
            return Response({
                "error": "Image url required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # =========================
        # Find Image
        # =========================
        image_obj = None

        for img in barber.portfolio_images.all():

            full_url = request.build_absolute_uri(img.image.url)

            if full_url == image_url:
                image_obj = img
                break

        if not image_obj:
            return Response({
                "error": "Image not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # =========================
        # Delete File From Storage
        # =========================
        if image_obj.image:
            image_obj.image.delete(save=False)

        # =========================
        # Delete DB Record
        # =========================
        image_obj.delete()

        return Response({
            "status": "success",
            "message": "Image deleted successfully"
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
    

#======================================
# التحليلات 
#=====================================

from django.db.models import Count, Avg
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


from barber_accounts.models import BarberProfile

class BarberAnalyticsView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        barber = BarberProfile.objects.get(
            user=request.user
        )

        bookings = Booking.objects.filter(
            barber=barber
        )

        # =========================
        # Overview
        # =========================
        total_bookings = bookings.count()

        completed = bookings.filter(
            status="completed"
        ).count()

        cancelled = bookings.filter(
            status="cancelled"
        ).count()

        pending = bookings.filter(
            status="pending"
        ).count()

        customers = bookings.values(
            "user"
        ).distinct().count()

        # =========================
        # Ratings
        # =========================
        reviews = Review.objects.filter(
            barber=barber
        )

        avg_rating = reviews.aggregate(
            Avg("rating")
        )["rating__avg"] or 0

        # =========================
        # Booking Status Chart
        # =========================
        booking_chart = bookings.values(
            "status"
        ).annotate(
            count=Count("id")
        )

        # =========================
        # Ratings Distribution
        # =========================
        ratings_chart = reviews.values(
            "rating"
        ).annotate(
            count=Count("id")
        ).order_by("rating")

        return Response({

            "overview": {

                "total_bookings": total_bookings,
                "completed_bookings": completed,
                "cancelled_bookings": cancelled,
                "pending_bookings": pending,
                "total_customers": customers,
                "average_rating": round(avg_rating, 1)

            },

            "booking_status_chart": booking_chart,

            "ratings_distribution": ratings_chart

        })




