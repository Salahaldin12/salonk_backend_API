from django.db import models
from barber_accounts.models import BarberProfile

class Branch(models.Model):

    barber = models.ForeignKey(
        BarberProfile,
        on_delete=models.CASCADE,
        related_name='branches'
    )

    name = models.CharField(max_length=100)

    lat = models.DecimalField(max_digits=9, decimal_places=6)

    lng = models.DecimalField(max_digits=9, decimal_places=6)

    location = models.URLField()

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.barber}"