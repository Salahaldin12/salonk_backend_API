from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import FCMDevice


class SaveFCMTokenView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        print("========== FCM REQUEST ==========")
        print("USER:", request.user)
        print("AUTH:", request.auth)
        print("DATA:", request.data)

        fcm_token = request.data.get("fcm_token")
        device_type = request.data.get("device_type", "android")

        print("TOKEN:", fcm_token)

        if not fcm_token:

            return Response({
                "error": "fcm_token required"
            }, status=status.HTTP_400_BAD_REQUEST)

        device, created = FCMDevice.objects.update_or_create(

            fcm_token=fcm_token,

            defaults={

                "user": request.user,
                "device_type": device_type,
                "is_active": True,
            }
        )

        print("DEVICE ID:", device.id)
        print("CREATED:", created)

        return Response({

            "message": "FCM token saved successfully",
            "created": created,
            "token": device.fcm_token,
        }, status=status.HTTP_200_OK)