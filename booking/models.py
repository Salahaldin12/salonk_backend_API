from django.db import models
from django.utils import timezone

# Create your models here.

class TimeSlot(models.Model):
    date = models.DateField()
    time = models.TimeField()
    copacity = models.PositiveBigIntegerField(default=3) #عدد الأشخاص المسموح لهم في نفس الوقت


    class Meta:
        unique_together = ('date', 'time')  # منع التكرار لنفس الوقت 
        ordering = ['date','time']

    def __str__(self):
        return f"{self.date} - {self.time} (Capacity: {self.copacity})"
    

    def available_slots(self):
        """تحسب عدد الأماكن المتاحة بناءً على عدد الحجوزات الحالية"""
        current_booking = self.bookings.filter(status='pending').count()
        return max(self.copacity - current_booking, 0)

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField()
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    #date = models.DateField() #اليوم 
    #time = models.TimeField() #الوقت
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        #unique_together = ('date', 'time')  # منع التكرار لنفس الوقت مع المستخدم 
        ordering = ['timeslot__date', 'timeslot__time']



    def __str__(self):
        return f"{self.name} - {self.timeslot.date} at {self.timeslot.time}"
