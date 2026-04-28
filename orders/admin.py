from django.contrib import admin, messages
from django.utils.html import format_html
from .models import Order, OrderItem
from .constants import OrderStatus


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "quantity", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "colored_status",
        "total_price",
        "created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email")
    ordering = ("-created_at",)

    inlines = [OrderItemInline]

    readonly_fields = (
        "user",
        "total_price",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("معلومات الطلب", {
            "fields": ("user", "full_name", "phone", "address", "status", "total_price")
        }),
        ("التوقيت", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def colored_status(self, obj):
        colors = {
            OrderStatus.PENDING: "#f39c12",
            OrderStatus.CONFIRMED: "#3498db",
            OrderStatus.PROCESSING: "#8e44ad",
            OrderStatus.SHIPPED: "#16a085",
            OrderStatus.DELIVERED: "#27ae60",
            OrderStatus.CANCELLED: "#c0392b",
        }
        return format_html(
            '<b style="color:{}">{}</b>',
            colors.get(obj.status, "#000"),
            obj.get_status_display()
        )

    colored_status.short_description = "حالة الطلب"

    def save_model(self, request, obj, form, change):
        if change:
            old_status = Order.objects.get(pk=obj.pk).status

            if old_status == OrderStatus.DELIVERED:
                messages.error(request, "❌ لا يمكن تعديل طلب تم تسليمه")
                return  # ❗ يمنع الحفظ بوضوح

        super().save_model(request, obj, form, change)