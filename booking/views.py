from datetime import datetime, timedelta, date as dt_date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import CreateAPIView

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from barber_accounts.models import WorkingTime, BarberProfile
from branches.models import Branch
from customers_accounts.models import CustomerProfile

from .models import Booking, Review
from .serializers import ReviewSerializer

# 🔥 Notification Service
from notifications.services import NotificationService


#===========================================
# عرض مواعيد الحجز المتاحة
#===========================================
from datetime import datetime, timedelta, date
class AvailableSlotsView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        branch = get_object_or_404(
            Branch,
            id=request.data.get("branch_id")
        )

        barber = get_object_or_404(
            BarberProfile,
            id=request.data.get("barber_id")
        )

        today = date.today()
        now = datetime.now()

        # =========================
        # 🔥 فقط اليوم والمستقبل
        # =========================
        working_days = WorkingTime.objects.filter(
            barber=barber,
            branch=branch,
            date__gte=today
        ).order_by("date")

        result = []

        for day in working_days:

            start_dt = datetime.combine(day.date, day.start_time)
            end_dt = datetime.combine(day.date, day.end_time)

            slots = []
            slot_duration = timedelta(hours=1)

            current = start_dt

            while current < end_dt:

                slot_time = current.time()

                # =========================
                # 🔥 منع الوقت اللي فات في نفس اليوم
                # =========================
                if day.date == today and current < now:
                    current += slot_duration
                    continue

                booked_count = Booking.objects.filter(
                    barber=barber,
                    branch=branch,
                    date=day.date,
                    time=slot_time,
                    status__in=["pending", "confirmed"]
                ).count()

                if booked_count < day.clients_per_hour:
                    slots.append(slot_time.strftime("%H:%M"))

                current += slot_duration

            if slots:
                result.append({
                    "date": day.date.strftime("%Y-%m-%d"),
                    "slots": slots
                })

        return Response({
            "status": "success",
            "available_days": result
        })


#===========================================
# إنشاء حجز داخل المحل
#===========================================
class CreateShopBookingView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        branch = get_object_or_404(
            Branch,
            id=request.data.get("branch_id")
        )

        barber = get_object_or_404(
            BarberProfile,
            id=request.data.get("barber_id")
        )

        booking_date = dt_date.fromisoformat(
            request.data.get("date")
        )

        booking_time = datetime.strptime(
            request.data.get("time"),
            "%H:%M"
        ).time()

        customer = get_object_or_404(
            CustomerProfile,
            user=request.user
        )

        # =========================
        # منع تعدد الحجوزات النشطة
        # =========================
        if Booking.objects.filter(
            user=customer,
            status__in=["pending", "confirmed"]
        ).exists():

            return Response({
                "error": "active booking exists"
            }, status=400)

        with transaction.atomic():

            working_time = WorkingTime.objects.select_for_update().filter(
                barber=barber,
                branch=branch,
                date=booking_date
            ).first()

            if not working_time:

                return Response({
                    "error": "barber not working"
                }, status=400)

            booked_count = Booking.objects.select_for_update().filter(
                barber=barber,
                branch=branch,
                date=booking_date,
                time=booking_time,
                status__in=["pending", "confirmed"]
            ).count()

            if booked_count >= working_time.clients_per_hour:

                return Response({
                    "error": "slot full"
                }, status=400)

            booking = Booking.objects.create(
                barber=barber,
                branch=branch,
                user=customer,
                booking_type="shop",
                date=booking_date,
                time=booking_time,
                status="pending"
            )

            # =========================
            # إشعار للحلاق
            # =========================
            NotificationService.send_notification(
                
                user=barber.user,
                title="🔥 حجز جديد",
                body=f"لديك حجز جديد يوم {booking.date}",
                notification_type="barber_advance_booking",
                category="booking",
                screen="booking_details",
                extra_data={
                    "booking_id": booking.id,
                    "booking_type": booking.booking_type,
                    "date": str(booking.date),
                    "time": str(booking.time),
                }
            )

            # =========================
            # إشعار للعميل
            # =========================
            NotificationService.send_notification(
                user=request.user,
                title="✅ تم إنشاء الحجز",
                body="تم إرسال طلب الحجز بنجاح",
                notification_type="user_advance_booking",
                category="booking",
                screen="my_bookings",
                extra_data={
                    "booking_id": booking.id,
                }
            )

        return Response({
            "message": "booking created",
            "booking_id": booking.id
        })


