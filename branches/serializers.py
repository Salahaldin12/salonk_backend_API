from rest_framework import serializers
from .models import Branch


class BranchSerializer(serializers.ModelSerializer):

    barber_name = serializers.CharField(source="barber.name", read_only=True)
    barber_phone = serializers.CharField(source="barber.phone", read_only=True)
    barber_email = serializers.EmailField(source="barber.email", read_only=True)
    barber_image = serializers.ImageField(source="barber.profile_image", read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id',
            'name',
            'lat',
            'lng',
            'location',
            'barber_name',
            'barber_phone',
            'barber_email',
            'barber_image',
        ]