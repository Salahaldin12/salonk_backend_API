from django.db import models
from accounts.models import User


class Notification(models.Model):

    # =========================================
    # Notification Types
    # =========================================
    NOTIFICATION_TYPES = (

        # Authentication
        ('login', 'Login'),

        # Barber Bookings
        ('barber_advance_booking', 'Barber Advance Booking'),
        ('barber_home_booking', 'Barber Home Booking'),

        # User Bookings
        ('user_advance_booking', 'User Advance Booking'),
        ('user_home_booking', 'User Home Booking'),

        # Profile
        ('profile_updated', 'Profile Updated'),

        # Reviews
        ('new_review', 'New Review'),

        # General
        ('general', 'General'),
    )

    # =========================================
    # Categories
    # =========================================
    CATEGORY_CHOICES = (

        ('auth', 'Authentication'),
        ('booking', 'Booking'),
        ('profile', 'Profile'),
        ('review', 'Review'),
        ('general', 'General'),
    )

    # =========================================
    # Receiver Types
    # =========================================
    RECEIVER_TYPES = (

        ('customer', 'Customer'),
        ('barber', 'Barber'),
        ('admin', 'Admin'),
    )

    # =========================================
    # Priority Levels
    # =========================================
    PRIORITY_CHOICES = (

        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    # =========================================
    # Main Fields
    # =========================================
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(
        max_length=255
    )

    body = models.TextField()

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default='general'
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='general'
    )

    receiver_type = models.CharField(
    max_length=20,
    choices=RECEIVER_TYPES,
    null=True,
    blank=True
)

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    # =========================================
    # Navigation
    # =========================================
    screen = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    # =========================================
    # Extra Data
    # =========================================
    extra_data = models.JSONField(
        null=True,
        blank=True
    )

    # =========================================
    # Device & Location
    # =========================================
    device_type = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    location = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # =========================================
    # Optional Image
    # =========================================
    image = models.URLField(
        null=True,
        blank=True
    )

    # =========================================
    # Notification Status
    # =========================================
    is_read = models.BooleanField(
        default=False
    )

    is_deleted = models.BooleanField(
        default=False
    )

    is_push_sent = models.BooleanField(
        default=False
    )

    # =========================================
    # Dates
    # =========================================
    push_sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # =========================================
    # Meta
    # =========================================
    class Meta:
        ordering = ['-created_at']

    # =========================================
    # String Representation
    # =========================================
    def __str__(self):
        return f"{self.user.email} - {self.notification_type}"
    


class FCMDevice(models.Model):

    APP_TYPES = (
        ('customer', 'Customer App'),
        ('barber', 'Barber App'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="fcm_devices"
    )

    fcm_token = models.TextField(
        unique=True
    )

    app_type = models.CharField(
        max_length=20,
        choices=APP_TYPES
    )

    device_type = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    device_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    last_seen = models.DateTimeField(
        auto_now=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.email} - {self.app_type}"