#===========================================
# إنشاء حجز منزلي
#===========================================
class CreateHomeBookingView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        branch = get_object_or_404(
            Branch,
            id=request.data.get("branch_id")
        )

        barber = get_object_or_404(
            BarberProfile,
            id=request.data.get("barber_id")
        )

        booking_date = dt_date.fromisoformat(
            request.data.get("date")
        )

        booking_time = datetime.strptime(
            request.data.get("time"),
            "%H:%M"
        ).time()

        location_url = request.data.get("location_url")

        customer = get_object_or_404(
            CustomerProfile,
            user=request.user
        )

        if Booking.objects.filter(
            user=customer,
            status__in=["pending", "confirmed"]
        ).exists():

            return Response({
                "error": "active booking exists"
            }, status=400)

        with transaction.atomic():

            working_time = WorkingTime.objects.select_for_update().filter(
                barber=barber,
                branch=branch,
                date=booking_date
            ).first()

            if not working_time:

                return Response({
                    "error": "barber not working"
                }, status=400)

            booked_count = Booking.objects.select_for_update().filter(
                barber=barber,
                branch=branch,
                date=booking_date,
                time=booking_time,
                status__in=["pending", "confirmed"]
            ).count()

            if booked_count >= working_time.clients_per_hour:

                return Response({
                    "error": "slot full"
                }, status=400)

            booking = Booking.objects.create(
                barber=barber,
                branch=branch,
                user=customer,
                booking_type="home",
                date=booking_date,
                time=booking_time,
                location_url=location_url,
                status="pending"
            )

            # =========================
            # إشعار للحلاق
            # =========================
            NotificationService.send_notification(
                user=barber.user,
                title="🏠 حجز منزلي جديد",
                body=f"لديك حجز منزلي يوم {booking.date}",
                notification_type="barber_home_booking",
                category="booking",
                screen="booking_details",
                extra_data={
                    "booking_id": booking.id,
                    "booking_type": booking.booking_type,
                    "date": str(booking.date),
                    "time": str(booking.time),
                    "location_url": booking.location_url,
                }
            )

            # =========================
            # إشعار للعميل
            # =========================
            NotificationService.send_notification(
                user=request.user,
                title="✅ تم إرسال الحجز المنزلي",
                body="تم إرسال طلب الحجز المنزلي بنجاح",
                notification_type="user_home_booking",
                category="booking",
                screen="my_bookings",
                extra_data={
                    "booking_id": booking.id,
                }
            )

        return Response({
            "message": "home booking created",
            "booking_id": booking.id
        })


#===========================================
# حجوزات المستخدم
#===========================================
class MyBookingsView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        customer = get_object_or_404(
            CustomerProfile,
            user=request.user
        )

        bookings = Booking.objects.filter(
            user=customer
        ).order_by("-date")

        data = []

        for b in bookings:

            booking_datetime = datetime.combine(
                b.date,
                b.time
            )

            can_review = (
                b.status == "completed"
                and not getattr(b, "is_reviewed", False)
                and booking_datetime <= datetime.now()
            )

            data.append({
                "booking_id": b.id,
                "barber_name": b.barber.user.name,
                "date": b.date,
                "time": b.time,
                "status": b.status,
                "type": b.booking_type,
                "is_reviewed": getattr(b, "is_reviewed", False),
                "can_review": can_review
            })

        return Response(data)

    def patch(self, request):

        action = request.data.get("action")
        booking_id = request.data.get("booking_id")

        customer = get_object_or_404(
            CustomerProfile,
            user=request.user
        )

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            user=customer
        )

        booking_datetime = datetime.combine(
            booking.date,
            booking.time
        )

        if booking.status in ["confirmed", "completed"]:

            return Response({
                "error": "cannot modify"
            }, status=400)

        if booking_datetime - datetime.now() <= timedelta(minutes=30):

            return Response({
                "error": "too late"
            }, status=400)

        if action == "cancel":

            booking.status = "cancelled"
            booking.save()

            return Response({
                "message": "cancelled"
            })

        return Response({
            "error": "invalid action"
        }, status=400)


