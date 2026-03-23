from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User
from barber_accounts.models import WorkingTime
from branches.models import Branch

# ===== Login Serializer =====
class BarberLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])

        if not user:
            raise serializers.ValidationError("بيانات الدخول غير صحيحة")

        if not user.is_active:
            raise serializers.ValidationError("الحساب غير مفعل")

        return user


# ===== WorkingTime Serializer =====
class WorkingTimeSerializer(serializers.ModelSerializer):

    branch_id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    clients_per_hour = serializers.IntegerField(default=3)

    class Meta:
        model = WorkingTime
        fields = [
            'branch_id',
            'date',
            'start_time',
            'end_time',
            'clients_per_hour'
        ]


# ===== Profile Serializer =====
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
        #print("gggggggggggggggggggggggggggg")
        extra_kwargs = {
            'email': {'required': False},
            'phone': {'required': False},
            'name': {'required': False},
        }

    def update(self, instance, validated_data):
        working_times_data = validated_data.pop("working_times", None)

        # تحديث بيانات المستخدم
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if working_times_data and hasattr(instance, "barber"):
            barber = instance.barber

            for slot in working_times_data:
                try:
                    branch = Branch.objects.get(id=slot["branch_id"])
                except Branch.DoesNotExist:
                    raise serializers.ValidationError("الفرع غير موجود")

                # تحديث أو إنشاء
                obj, created = WorkingTime.objects.update_or_create(
                    barber=barber,
                    branch=branch,
                    date=slot["date"],  # هنا نستخدم التاريخ الفعلي
                    defaults={
                        "start_time": slot["start_time"],
                        "end_time": slot["end_time"],
                        "clients_per_hour": slot.get("clients_per_hour", 3)
                    }
                )

        return instance