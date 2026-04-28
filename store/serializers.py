from rest_framework import serializers
from .models import Product 

class ProductSerilizer(serializers.ModelSerializer):
    category_ar = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "brand",
            "category",        # القيمة الانجليزية
            "category_ar",     # 👈 النص العربي الجديد
            "rating",
            "stock",
            "created_at",
            "user",
            "image",
        ]