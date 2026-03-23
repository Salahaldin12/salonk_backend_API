from django import forms
from django.contrib import admin
from .models import BarberProfile
from accounts.models import User

# ModelForm مخصص للـ Admin
class BarberProfileAdminForm(forms.ModelForm):
    # اختيار مستخدم موجود ليكون حلاق
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        help_text="اختار مستخدم ليصبح حلاق"
    )

    class Meta:
        model = BarberProfile
        fields = '__all__'

@admin.register(BarberProfile)
class BarberProfileAdmin(admin.ModelAdmin):
    form = BarberProfileAdminForm

    list_display = (
        'id',
        'user',
        'shop_name',
        'get_is_active',
        'get_is_verified',
        'created_at',
    )

    list_filter = (
        'user__is_active',
        'user__is_verified',
        'created_at',
    )

    search_fields = (
        'user__name',
        'user__email',
        'shop_name',
    )

    readonly_fields = (
        'created_at',
    )

    # عرض حالة النشاط من User
    def get_is_active(self, obj):
        return obj.user.is_active
    get_is_active.short_description = 'Active'
    get_is_active.admin_order_field = 'user__is_active'

    # عرض حالة التحقق من User
    def get_is_verified(self, obj):
        return obj.user.is_verified
    get_is_verified.short_description = 'Verified'
    get_is_verified.admin_order_field = 'user__is_verified'