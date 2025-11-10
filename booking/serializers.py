from rest_framework import serializers
from .models import Booking, TimeSlot

# Serializer لموديل TimeSlot
class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'date', 'time', 'copacity']  # الحقول المتاحة في TimeSlot

# Serializer لموديل Booking مع تضمين تفاصيل TimeSlot
class BookingSerializer(serializers.ModelSerializer):
    timeslot = TimeSlotSerializer()  # Nested serializer

    class Meta:
        model = Booking
        fields = ['id', 'name', 'email', 'timeslot', 'status', 'created_at']