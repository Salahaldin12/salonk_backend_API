from django.db import models
from accounts.models import User

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    # بيانات إضافية للمستخدم العادي
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_customer = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.name} Profile"