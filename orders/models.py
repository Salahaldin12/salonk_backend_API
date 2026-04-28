from django.conf import settings
from django.db import models, transaction
from django.core.exceptions import ValidationError
from .constants import OrderStatus
from store.models import Product

User = settings.AUTH_USER_MODEL


class Order(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders"
    )

    full_name = models.CharField(max_length=150, verbose_name="اسم المستلم")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    address = models.TextField(verbose_name="عنوان التوصيل")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():

            old_status = None
            if self.pk:
                old_status = Order.objects.select_for_update().get(pk=self.pk).status
                if old_status == OrderStatus.DELIVERED:
                    raise ValidationError("❌ لا يمكن تعديل طلب تم تسليمه")

            super().save(*args, **kwargs)

            # خصم المخزون عند التحويل إلى CONFIRMED أو PROCESSING
            if old_status != self.status:
                if self.status in [OrderStatus.CONFIRMED, OrderStatus.PROCESSING]:
                    for item in self.items.select_related("product").select_for_update():
                        product = item.product
                        reserved_qty = getattr(item, 'reserved_qty', item.quantity)

                        if reserved_qty > product.stock:
                            raise ValidationError(
                                f"❌ الكمية غير متوفرة للمنتج: {product.name}"
                            )

                        product.stock -= reserved_qty
                        product.save()

                # إعادة الكميات عند الإلغاء
                elif self.status == OrderStatus.CANCELLED:
                    for item in self.items.select_related("product").select_for_update():
                        product = item.product
                        product.stock += item.quantity
                        product.save()

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"