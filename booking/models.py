from django.db import models
from barber_accounts.models import BarberProfile
from customers_accounts.models import CustomerProfile
from branches.models import Branch


class Booking(models.Model):

    BOOKING_TYPE = [
        ("shop", "Shop"),
        ("home", "Home Service"),
    ]

    STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    # المستخدم الذي قام بالحجز
    user = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    # الحلاق
    barber = models.ForeignKey(
        BarberProfile,
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True
    )

    # الفرع
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    # نوع الحجز
    booking_type = models.CharField(
        max_length=10,
        choices=BOOKING_TYPE,
        default="shop"
    )

    # تاريخ الحجز
    date = models.DateField()

    # وقت الحجز
    time = models.TimeField()

    # يستخدم فقط للحجز المنزلي
    location_url = models.URLField(
        null=True,
        blank=True
    )

    # ملاحظات
    notes = models.TextField(
        null=True,
        blank=True
    )

    # حالة الحجز
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="pending"
    )

    # تاريخ إنشاء الحجز
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["date", "time"]
        unique_together = ["barber", "date", "time"]

    def __str__(self):
        return f"{self.user} - {self.barber} - {self.date} {self.time}"