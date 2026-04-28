from django.contrib import admin
from django.urls import path, include

# 👇 ضيف دول
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('store/', include('store.urls')),
    path('orders/', include('orders.urls')),
    path('booking/', include('booking.urls')),
   # path('accounts/', include('accounts.urls')),
    path('branches/', include('branches.urls')),
    path('barber_accounts/', include('barber_accounts.urls')),
    path('customers_accounts/', include('customers_accounts.urls')),
]

# 👇 مهم جدًا
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)