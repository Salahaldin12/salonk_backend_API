# orders/constants.py
from django.db import models

class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "قيد المراجعة"
    CONFIRMED = "CONFIRMED", "تم التأكيد"
    PROCESSING = "PROCESSING", "جاري التجهيز"
    SHIPPED = "SHIPPED", "تم الشحن"
    DELIVERED = "DELIVERED", "تم التسليم"
    CANCELLED = "CANCELLED", "تم الإلغاء"