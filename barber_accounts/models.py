from django.db import models
from accounts.models import User


class BarberProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='barber'
    )
    shop_name = models.CharField(max_length=150)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} Barber"


# ========================================
# WorkingTime بالتاريخ وليس اليوم
# ========================================
class WorkingTime(models.Model):

    barber = models.ForeignKey(
        BarberProfile,
        on_delete=models.CASCADE,
        related_name='working_times'
    )

    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='working_times'
    )

    # التاريخ الفعلي
    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    clients_per_hour = models.IntegerField(
        default=3
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('barber', 'branch', 'date')

    def __str__(self):
        return f"{self.barber.user.name} - {self.date} ({self.start_time}-{self.end_time})"