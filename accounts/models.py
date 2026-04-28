from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# =========================
# User Manager
# =========================
class UserManager(BaseUserManager):
    def create_user(self, email, name, phone, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            name=name,
            phone=phone,
            is_active=True,      # 🔥 الحل هنا
            is_verified=True     # 🔥 مهم جدًا
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone, password=None):
        user = self.create_user(email, name, phone, password)

        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user
# =========================
# User Model
# =========================
class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)

    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True
    )

    verification_code = models.CharField(max_length=6, blank=True, null=True)
    reset_code = models.CharField(max_length=6, blank=True, null=True)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # 🔥 معلومات آخر تسجيل دخول (للأمان)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=255, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone']

    def __str__(self):
        return self.email


# =========================
# User Session Model
# =========================
class UserSession(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sessions"
    )
    # 🔥 الموقع (مهم للـ GPS)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    # 🔐 التوكن الأساسي للجلسة
    refresh_token = models.TextField()

    # 📱 معلومات الجهاز
    device_name = models.CharField(max_length=255)
    platform = models.CharField(max_length=50)

    # 🌍 معلومات الشبكة
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)

    # 🟢 حالة الجلسة
    is_active = models.BooleanField(default=True)

    # ⏱️ النشاط
    last_activity = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.device_name}"