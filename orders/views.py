# orders/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.conf import settings
from .models import Order
from .serializers import OrderSerializer, OrderDetailSerializer
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated


# ==============================
# إنشاء طلب جديد
# ==============================
class CreateOrderAPIView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # تعطيل الطلبات مؤقتًا (اختبار)
        if hasattr(settings, "ORDERS_ENABLED") and not settings.ORDERS_ENABLED:
            return Response(
                {"detail": "الطلبات متوقفة مؤقتًا."},
                status=status.HTTP_403_FORBIDDEN
            )

        # التحقق من البيانات وحفظ الطلب
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # استخدام Serializer جديد لإظهار كل تفاصيل الطلب في الـ Response
        output_serializer = OrderDetailSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


# ==============================
# عرض تفاصيل طلب محدد
# ==============================
class OrderDetailAPIView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"


# ==============================
# عرض كل طلبات المستخدم
# ==============================
class UserOrdersListAPIView(generics.ListAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")



class MyOrdersView(ListAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).order_by("-created_at")