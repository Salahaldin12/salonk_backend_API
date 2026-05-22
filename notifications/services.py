from firebase_admin import messaging
from .models import Notification
from .models import FCMDevice
from django.utils import timezone


class NotificationService:

    @staticmethod
    def send_notification(
        user,
        title,
        body,
        notification_type="general",
        category="general",
        reference_id=None,
        extra_data=None,
        screen=None
    ):

        # =========================
        # 1. Save Notification in DB
        # =========================
        notification = Notification.objects.create(
            user=user,
            title=title,
            body=body,
            notification_type=notification_type,
            category=category,
            extra_data=extra_data,
            screen=screen
        )

        # =========================
        # 2. Get active sessions
        # =========================
        sessions = FCMDevice.objects.filter(
            user=user,
            is_active=True
        ).exclude(
            fcm_token__isnull=True
        )

        if not sessions.exists():
            print("❌ No active sessions")
            return notification

        # =========================
        # 3. Collect tokens
        # =========================
        tokens = list(set([
            s.fcm_token.strip()
            for s in sessions
            if s.fcm_token and s.fcm_token.strip()
        ]))

        print("🔥 TOKENS:", tokens)

        if not tokens:
            print("❌ No valid tokens")
            return notification

        # =========================
        # 4. Build Message
        # =========================
        try:

            message = messaging.MulticastMessage(

                notification=messaging.Notification(
                    title=title,
                    body=body
                ),

                data={
                    "type": str(notification_type),
                    "category": str(category),
                    "screen": str(screen or ""),
                    "notification_id": str(notification.id),
                },

                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        channel_id="high_importance_channel"
                    )
                ),

                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default"
                        )
                    )
                ),

                tokens=tokens
            )

            # =========================
            # 5. Send
            # =========================
            response = messaging.send_each_for_multicast(message)

            print("✅ Success:", response.success_count)
            print("❌ Failed:", response.failure_count)

            # =========================
            # 6. Remove invalid tokens
            # =========================
            for idx, resp in enumerate(response.responses):

                if not resp.success:

                    error = resp.exception

                    print(f"❌ Token Error: {error}")

                    bad_token = tokens[idx]

                    FCMDevice.objects.filter(
                        fcm_token=bad_token
                    ).update(
                        fcm_token=None
                    )

            # =========================
            # 7. Update DB
            # =========================
            notification.is_push_sent = True
            notification.push_sent_at = timezone.now()

            notification.save()

        except Exception as e:

            print(f"[FCM ERROR]: {e}")

        return notification