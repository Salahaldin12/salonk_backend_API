from datetime import datetime, timedelta, date as dt_date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.shortcuts import get_object_or_404

from barber_accounts.models import WorkingTime, BarberProfile
from branches.models import Branch
from customers_accounts.models import CustomerProfile
from .models import Booking
from datetime import datetime, timedelta


#===========================================
# عرض مواعيد الحجز المتاحه للمستخدك 
#===========================================
class AvailableSlotsView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        branch_id = request.data.get("branch_id")
        barber_id = request.data.get("barber_id")

        branch = get_object_or_404(Branch, id=branch_id)
        barber = get_object_or_404(BarberProfile, id=barber_id)

        working_days = WorkingTime.objects.filter(
            barber=barber,
            branch=branch
        ).order_by("date")

        result = []

        for day in working_days:

            start = day.start_time
            end = day.end_time

            current = datetime.combine(day.date, start)
            end_datetime = datetime.combine(day.date, end)

            slots = []
            slot_duration = timedelta(hours=1)

            while current < end_datetime:

                slot_time = current.time()

                booked_count = Booking.objects.filter(
                    barber=barber,
                    branch=branch,
                    date=day.date,
                    time=slot_time,
                    status__in=["pending", "confirmed"]
                ).count()

                if booked_count < day.clients_per_hour:
                    slots.append(slot_time)

                current += slot_duration

            if slots:  # لو في ساعات متاحة
                result.append({
                    "date": day.date,
                    "slots": slots
                })

        return Response({
            "available_days": result
        })
    
#===========================================
# انشاء حجز داخل المحل 
#===========================================

from django.db import transaction

class CreateShopBookingView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        branch = get_object_or_404(Branch, id=request.data.get("branch_id"))
        barber = get_object_or_404(BarberProfile, id=request.data.get("barber_id"))

        booking_date = dt_date.fromisoformat(request.data.get("date"))
        booking_time = datetime.strptime(request.data.get("time"), "%H:%M").time()

        customer_profile = get_object_or_404(CustomerProfile, user=request.user)

        # 🚫 منع تعدد الحجوزات
        if Booking.objects.filter(
            user=customer_profile,
            status__in=["pending", "confirmed"]
        ).exists():
            return Response({"error": "active booking exists"}, status=400)

        # 🔒 بداية الترانزاكشن
        with transaction.atomic():

            working_time = WorkingTime.objects.select_for_update().filter(
                barber=barber,
                branch=branch,
                date=booking_date
            ).first()

            if not working_time:
                return Response({"error": "barber not working"}, status=400)

            # 🔒 lock على الحجوزات
            booked_count = Booking.objects.select_for_update().filter(
                barber=barber,
                branch=branch,
                date=booking_date,
                time=booking_time,
                status__in=["pending", "confirmed"]
            ).count()

            if booked_count >= working_time.clients_per_hour:
                return Response({"error": "slot full"}, status=400)

            # ✅ إنشاء آمن
            booking = Booking.objects.create(
                barber=barber,
                branch=branch,
                user=customer_profile,
                booking_type="shop",
                date=booking_date,
                time=booking_time,
                status="pending"
            )

        return Response({
            "message": "booking created safely",
            "booking_id": booking.id
        })

#===========================================
#انشاءحجز منزلي 
#===========================================

from django.db import transaction

class CreateHomeBookingView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        branch = get_object_or_404(Branch, id=request.data.get("branch_id"))
        barber = get_object_or_404(BarberProfile, id=request.data.get("barber_id"))

        booking_date = dt_date.fromisoformat(request.data.get("date"))
        booking_time = datetime.strptime(request.data.get("time"), "%H:%M").time()

        location_url = request.data.get("location_url")

        customer_profile = get_object_or_404(CustomerProfile, user=request.user)

        # 🚫 منع تعدد الحجوزات
        if Booking.objects.filter(
            user=customer_profile,
            status__in=["pending", "confirmed"]
        ).exists():
            return Response({"error": "active booking exists"}, status=400)

        # 🔒 بداية الترانزاكشن
        with transaction.atomic():

            # 🔒 lock على مواعيد العمل
            working_time = WorkingTime.objects.select_for_update().filter(
                barber=barber,
                branch=branch,
                date=booking_date
            ).first()

            if not working_time:
                return Response({"error": "barber not working"}, status=400)

            # 🔒 lock على الحجوزات
            booked_count = Booking.objects.select_for_update().filter(
                barber=barber,
                branch=branch,
                date=booking_date,
                time=booking_time,
                status__in=["pending", "confirmed"]
            ).count()

            if booked_count >= working_time.clients_per_hour:
                return Response({"error": "slot full"}, status=400)

            # ✅ إنشاء آمن
            booking = Booking.objects.create(
                barber=barber,
                branch=branch,
                user=customer_profile,
                booking_type="home",
                date=booking_date,
                time=booking_time,
                location_url=location_url,
                status="pending"
            )

        return Response({
            "message": "home booking created safely",
            "booking_id": booking.id
        })

