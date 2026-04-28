from django.db import models
from django.core.exceptions import ValidationError
from datetime import date

from accounts.models import User


# ========================================
# 👨‍🦱 Barber Profile
# ========================================

class BarberProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='barber'
    )

    shop_name = models.CharField(max_length=150)

    # ✅ ربط مباشر بالحلاق بالفرع
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='barbers'
    )

    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} Barber"

# ========================================
# 🕒 Working Time
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

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    clients_per_hour = models.PositiveIntegerField(default=3)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('barber', 'branch', 'date')

    def __str__(self):
        return f"{self.barber.user.name} - {self.date}"
# ========================================
# 🔥 Portfolio Data
# ========================================
class BarberPortfolio(models.Model):

    barber = models.OneToOneField(
        BarberProfile,
        on_delete=models.CASCADE,
        related_name="portfolio"
    )

    bio = models.TextField(null=True, blank=True)
    experience_years = models.PositiveIntegerField(default=0)

    specialization = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.barber.user.name} Portfolio"


# ========================================
# 📸 Portfolio Images
# ========================================
class BarberPortfolioImage(models.Model):

    barber = models.ForeignKey(
        BarberProfile,
        on_delete=models.CASCADE,
        related_name="portfolio_images"
    )

    image = models.ImageField(upload_to="barber_portfolio/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.barber.user.name}"


# ========================================
# 👥 Team Members
# ========================================
class BarberTeamMember(models.Model):

    barber = models.ForeignKey(
        BarberProfile,
        on_delete=models.CASCADE,
        related_name="team_members"
    )

    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)

    image = models.ImageField(
        upload_to="barber_team/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.barber.user.name}"