#===========================================
# حجوزات الحلاق
#===========================================
class BarberBookingsView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        barber = get_object_or_404(
            BarberProfile,
            user=request.user
        )

        # =========================
        # 🔥 فلترة الحجوزات (بدون completed/cancelled)
        # =========================
        bookings = Booking.objects.filter(
            barber=barber,
            status__in=["pending", "confirmed"]
        ).order_by("date", "time")

        data = []

        for b in bookings:

            data.append({
                "id": b.id,
                "customer_name": b.user.user.name,
                "customer_phone": b.user.user.phone,
                "date": b.date,
                "time": b.time,
                "type": b.booking_type,
                "status": b.status,
                "location_url": b.location_url
            })

        return Response(data)

    def patch(self, request):

        barber = get_object_or_404(
            BarberProfile,
            user=request.user
        )

        booking_id = request.data.get("booking_id")
        action = request.data.get("action")

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            barber=barber
        )

        if action == "cancel":

            booking.status = "cancelled"

        elif action == "confirm":

            if booking.status != "pending":
                return Response({"error": "invalid state"}, status=400)

            booking.status = "confirmed"

        elif action == "complete":

            if booking.status != "confirmed":
                return Response({"error": "must be confirmed first"}, status=400)

            booking.status = "completed"

        else:
            return Response({"error": "invalid action"}, status=400)

        booking.save()

        # =========================
        # 🔔 Notifications
        # =========================
        if action == "confirm":

            NotificationService.send_notification(
                user=booking.user.user,
                title="✅ تم تأكيد الحجز",
                body="قام الحلاق بتأكيد الحجز الخاص بك",
                notification_type="user_advance_booking",
                category="booking",
                screen="my_bookings",
                extra_data={
                    "booking_id": booking.id,
                    "status": booking.status
                }
            )

        elif action == "cancel":

            NotificationService.send_notification(
                user=booking.user.user,
                title="❌ تم إلغاء الحجز",
                body="قام الحلاق بإلغاء الحجز",
                notification_type="general",
                category="booking",
                screen="my_bookings",
                extra_data={
                    "booking_id": booking.id,
                    "status": booking.status
                }
            )

        elif action == "complete":

            NotificationService.send_notification(
                user=booking.user.user,
                title="🎉 اكتمل الحجز",
                body="تم إنهاء الخدمة بنجاح",
                notification_type="general",
                category="booking",
                screen="my_bookings",
                extra_data={
                    "booking_id": booking.id,
                    "status": booking.status
                }
            )

        return Response({
            "message": f"{action} done",
            "status": booking.status
        })
    
    
#===========================================
# التقييم
#===========================================
class CreateReviewView(CreateAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        user = get_object_or_404(
            CustomerProfile,
            user=self.request.user
        )

        booking = serializer.validated_data["booking"]
        rating = serializer.validated_data["rating"]
        comment = serializer.validated_data.get("comment", "")

        if booking.status != "completed":
            raise Exception("لا يمكن التقييم قبل اكتمال الحجز")

        review = serializer.save(
            user=user,
            barber=booking.barber
        )

        # =========================
        # تحديث الحجز
        # =========================
        booking.is_reviewed = True
        booking.save()

        # =========================
        # إشعار للحلاق
        # =========================
        NotificationService.send_notification(
            user=booking.barber.user,
            title="⭐ تقييم جديد",
            body=f"حصلت على تقييم {rating} نجوم",
            notification_type="new_review",
            category="review",
            screen="reviews",
            extra_data={
                "booking_id": booking.id,
                "rating": rating,
                "comment": comment
            }
        )

        # =========================
        # لو التقييم سلبي
        # =========================
        if rating <= 2:

            try:

                subject = "🚨 تقييم سلبي جديد"

                message = f"""
                تم استلام تقييم سلبي:

                👤 اسم العميل: {user.user.name}
                📞 الهاتف: {user.user.phone}
                📧 البريد: {user.user.email}

                💈 الحلاق: {booking.barber.user.name}

                ⭐ التقييم: {rating}
                💬 التعليق: {comment}

                📅 تاريخ الحجز: {booking.date} {booking.time}
                """

                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    ["aslah4791@gmail.com"],
                    fail_silently=True,
                )

            except Exception as e:
                print("Email failed:", e)

        return review

    def create(self, request, *args, **kwargs):

        response = super().create(request, *args, **kwargs)

        return Response({
            "message": "تم إضافة التقييم",
            "data": response.data
        }, status=201)