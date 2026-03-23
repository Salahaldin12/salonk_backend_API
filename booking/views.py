from datetime import datetime, timedelta, date as dt_date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from django.shortcuts import get_object_or_404

from barber_accounts.models import WorkingTime, BarberProfile
from branches.models import Branch
from customers_accounts.models import CustomerProfile
from .models import Booking


#===========================================
# عرض مواعيد الحجز المتاحه للمستخدك 
#===========================================
class AvailableSlotsView(APIView):

    authentication_classes = [TokenAuthentication]
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

class CreateShopBookingView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        branch = get_object_or_404(Branch, id=request.data.get("branch_id"))
        barber = get_object_or_404(BarberProfile, id=request.data.get("barber_id"))

        booking_date = dt_date.fromisoformat(request.data.get("date"))
        booking_time = datetime.strptime(request.data.get("time"), "%H:%M").time()

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
        ).count()

        if booked_count >= working_time.clients_per_hour:
            return Response({"error": "slot full"}, status=400)

        customer_profile = get_object_or_404(CustomerProfile, user=request.user)

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
            "booking_id": booking.id,
            "barber_name": barber.user.name,
            "date": booking_date,
            "time": booking_time
        })
    

#===========================================
#انشاءحجز منزلي 
#===========================================

class CreateHomeBookingView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        branch = get_object_or_404(Branch, id=request.data.get("branch_id"))
        barber = get_object_or_404(BarberProfile, id=request.data.get("barber_id"))

        booking_date = dt_date.fromisoformat(request.data.get("date"))
        booking_time = datetime.strptime(request.data.get("time"), "%H:%M").time()

        location_url = request.data.get("location_url")

        customer_profile = get_object_or_404(CustomerProfile, user=request.user)

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
            "booking_id": booking.id,
            "barber_name": barber.user.name,
            "date": booking_date,
            "time": booking_time
        })


#===========================================
# حجوزات المستخدم (عرض + إلغاء)
#===========================================

class MyBookingsView(APIView):

    authentication_classes = [TokenAuthentication]
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
                "status": b.status
            })

        return Response(data)


    # الغاء الحجز
    def patch(self, request):

        booking_id = request.data.get("booking_id")

        customer = get_object_or_404(CustomerProfile, user=request.user)

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            user=customer
        )

        booking.status = "cancelled"
        booking.save()

        return Response({
            "message": "booking cancelled",
            "booking_id": booking.id
        })

#===========================================
# عرض الحجوزات للحلاق 
#===========================================

class BarberBookingsView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # عرض الحجوزات
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

    # قبول او رفض الحجز
    def patch(self, request):

        barber = get_object_or_404(BarberProfile, user=request.user)

        booking_id = request.data.get("booking_id")
        new_status = request.data.get("status")

        if new_status not in ["confirmed", "rejected"]:
            return Response({"error": "invalid status"}, status=400)

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            barber=barber
        )

        booking.status = new_status
        booking.save()

        return Response({
            "message": "booking status updated",
            "booking_id": booking.id,
            "new_status": booking.status
        })
    





