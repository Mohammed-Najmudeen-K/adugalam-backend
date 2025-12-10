from rest_framework import serializers
from turfs.models import Turf, TurfImage
from bookings.models import Booking, Slot
from users.models import Player, WalletTransaction
from .models import SiteSetting, CouponCampaign, CouponCode, AdminActionLog


# ------------------------------------------------------
# TURF SERIALIZERS
# ------------------------------------------------------
class TurfImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TurfImage
        fields = ["id", "image", "image_url"]

    def get_image_url(self, obj):
        req = self.context.get("request")
        return req.build_absolute_uri(obj.image.url) if req else None


class TurfAdminSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Turf
        fields = [
            "id", "name", "location", "sport_type",
            "price_per_hour", "description",
            "is_active", "created_at",
            "images"
        ]

    def get_images(self, obj):
        req = self.context.get("request")
        qs = TurfImage.objects.filter(turf=obj)
        return [
            {"id": i.id, "url": req.build_absolute_uri(i.image.url)}
            for i in qs
        ]


class TurfCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turf
        fields = [
            "name", "location", "sport_type",
            "price_per_hour", "description", "is_active"
        ]



# ------------------------------------------------------
# SLOT SERIALIZER (required for admin_list_slots)
# ------------------------------------------------------
class SlotAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ["id", "start_time", "end_time", "price", "is_booked"]


# ------------------------------------------------------
# BOOKING SERIALIZER
# ------------------------------------------------------
class BookingAdminSerializer(serializers.ModelSerializer):
    turf_name = serializers.CharField(source="slot.turf.name", read_only=True)
    player_name = serializers.CharField(source="player.name", read_only=True)

    class Meta:
        model = Booking
        fields = "__all__"


# ------------------------------------------------------
# USER SERIALIZERS
# ------------------------------------------------------
class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = [
            "id", "name", "phone", "email",
            "wallet", "is_active", "city", "created_at"
        ]


class WalletAdjustSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    type = serializers.ChoiceField(choices=[("add", "add"), ("debit", "debit")])
    reason = serializers.CharField(required=False, allow_blank=True)


# ------------------------------------------------------
# SETTINGS SERIALIZER
# ------------------------------------------------------
class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = ["key", "value"]


# ------------------------------------------------------
# COUPONS SERIALIZERS
# ------------------------------------------------------
class CouponCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponCampaign
        fields = "__all__"


class CouponCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponCode
        fields = "__all__"


# ------------------------------------------------------
# ADMIN ACTION LOG
# ------------------------------------------------------
class AdminActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminActionLog
        fields = "__all__"
