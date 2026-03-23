from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate

# Serializer لتسجيل مستخدم جديد
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'password']  # لا نجبر على الصورة هنا

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# Serializer لتسجيل الدخول
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid Credentials")


# Serializer لتعديل بيانات الملف الشخصي
class EditProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'profile_image']
        extra_kwargs = {
            'email': {'required': False},
            'phone': {'required': False},
            'name': {'required': False},
        }

    def update(self, instance, validated_data):
        # تعديل كل الحقول إذا وجدت في الطلب
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
