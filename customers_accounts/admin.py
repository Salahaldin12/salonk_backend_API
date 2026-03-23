from django.contrib import admin
from .models import CustomerProfile

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'get_phone',
        'get_is_verified',
        'created_at',
    )

    list_filter = (
        'user__is_verified',
        'created_at',
    )

    search_fields = (
        'user__name',   # بدل username
        'user__email',
        'user__phone',  # بدل phone مباشرة
    )

    readonly_fields = (
        'created_at',
    )

    # دالة لجلب رقم الهاتف من User
    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = 'Phone'
    get_phone.admin_order_field = 'user__phone'

    # دالة لجلب حالة التحقق من User
    def get_is_verified(self, obj):
        return obj.user.is_verified
    get_is_verified.short_description = 'Verified'
    get_is_verified.admin_order_field = 'user__is_verified'