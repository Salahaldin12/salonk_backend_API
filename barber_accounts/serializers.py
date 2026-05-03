from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User
from barber_accounts.models import WorkingTime
from branches.models import Branch


# =========================
# 🔐 Login Serializer
# =========================
class BarberLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            email=data['email'],
            password=data['password']
        )

        if not user:
            raise serializers.ValidationError("بيانات الدخول غير صحيحة")

        if not hasattr(user, "barber"):
            raise serializers.ValidationError("هذا الحساب ليس حساب حلاق")

        if not user.is_active:
            raise serializers.ValidationError("الحساب غير مفعل")

        return user


# =========================
# 🕒 Working Time Serializer
# =========================
class WorkingTimeSerializer(serializers.Serializer):

    branch_id = serializers.IntegerField(required=True)
    date = serializers.DateField(required=True)
    start_time = serializers.TimeField(required=True)
    end_time = serializers.TimeField(required=True)
    clients_per_hour = serializers.IntegerField(required=False, default=3)


# =========================
# 👤 Profile Serializer
# =========================
class EditProfileSerializer(serializers.ModelSerializer):

    profile_image = serializers.ImageField(required=False, allow_null=True)
    working_times = WorkingTimeSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = [
            'name',
            'email',
            'phone',
            'profile_image',
            'working_times'
        ]

        extra_kwargs = {
            'email': {'required': False},
            'phone': {'required': False},
            'name': {'required': False},
        }

    def update(self, instance, validated_data):

        # =========================
        # 🔹 Extract working times
        # =========================
        working_times_data = validated_data.pop("working_times", None)

        # =========================
        # 🔹 Update basic info
        # =========================
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # =========================
        # 🔹 Update Working Times
        # =========================
        if working_times_data and hasattr(instance, "barber"):

            barber = instance.barber

            # ❗ نحذف القديم (حسب نظامك)
            barber.working_times.all().delete()

            for slot in working_times_data:

                branch_id = slot.get("branch_id")

                # 🛑 حماية من الكراش
                if not branch_id:
                    continue

                try:
                    branch = Branch.objects.get(id=branch_id)
                except Branch.DoesNotExist:
                    continue  # أو ممكن ترجع error

                WorkingTime.objects.create(
                    barber=barber,
                    branch=branch,
                    date=slot.get("date"),
                    start_time=slot.get("start_time"),
                    end_time=slot.get("end_time"),
                    clients_per_hour=slot.get("clients_per_hour", 3)
                )

        return instance