#===========================================
# حجوزات المستخدم (عرض + إلغاء)
#===========================================



class MyBookingsView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # عرض الحجوزات
    def get(self, request):

        customer = get_object_or_404(CustomerProfile, user=request.user)

        bookings = Booking.objects.filter(
            user=customer
        ).order_by("-date")

        data = []

        for b in bookings:
            data.append({
                "booking_id": b.id,
                "barber_name": b.barber.user.name,
                "date": b.date,
                "time": b.time,
                "status": b.status,
                "type": b.booking_type
            })

        return Response(data)


    # 🔥 cancel أو update
    def patch(self, request):

        action = request.data.get("action")  # cancel or update
        booking_id = request.data.get("booking_id")

        customer = get_object_or_404(CustomerProfile, user=request.user)

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            user=customer
        )

        # =========================
        # 🚫 منع التعديل في حالات معينة
        # =========================
        booking_datetime = datetime.combine(booking.date, booking.time)
        now = datetime.now()

        if booking.status in ["confirmed", "completed"]:
            return Response({"error": "cannot modify confirmed/completed booking"}, status=400)

        if booking_datetime - now <= timedelta(minutes=30):
            return Response({"error": "cannot modify booking within 30 minutes"}, status=400)

        # =========================
        # ❌ إلغاء الحجز
        # =========================
        if action == "cancel":
            booking.status = "cancelled"
            booking.save()

            return Response({
                "message": "booking cancelled",
                "booking_id": booking.id
            })

        # =========================
        # ✏️ تعديل الحجز
        # =========================
        elif action == "update":

            new_date = request.data.get("date")
            new_time = request.data.get("time")
            new_type = request.data.get("booking_type")
            location_url = request.data.get("location_url")

            branch = get_object_or_404(Branch, id=request.data.get("branch_id"))
            barber = get_object_or_404(BarberProfile, id=request.data.get("barber_id"))

            booking_date = datetime.strptime(new_date, "%Y-%m-%d").date()
            booking_time = datetime.strptime(new_time, "%H:%M").time()

            # 🔥 تحقق من المواعيد (للحجز داخل المحل فقط)
            working_time = WorkingTime.objects.filter(
                barber=barber,
                branch=branch,
                date=booking_date
            ).first()

            if not working_time:
                return Response({"error": "barber not working this day"}, status=400)

            booked_count = Booking.objects.filter(
                barber=barber,
                branch=branch,
                date=booking_date,
                time=booking_time,
                status__in=["pending", "confirmed"]
            ).exclude(id=booking.id).count()

            if booked_count >= working_time.clients_per_hour:
                return Response({"error": "slot full"}, status=400)

            # ✏️ تحديث البيانات
            booking.barber = barber
            booking.branch = branch
            booking.date = booking_date
            booking.time = booking_time
            booking.booking_type = new_type

            if new_type == "home":
                booking.location_url = location_url
            else:
                booking.location_url = None

            booking.save()

            return Response({
                "message": "booking updated",
                "booking_id": booking.id,
                "new_date": booking.date,
                "new_time": booking.time,
                "new_type": booking.booking_type
            })

        else:
            return Response({"error": "invalid action"}, status=400)

#===========================================
# عرض الحجوزات للحلاق 
#===========================================

class BarberBookingsView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # =========================
    # 📋 عرض الحجوزات
    # =========================
    def get(self, request):

        barber = get_object_or_404(BarberProfile, user=request.user)

        bookings = Booking.objects.filter(
            barber=barber
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

    # =========================
    # ✅ قبول / ❌ رفض الحجز
    # =========================
    def patch(self, request):

        barber = get_object_or_404(BarberProfile, user=request.user)

        booking_id = request.data.get("booking_id")
        action = request.data.get("action")  # confirm / cancel

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            barber=barber
        )

        # =========================
        # ❌ رفض الحجز
        # =========================
        if action == "cancel":
            booking.status = "cancelled"
            booking.save()

            return Response({
                "message": "booking cancelled",
                "booking_id": booking.id,
                "status": booking.status
            })

        # =========================
        # ✅ تأكيد الحجز
        # =========================
        elif action == "confirm":

            # 🔥 تحقق إن slot لسه فيه مكان
            working_time = WorkingTime.objects.filter(
                barber=barber,
                branch=booking.branch,
                date=booking.date
            ).first()

            if not working_time:
                return Response({"error": "invalid working day"}, status=400)

            booked_count = Booking.objects.filter(
                barber=barber,
                branch=booking.branch,
                date=booking.date,
                time=booking.time,
                status__in=["confirmed"]
            ).count()

            if booked_count >= working_time.clients_per_hour:
                return Response({"error": "slot full"}, status=400)

            booking.status = "confirmed"
            booking.save()

            return Response({
                "message": "booking confirmed",
                "booking_id": booking.id,
                "status": booking.status
            })

        else:
            return Response({"error": "invalid action"}, status=400)





