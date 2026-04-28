from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem
from store.models import Product
from .constants import OrderStatus
from django.db.models import Sum, Q


class OrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("المنتج غير موجود")
        return value


class OrderSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField()
    items = OrderItemSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("لا يمكن إنشاء طلب بدون منتجات")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        items_data = validated_data.pop("items")

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                full_name=validated_data["full_name"],
                phone=validated_data["phone"],
                address=validated_data["address"],
                total_price=0,
                status=OrderStatus.PENDING
            )

            total_price = 0
            order_items = []

            for item in items_data:
                product = Product.objects.select_for_update().get(id=item["product_id"])

                # حساب الكمية المحجوزة من الطلبات المفتوحة
                reserved_qty = (
                    OrderItem.objects
                    .filter(
                        product=product,
                        order__status__in=[
                            OrderStatus.PENDING,
                            OrderStatus.CONFIRMED,
                            OrderStatus.PROCESSING
                        ]
                    )
                    .aggregate(total_reserved=Sum('quantity'))['total_reserved'] or 0
                )

                available_stock = product.stock - reserved_qty
                if item["quantity"] > available_stock:
                    raise serializers.ValidationError(
                        f"الكمية المطلوبة من المنتج {product.name} غير متوفرة. المتاح بعد الحجز المؤقت: {available_stock}"
                    )

                price = product.price * item["quantity"]
                total_price += price

                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        quantity=item["quantity"],
                        price=price
                    )
                )

            OrderItem.objects.bulk_create(order_items)
            order.total_price = total_price
            order.save()

        return order


class OrderItemDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("product_id", "product_name", "quantity", "price")


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "full_name",
            "phone",
            "address",
            "status",
            "status_display",
            "total_price",
            "created_at",
            "items",
        )