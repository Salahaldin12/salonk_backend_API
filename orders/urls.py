# orders/urls.py
from django.urls import path
from .views import CreateOrderAPIView, MyOrdersView, OrderDetailAPIView, UserOrdersListAPIView

urlpatterns = [
    path("create/", CreateOrderAPIView.as_view(), name="create-order"),
    path("<int:id>/", OrderDetailAPIView.as_view(), name="order-detail"),
    path("my-orders/", UserOrdersListAPIView.as_view(), name="user-orders"),
    path("my-orders/", MyOrdersView.as_view()),
]