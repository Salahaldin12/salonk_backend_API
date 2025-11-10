import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

class BookingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("booking_updates", self.channel_name)
        await self.accept()

        # أرسل العدد الحالي عند الاتصال
        count = await self.get_current_count()
        await self.send(text_data=json.dumps({
            "waiting_count": count
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("booking_updates", self.channel_name)

    async def receive(self, text_data):
        """لو المستخدم بعت رسالة عبر WebSocket (نادر هنا)"""
        data = json.loads(text_data)
        if data.get("action") == "get_count":
            count = await self.get_current_count()
            await self.send(text_data=json.dumps({
                "waiting_count": count
            }))

    async def booking_update(self, event):
        """يُستدعى تلقائياً عندما view تبعت إشعار تحديث"""
        await self.send(text_data=json.dumps({
            "waiting_count": event["waiting_count"]
        }))

    @sync_to_async
    def get_current_count(self):
        """عدد الحجوزات الحالية (يمكن تغييره حسب المنطق المطلوب)"""
        from .models import Booking   # 👈 حط الاستيراد هنا فقط
        return Booking.objects.count()
