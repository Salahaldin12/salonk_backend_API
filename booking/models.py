from django.db import models
from barber_accounts.models import BarberProfile
from customers_accounts.models import CustomerProfile
from branches.models import Branch
from django.db import models
from django.db.models import Q


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

    user = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    barber = models.ForeignKey(
        BarberProfile,
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    booking_type = models.CharField(
        max_length=10,
        choices=BOOKING_TYPE,
        default="shop"
    )

    date = models.DateField()
    time = models.TimeField()

    location_url = models.URLField(null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]

        constraints = [
            # 🔥 يمنع user يعمل اكتر من حجز active
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status__in=["pending", "confirmed"]),
                name="unique_active_booking_per_user"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.barber} - {self.date} {self.time}"