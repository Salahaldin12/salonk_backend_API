from datetime import date
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date, parse_time

from booking.booking_time import WORK_END, WORK_START
from .models import Booking, TimeSlot
import json

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@csrf_exempt
def create_booking(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        date_obj = parse_date(data.get('date'))
        time_obj = parse_time(data.get('time'))

        if not (name and email and date_obj and time_obj):
            return JsonResponse({'message': 'البيانات غير مكتملة'}, status=400)

        # تحقق من وقت العمل
        if not (WORK_START <= time_obj <= WORK_END):
            return JsonResponse({
                'status': 'error',
                'message': 'هذا الموعد خارج ساعات العمل الرسمية (من 10 صباحًا إلى 11 مساءً).'
            }, status=400)

        # نحاول نجيب أو ننشئ التايم سلوت (اليوم + الوقت)
        timeslot, created = TimeSlot.objects.get_or_create(date=date_obj, time=time_obj)

        # التحقق من السعة
        if timeslot.available_slots() <= 0:
            return JsonResponse({'message': 'هذا الوقت ممتلئ بالحجوزات حالياً'}, status=400)

        # تحقق هل للمستخدم حجز سابق في نفس التايم سلوت
        if Booking.objects.filter(name=name, timeslot=timeslot, status='pending').exists():
            return JsonResponse({'message': 'تم الحجز بالفعل في هذا الموعد'}, status=400)

        # إنشاء حجز جديد بالحالة pending
        Booking.objects.create(
            name=name,
            email=email,
            timeslot=timeslot,
            status='pending'
        )
        return JsonResponse({'message': 'تم الحجز بنجاح'}, status=201)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def waiting_count(user):
    user_booking = Booking.objects.filter(user=user, status='waiting').first()
    if not user_booking:
        return 0  # لم يحجز بعد
    """إرجاع عدد الأشخاص في الانتظار ليوم معين"""
    count = Booking.objects.filter(
        booking_date=user_booking.booking_date,
        status='pending'
    ).filter(
        Q(booking_time__lt=user_booking.booking_time) |
        Q(booking_time=user_booking.booking_time, created_at__lt=user_booking.created_at)
    ).count()

    return JsonResponse({'date': date, 'waiting_users': count}) 


def get_waiting_count(request):
    current_time = timezone.now().time()
    #waiting_count = Booking.objects.filter(time__gt=current_time,status="waiting").count()
    waiting_count = Booking.objects.filter(status="waiting").count()
    return JsonResponse({"waiting_count": waiting_count})



@csrf_exempt
def cancel_booking(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            email = data.get('email')

            if not (name and email):
                return JsonResponse({'message': 'البيانات غير مكتملة'}, status=400)

            # نبحث عن الحجز القائم
            booking = Booking.objects.filter(name=name, email=email, status='pending').first()

            if not booking:
                return JsonResponse({'message': 'لا يوجد حجز قائم لإلغائه'}, status=404)

            # نغير الحالة إلى ملغي
            booking.status = 'canceled'
            booking.save()

            # إشعار WebSocket لكل المستخدمين (لو عندك قناة بث)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "bookings_group",
                {
                    "type": "booking_update",
                    "event": "canceled",
                    "name": booking.name,
                    "email": booking.email,
                    "date": str(booking.date),
                    "time": booking.time.strftime('%H:%M'),
                    "status": booking.status
                }
            )

            return JsonResponse({'message': 'تم إلغاء الحجز بنجاح'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'message': 'صيغة البيانات غير صحيحة'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

#=========================================================================
# الحلاق 


def list_bookings(request):
    if request.method == 'GET':
        bookings = Booking.objects.select_related('timeslot').all().order_by('-id')

        booking_list = [
            {
                "id": b.id,
                "name": b.name,
                "email": b.email,
                "date": b.timeslot.date.strftime("%Y-%m-%d") if b.timeslot else None,
                "time": b.timeslot.time.strftime("%H:%M:%S") if b.timeslot else None,
                "status": b.status,
            }
            for b in bookings
        ]

        return JsonResponse({"bookings": booking_list}, safe=False, json_dumps_params={'ensure_ascii': False})

    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def complete_booking(request, booking_id):
    if request.method == "POST":
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.status = "completed"
            booking.save()
            return JsonResponse({"message": "تم تحديد الحجز كمكتمل بنجاح ✅"})
        except Booking.DoesNotExist:
            return JsonResponse({"error": "الحجز غير موجود"}, status=404)
    else:
        return JsonResponse({"error": "الطريقة غير مدعومة"}, status=405)

#$=============================================================

@csrf_exempt
def update_booking_status(request, booking_id):
    if request.method == 'PATCH':
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return JsonResponse({'message': 'الحجز غير موجود'}, status=404)

        data = json.loads(request.body)
        new_status = data.get('status')

        if new_status not in ['pending', 'completed', 'cancelled']:
            return JsonResponse({'message': 'حالة غير صالحة'}, status=400)

        booking.status = new_status
        booking.save()
        return JsonResponse({'message': f'تم تحديث حالة الحجز إلى {new_status} بنجاح'}, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)