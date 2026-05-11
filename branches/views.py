import math
from django.db.models import Avg, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Branch
from booking.models import Review  # مهم


class NearbyBranches(APIView):

    def get(self, request):
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')

        if not lat or not lng:
            return Response(
                {"error": "lat and lng are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_lat = float(lat)
        user_lng = float(lng)

        # 🔥 تحسين الأداء
        branches = Branch.objects.select_related("barber", "barber__user").filter(is_active=True)

        # 🔥 نجيب التقييمات مرة واحدة
        reviews_data = Review.objects.values("barber").annotate(
            avg_rating=Avg("rating"),
            total_reviews=Count("id")
        )

        # نحولها لـ dict عشان lookup سريع
        reviews_dict = {
            r["barber"]: {
                "rating": round(r["avg_rating"], 1) if r["avg_rating"] else 0,
                "count": r["total_reviews"]
            }
            for r in reviews_data
        }

        def distance(lat1, lng1, lat2, lng2):
            R = 6371
            dLat = math.radians(lat2 - lat1)
            dLng = math.radians(lng2 - lng1)

            a = (
                math.sin(dLat / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(dLng / 2) ** 2
            )

            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        data = []

        for branch in branches:

            dist = distance(
                user_lat,
                user_lng,
                float(branch.lat),
                float(branch.lng),
            )

            # 🔥 نجيب التقييم
            review_info = reviews_dict.get(branch.barber.id, {
                "rating": 0,
                "count": 0
            })

            data.append({
                "id": branch.id,
                "branch_name": branch.name,
                "lat": branch.lat,
                "lng": branch.lng,
                "distance": round(dist, 2),

                # 👇 معلومات الحلاق
                "barber_id": branch.barber.id,
                "barber_name": branch.barber.user.name,
                "barber_phone": branch.barber.user.phone,
                "barber_email": branch.barber.user.email,
                "barber_image": branch.barber.user.profile_image.url if branch.barber.user.profile_image else None,

                # ⭐ التقييمات
                "rating": review_info["rating"],
                "reviews_count": review_info["count"],
            })

        data.sort(key=lambda x: x["distance"])

        return Response(data[:5])