from rest_framework import serializers
from barber_accounts.models import WorkingTime, BarberProfile
from branches.models import Branch
from .models import Booking
from customers_accounts.models import CustomerProfile

from rest_framework import serializers
from .models import Review, Booking

# ===============================
# 1️⃣ Working Time Serializer
# ===============================
class WorkingTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingTime
        fields = [
            "id",
            "branch",
            "barber",
            "date",
            "start_time",
            "end_time",
            "clients_per_hour"
        ]


# ===============================
# 2️⃣ Available Slots Serializer
# ===============================
class AvailableSlotsSerializer(serializers.Serializer):
    branch_id = serializers.IntegerField()
    barber_id = serializers.IntegerField()
    date = serializers.DateField()


# ===============================
# 3️⃣ Create Booking Serializer
# ===============================
class CreateBookingSerializer(serializers.ModelSerializer):
    branch_id = serializers.IntegerField(write_only=True)
    barber_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField(write_only=True)  # CustomerProfile

    class Meta:
        model = Booking
        fields = [
            "id",
            "branch_id",
            "barber_id",
            "user_id",
            "booking_type",
            "date",
            "time",
            "location_url",
            "status"
        ]
        read_only_fields = ["id", "status"]

    def validate(self, data):
        # ===== التحقق من الفرع =====
        try:
            branch = Branch.objects.get(id=data["branch_id"])
        except Branch.DoesNotExist:
            raise serializers.ValidationError("Branch not found")

        # ===== التحقق من الحلاق =====
        try:
            barber = BarberProfile.objects.get(id=data["barber_id"])
        except BarberProfile.DoesNotExist:
            raise serializers.ValidationError("Barber not found")

        # ===== التحقق من المستخدم =====
        try:
            user = CustomerProfile.objects.get(id=data["user_id"])
        except CustomerProfile.DoesNotExist:
            raise serializers.ValidationError("Customer not found")

        data["branch"] = branch
        data["barber"] = barber
        data["user"] = user

        return data

    def create(self, validated_data):
        # إزالة الحقول المؤقتة
        validated_data.pop("branch_id")
        validated_data.pop("barber_id")
        validated_data.pop("user_id")

        return Booking.objects.create(**validated_data)


# ===============================
# 4️⃣ Booking Display Serializer
# ===============================
class BookingSerializer(serializers.ModelSerializer):
    barber_name = serializers.CharField(source="barber.user.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "barber",
            "barber_name",
            "branch",
            "branch_name",
            "name",
            "phone",
            "booking_type",
            "date",
            "time",
            "location_url",
            "status"
        ]



from customers_accounts.models import CustomerProfile
from rest_framework import serializers

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "booking", "rating", "comment", "created_at"]

    def validate(self, data):
        request = self.context["request"]

        # ✅ الحصول على العميل بطريقة آمنة
        try:
            user = CustomerProfile.objects.get(user=request.user)
        except CustomerProfile.DoesNotExist:
            raise serializers.ValidationError("المستخدم ليس عميل")

        booking = data.get("booking")

        # ✅ تحقق إن الحجز ملك المستخدم
        if booking.user != user:
            raise serializers.ValidationError("هذا الحجز لا يخصك")

        # ✅ لازم يكون مكتمل
        if booking.status != "completed":
            raise serializers.ValidationError("لا يمكن التقييم قبل اكتمال الحجز")

        # ✅ لازم يكون فيه حلاق
        if not booking.barber:
            raise serializers.ValidationError("لا يوجد حلاق مرتبط بالحجز")

        # ✅ منع التكرار
        if hasattr(booking, "review"):
            raise serializers.ValidationError("تم التقييم مسبقاً")

        return data