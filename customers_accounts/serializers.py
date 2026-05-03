from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User, UserSession
from customers_accounts.models import CustomerProfile


class CustomerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'password']

    def create(self, validated_data):
        # إنشاء المستخدم
        user = User.objects.create_user(**validated_data)

        # تعطيل الحساب حتى يتم التفعيل
        user.is_active = False
        user.save()

        # إنشاء بروفايل المستخدم العادي
        CustomerProfile.objects.create(user=user)

        return user


class CustomerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])

        if not user:
            raise serializers.ValidationError("بيانات الدخول غير صحيحة")

        # التأكد أن الحساب Customer
        if not hasattr(user, "customer"):
            raise serializers.ValidationError("هذا الحساب ليس حساب مستخدم")

        # التأكد أن الحساب مفعل
        if not user.is_active:
            raise serializers.ValidationError("الحساب غير مفعل")

        return user


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'name',
            'email',
            'phone',
            'profile_image',
        ]

        
class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = [
            "device_name",
            "platform",
            "ip_address",
            "country",
            "city",
            "created_at"
        ]