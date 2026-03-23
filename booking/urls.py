from django.urls import path
from .views import (
    AvailableSlotsView,
    CreateShopBookingView,
    CreateHomeBookingView,
    MyBookingsView,
    BarberBookingsView,
)

urlpatterns = [

    # ===============================
    # 1️⃣ عرض المواعيد المتاحة
    # ===============================
    path(
        "available-slots/",
        AvailableSlotsView.as_view(),
        name="available-slots"
    ),

    # ===============================
    # 2️⃣ إنشاء حجز داخل المحل
    # ===============================
    path(
        "create-shop-booking/",
        CreateShopBookingView.as_view(),
        name="create-shop-booking"
    ),

    # ===============================
    # 3️⃣ إنشاء حجز منزلي
    # ===============================
    path(
        "create-home-booking/",
        CreateHomeBookingView.as_view(),
        name="create-home-booking"
    ),

    # ===============================
    # 4️⃣ عرض حجوزات المستخدم
    # ===============================
    path(
        "my-bookings/",
        MyBookingsView.as_view(),
        name="my-bookings"
    ),

    # ===============================
    # 6️⃣ الحجوزات الخاصة بالحلاق
    # عرض + قبول + رفض
    # ===============================
    path(
        "barber/bookings/",
        BarberBookingsView.as_view(),
        name="barber-bookings"
    ),

]