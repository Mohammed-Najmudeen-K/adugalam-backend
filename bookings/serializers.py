from rest_framework import serializers
from .models import Slot, Booking


# --------------------------------------
# BASIC SLOT SERIALIZER
# --------------------------------------
class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ["id", "turf", "start_time", "end_time", "price", "is_booked"]


# --------------------------------------
# SLOT DETAIL SERIALIZER (used inside booking list)
# --------------------------------------
class SlotDetailSerializer(serializers.ModelSerializer):
    turf_name = serializers.CharField(source="turf.name", read_only=True)
    turf_location = serializers.CharField(source="turf.location", read_only=True)
    turf_price = serializers.DecimalField(source="price", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Slot
        fields = [
            "id",
            "start_time",
            "end_time",
            "turf_name",
            "turf_location",
            "turf_price",
        ]


# --------------------------------------
# SIMPLE BOOKING SERIALIZER
# --------------------------------------
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "player", "slot", "booked_at"]


# --------------------------------------
# DETAILED BOOKING SERIALIZER
# --------------------------------------
class BookingDetailSerializer(serializers.ModelSerializer):

    slot_details = SlotDetailSerializer(source="slot", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "player",
            "slot",
            "slot_details",
            "booked_at",
        ]

class CreateBookingSerializer(serializers.Serializer):
    turf_id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    hours = serializers.DecimalField(max_digits=4, decimal_places=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    advance_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_status = serializers.CharField()

class SlotAvailabilitySerializer(serializers.Serializer):
    turf_id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

class RescheduleBookingSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    new_date = serializers.DateField()
    new_start_time = serializers.TimeField()
    new_end_time = serializers.TimeField()

class AdminSendNotificationSerializer(serializers.Serializer):
    title = serializers.CharField()
    message = serializers.CharField()
    user_id = serializers.IntegerField(required=False)

