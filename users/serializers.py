from rest_framework import serializers
from .models import Player, WalletTransaction, Favourite, Review, Notification, CartItem


# --------------------------------------------------------
# REGISTER SERIALIZER
# --------------------------------------------------------
class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField()
    name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False)


# --------------------------------------------------------
# PLAYER SERIALIZER
# --------------------------------------------------------
class PlayerSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            "id",
            "phone",
            "name",
            "email",
            "wallet",
            "profile_photo_url"
        ]

    def get_profile_photo_url(self, obj):
        request = self.context.get("request")
        if obj.profile_photo and request:
            return request.build_absolute_uri(obj.profile_photo.url)
        return None

# --------------------------------------------------------
# WALLET TRANSACTION
# --------------------------------------------------------
class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = "__all__"


# --------------------------------------------------------
# FAVOURITE SERIALIZER
# --------------------------------------------------------
class FavouriteSerializer(serializers.ModelSerializer):
    turf_name = serializers.CharField(source="turf.name", read_only=True)

    class Meta:
        model = Favourite
        fields = ["id", "turf", "turf_name", "created_at"]


# --------------------------------------------------------
# REVIEW SERIALIZER
# --------------------------------------------------------
class ReviewSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source="player.name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "player", "player_name", "turf", "rating", "comment", "created_at"]


# --------------------------------------------------------
# NOTIFICATION SERIALIZER
# --------------------------------------------------------
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


# --------------------------------------------------------
# CART SERIALIZER
# --------------------------------------------------------
class CartItemSerializer(serializers.ModelSerializer):
    turf_name = serializers.CharField(source="turf.name", read_only=True)
    slot_time = serializers.CharField(source="slot.start_time", read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "turf",
            "turf_name",
            "slot",
            "slot_time",
            "qty",
            "date",
            "price",
            "created_at",
        ]

class AdminSendNotificationSerializer(serializers.Serializer):
    title = serializers.CharField()
    message = serializers.CharField()
    user_id = serializers.IntegerField(required=False)
