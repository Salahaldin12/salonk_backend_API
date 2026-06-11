from django.db import models
from django.contrib.auth import get_user_model

# استدعاء موديل المستخدم الخاص بمشروعك
User = get_user_model()

class HairTryOnRequest(models.Model):
    # ربط الطلب بالعميل (null=True لو أحببت أن يجربها زائر بدون تسجيل دخول)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # 1. صورة العميل الأصلية التي سيرفعها من تطبيق Flutter
    user_image = models.ImageField(upload_to='hair_tryon/originals/')
    
    # 2. الخيار النصي: اسم أو وصف القصة المطلوبة (مثال: "Fade haircut for men")
    haircut_name = models.CharField(max_length=255, blank=True, null=True)
    
    # 3. الخيار البديل: لو رفع صورة للقصة التي يريدها بدل النص (سنحتاجها لاحقاً)
    reference_image = models.ImageField(upload_to='hair_tryon/references/', blank=True, null=True)
    
    # 4. رابط الصورة الناتجة من الذكاء الاصطناعي التي سنستقبلها من الـ API
    generated_image_url = models.URLField(max_length=1000, blank=True, null=True)
    
    # حالة الطلب لأن الـ API يأخذ بضع ثوانٍ للمعالجة
    STATUS_CHOICES = [
        ('pending', 'جاري المعالجة'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل التوليد'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # وقت إنشاء الطلب
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"طلب قصة شعر رقم {self.id} - حالة الطلب: {self.get_status_display()}"