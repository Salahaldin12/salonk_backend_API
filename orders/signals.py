from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import Order


@receiver(pre_save, sender=Order)
def order_status_changed(sender, instance, **kwargs):
    if not instance.pk:
        return  # طلب جديد، مش تغيير حالة

    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    if old_order.status != instance.status:
        subject = f"تحديث حالة الطلب رقم #{instance.id}"

        message = f"""
مرحبًا {instance.full_name} 👋

نحب نبلغك إن حالة طلبك رقم #{instance.id} اتغيرت.

🔄 الحالة الجديدة:
{instance.get_status_display()}

📦 إجمالي الطلب:
{instance.total_price} جنيه

شكراً لاختيارك Verde Life 🌱
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=False,
        )