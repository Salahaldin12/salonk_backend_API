from django.db import models
from accounts.models import User


# ===============================
# Main Categories
# ===============================
class Category(models.TextChoices):
    HAIR_CARE = ("hair_care", "العناية بالشعر")
    BEARD_CARE = ("beard_care", "العناية باللحية")
    TOOLS = ("tools", "أدوات الحلاقة")
    SKIN_CARE = ("skin_care", "العناية بالبشرة")
    PERSONAL_CARE = ("personal_care", "النظافة الشخصية")
    PROFESSIONAL_PRODUCTS = ("professional_products", "منتجات احترافية للصالونات")
    KIDS = ("kids", "قسم الأطفال")
    BUNDLES = ("bundles", "باكدجات")  # Bundles أو Kits


# ===============================
# Optional: Sub Categories
# ===============================
# ممكن نضيف SubCategory لاحقًا لكل Main Category لو حبينا فلترة أدق

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=200)

    category = models.CharField(max_length=50, choices=Category.choices)
    # sub_category = models.CharField(max_length=50, choices=SubCategory.choices, null=True, blank=True) 
    # ممكن نضيفها لاحقًا

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    image = models.ImageField(upload_to="products/", null=True, blank=True)

    def __str__(self):
        return self.name