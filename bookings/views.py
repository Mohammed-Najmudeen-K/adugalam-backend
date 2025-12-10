from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny

from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime

from turfs.models import Turf
from bookings.models import Slot, Booking
from users.models import Player

from .serializers import (
    SlotSerializer,
    BookingSerializer,
    BookingDetailSerializer
)

# ----------------------------------------------------
# CREATE SLOT (ADMIN = OWNER)
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_slot(request, turf_id):
    user = request.user

    # Admin = owner
    if not user.is_admin:
        return Response({"success": False, "message": "Only owners can create slots"}, status=403)

    turf = get_object_or_404(Turf, id=turf_id)

    if turf.owner != user:
        return Response({"success": False, "message": "You do not own this turf"}, status=403)

    start_time = parse_datetime(request.data.get("start_time"))
    end_time = parse_datetime(request.data.get("end_time"))
    price = request.data.get("price")

    if not start_time or not end_time or not price:
        return Response({"success": False, "message": "start_time, end_time, price required"}, status=400)

    slot = Slot.objects.create(
        turf=turf,
        start_time=start_time,
        end_time=end_time,
        price=price
    )

    return Response({"success": True, "message": "Slot created", "slot": SlotSerializer(slot).data})


# ----------------------------------------------------
# GET ALL SLOTS FOR A TURF
# ----------------------------------------------------
@api_view(["GET"])
def turf_slots(request, turf_id):
    slots = Slot.objects.filter(turf_id=turf_id).order_by("start_time")
    return Response({"success": True, "slots": SlotSerializer(slots, many=True).data})


# ----------------------------------------------------
# BOOK SLOT (PLAYER)
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def book_slot(request):
    user = request.user

    if user.is_admin:
        return Response({"success": False, "message": "Admins cannot book slots"}, status=403)

    slot_id = request.data.get("slot_id")
    slot = get_object_or_404(Slot, id=slot_id)

    if slot.is_booked:
        return Response({"success": False, "message": "Slot already booked"}, status=400)

    if user.wallet < slot.price:
        return Response({
            "success": False,
            "message": "Insufficient wallet balance",
            "required": float(slot.price),
            "wallet": float(user.wallet)
        }, status=400)

    # Deduct wallet
    user.wallet -= slot.price
    user.save()

    booking = Booking.objects.create(player=user, slot=slot)

    slot.is_booked = True
    slot.save()

    return Response({
        "success": True,
        "message": "Slot booked",
        "booking": BookingSerializer(booking).data,
        "wallet": float(user.wallet)
    })


# ----------------------------------------------------
# USER BOOKING HISTORY
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_bookings(request):
    user = request.user

    bookings = Booking.objects.filter(player=user).order_by("-booked_at")
    return Response({"success": True, "bookings": BookingSerializer(bookings, many=True).data})


# ----------------------------------------------------
# CANCEL BOOKING
# ----------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):
    user = request.user

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.player != user:
        return Response({"success": False, "message": "This booking does not belong to you"}, status=403)

    slot = booking.slot

    # Refund
    user.wallet += slot.price
    user.save()

    slot.is_booked = False
    slot.save()

    booking.delete()

    return Response({
        "success": True,
        "message": "Booking cancelled and amount refunded",
        "refund": float(slot.price),
        "wallet": float(user.wallet)
    })


# ----------------------------------------------------
# OWNER – ALL BOOKINGS FOR ONE TURF
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_turf_bookings_specific(request, turf_id):
    user = request.user

    if not user.is_admin:
        return Response({"success": False, "message": "Only owners can view bookings"}, status=403)

    turf = get_object_or_404(Turf, id=turf_id)

    if turf.owner != user:
        return Response({"success": False, "message": "You do not own this turf"}, status=403)

    bookings = Booking.objects.filter(slot__turf=turf).order_by("-booked_at")

    return Response({"success": True, "bookings": BookingDetailSerializer(bookings, many=True).data})


# ----------------------------------------------------
# OWNER – ALL BOOKINGS ACROSS ALL TURFS
# ----------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_all_turf_bookings(request):
    user = request.user

    if not user.is_admin:
        return Response({"success": False, "message": "Only owners can view bookings"}, status=403)

    turfs = Turf.objects.filter(owner=user)

    bookings = Booking.objects.filter(slot__turf__in=turfs).order_by("-booked_at")

    return Response({"success": True, "bookings": BookingDetailSerializer(bookings, many=True).data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def booking_create(request):
    from turfs.models import Turf
    from bookings.models import Booking

    data = request.data

    turf_id = data.get("turf_id")
    date = data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    hours = data.get("hours")
    price = data.get("price")
    advance_amount = data.get("advance_amount")
    payment_status = data.get("payment_status")

    # Turf check
    try:
        turf = Turf.objects.get(id=turf_id)
    except Turf.DoesNotExist:
        return Response({"success": False, "message": "Invalid turf"}, status=400)

    # Slot availability check
    exists = Booking.objects.filter(
        turf=turf,
        date=date,
        start_time=start_time,
        end_time=end_time,
        status="CONFIRMED"
    ).exists()

    if exists:
        return Response({"success": False, "message": "Slot not available"}, status=409)

    # Create booking
    booking = Booking.objects.create(
        turf=turf,
        user=request.user,
        date=date,
        start_time=start_time,
        end_time=end_time,
        hours=hours,
        price=price,
        advance_amount=advance_amount,
        payment_status=payment_status,
        status="CONFIRMED"
    )

    return Response({
        "success": True,
        "message": "Booking Created",
        "booking_id": booking.id
    })

@api_view(['POST'])
@permission_classes([AllowAny])   # or IsAuthenticated if needed
def check_slot_availability(request):
    from bookings.models import Booking
    from turfs.models import Turf

    data = request.data

    turf_id = data.get("turf_id")
    date = data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    # Turf check
    try:
        turf = Turf.objects.get(id=turf_id)
    except Turf.DoesNotExist:
        return Response({"success": False, "message": "Invalid turf"}, status=400)

    # Check conflicts
    conflict = Booking.objects.filter(
        turf=turf,
        date=date,
        start_time=start_time,
        end_time=end_time,
        status="CONFIRMED"
    ).first()

    if conflict:
        return Response({
            "success": False,
            "available": False,
            "message": "Slot not available",
            "existing_booking_id": conflict.id,
            "booked_by": conflict.user.name if conflict.user else None
        }, status=200)

    return Response({
        "success": True,
        "available": True,
        "message": "Slot available"
    }, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def booking_reschedule(request):
    from bookings.models import Booking
    from turfs.models import Turf

    data = request.data

    booking_id = data.get("booking_id")
    new_date = data.get("new_date")
    new_start_time = data.get("new_start_time")
    new_end_time = data.get("new_end_time")

    # Booking validation
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        return Response({"success": False, "message": "Invalid booking"}, status=404)

    # Check turf
    turf = booking.turf

    # Check slot availability
    conflict = Booking.objects.filter(
        turf=turf,
        date=new_date,
        start_time=new_start_time,
        end_time=new_end_time,
        status="CONFIRMED"
    ).exclude(id=booking_id).first()

    if conflict:
        return Response({
            "success": False,
            "message": "Selected slot is already booked",
            "conflict_booking_id": conflict.id
        }, status=409)

    # Update booking
    booking.date = new_date
    booking.start_time = new_start_time
    booking.end_time = new_end_time
    booking.save()

    return Response({
        "success": True,
        "message": "Booking rescheduled successfully",
        "booking_id": booking.id,
        "new_date": new_date,
        "new_start_time": new_start_time,
        "new_end_time": new_end_time
    })
