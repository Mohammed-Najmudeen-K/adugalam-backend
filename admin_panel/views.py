"""
admin_panel/views.py

Complete, production-ready rewrite for admin panel APIs (auth, dashboard,
turfs, slots, bookings, users, coupons, settings, logs, reports).

Notes:
- Login is merged: if phone exists in AdminAccount -> returns admin JWT tokens;
  else if phone exists in Player -> returns player JWT tokens.
- Tokens are generated via SimpleJWT (RefreshToken.for_user(...)) so they are
  compatible with DRF JWTAuthentication and AccessToken decoding.
- Admin permission (IsAdminUserCustom) should decode SimpleJWT AccessToken and
  then map `user_id` to AdminAccount. Keep your updated permissions.py from
  previous step (which uses AccessToken(...) and AdminAccount lookup).
"""
from admin_panel.authentication import AdminJWTAuthentication
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes, authentication_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.exceptions import ObjectDoesNotExist
from admin_panel.permissions import IsAdmin
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import TurfAdminSerializer

# models
from bookings.models import Booking, Slot
from turfs.models import Turf, TurfImage
from users.models import Player, WalletTransaction
from .models import (
    SiteSetting, CouponCampaign, CouponCode, AdminActionLog,
    AdminAccount
)

# serializers (assumed to exist)
from .serializers import (
    TurfAdminSerializer, TurfCreateSerializer, TurfImageSerializer,
    BookingAdminSerializer, UserAdminSerializer, WalletAdjustSerializer,
    SiteSettingSerializer, CouponCampaignSerializer, CouponCodeSerializer,
    AdminActionLogSerializer, SlotAdminSerializer
)

# permissions



# ------------------------------
# Helper
# ------------------------------
def log_action(admin, action, details=""):
    try:
        AdminActionLog.objects.create(admin=admin, action=action, details=details)
    except Exception:
        # avoid breaking API if logging fails
        pass


# ------------------------------
# MERGED Auth (Admin OR Player)
# ------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def admin_login(request):
    phone = request.data.get("phone")
    password = request.data.get("password")

    if not phone or not password:
        return Response({"success": False, "message": "Phone & password required"}, status=400)

    # 1️⃣ Check Admin first
    admin = AdminAccount.objects.filter(phone=phone).first()
    if admin:
        if not admin.check_password(password):
            return Response({"success": False, "message": "Invalid password"}, status=401)

        refresh = RefreshToken.for_user(admin)
        refresh["role"] = "admin"               # Add role to refresh token
        access = refresh.access_token
        access["role"] = "admin"                # Add role to access token (VERY IMPORTANT)

        return Response({
            "success": True,
            "role": "admin",
            "access": str(access),
            "refresh": str(refresh),
        })

    # 2️⃣ Check Player next
    player = Player.objects.filter(phone=phone).first()
    if player:
        if not player.check_password(password):
            return Response({"success": False, "message": "Invalid password"}, status=401)

        refresh = RefreshToken.for_user(player)
        access = refresh.access_token
        access["role"] = "player"

        return Response({
            "success": True,
            "role": "player",
            "access": str(access),
            "refresh": str(refresh),
        })

    return Response({"success": False, "message": "Account not found"}, status=404)


#CREATE ADMIN
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def create_admin(request):
    phone = request.data.get("phone")
    password = request.data.get("password")
    name = request.data.get("name")

    admin = AdminAccount(phone=phone, name=name)
    admin.set_password(password)
    admin.save()

    return Response({"success": True, "message": "Admin created successfully"})

@api_view(["GET", "PUT"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_user_detail(request, user_id):
    user = get_object_or_404(Player, id=user_id)

    if request.method == "GET":
        return Response({
            "success": True,
            "user": UserAdminSerializer(user).data
        })

    data = request.data

    if "name" in data:
        user.name = data["name"]

    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    if "city" in data:
        user.city = data["city"]     # ✅ Now allowed

    user.save()
    return Response({"success": True, "message": "User updated"})


# ------------------------------
# Dashboard summary
# ------------------------------
@api_view(["GET"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def dashboard_summary(request):
    users_count = Player.objects.count()
    turfs_count = Turf.objects.count()

    today = timezone.now().date()
    bookings_today = Booking.objects.filter(booked_at__date=today).count()

    from django.db.models import Sum
    revenue_today = Booking.objects.filter(booked_at__date=today).aggregate(total=Sum("slot__price"))["total"] or 0
    month_start = timezone.now().replace(day=1)
    revenue_month = Booking.objects.filter(booked_at__gte=month_start).aggregate(total=Sum("slot__price"))["total"] or 0

    data = {
        "users_count": users_count,
        "turfs_count": turfs_count,
        "bookings_today": bookings_today,
        "revenue_today": float(revenue_today),
        "revenue_month": float(revenue_month),
    }
    return Response({"success": True, "data": data})


# ------------------------------
# Turfs: list/create/detail/edit/delete + image upload/delete + toggle active
# ------------------------------
# ADD TURF (SIMPLE VERSION USED IN YOUR UI)
@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
@parser_classes([MultiPartParser, FormParser, JSONParser])   # <— IMPORTANT
def add_turf(request):
    try:
        data = request.data

        required_fields = ["name", "location", "price_per_hour", "sport_type"]
        for field in required_fields:
            if not data.get(field):
                return Response({
                    "success": False,
                    "message": f"{field} is required"
                }, status=400)

        turf = Turf.objects.create(
            name=data["name"],
            location=data["location"],
            sport_type=data["sport_type"],
            price_per_hour=data["price_per_hour"],
            description=data.get("description", "")
        )

        # Handle images if form-data used
        for key in ["image1", "image2", "image3"]:
            file = request.FILES.get(key)
            if file:
                TurfImage.objects.create(turf=turf, image=file)

        return Response({
            "success": True,
            "message": "Turf added successfully",
            "data": TurfAdminSerializer(turf, context={"request": request}).data
        }, status=201)

    except Exception as e:
        return Response({
            "success": False,
            "message": "Something went wrong",
            "error": str(e)
        }, status=500)



# LIST TURFS
@api_view(["GET"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_list_turfs(request):
    turfs = Turf.objects.all().order_by("-id")
    serializer = TurfAdminSerializer(turfs, many=True, context={"request": request})
    return Response({"success": True, "turfs": serializer.data})


# GET / UPDATE / DELETE TURF
@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_turf_detail(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)

    if request.method == "GET":
        return Response({
            "success": True,
            "turf": TurfAdminSerializer(turf, context={"request": request}).data
        })

    if request.method == "PUT":
        serializer = TurfCreateSerializer(turf, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_action(request.user, "edit_turf", f"turf_id={turf.id}")
            return Response({"success": True, "message": "Turf updated"})
        return Response({"success": False, "errors": serializer.errors}, status=400)

    # DELETE (soft delete)
    turf.is_active = False
    turf.save()
    log_action(request.user, "soft_delete_turf", f"turf_id={turf.id}")
    return Response({"success": True, "message": "Turf deactivated"})


# UPLOAD IMAGE TO A TURF
@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
@parser_classes([MultiPartParser, FormParser])
def admin_upload_turf_image(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    img = request.FILES.get("image")
    if not img:
        return Response({"success": False, "message": "Image required"}, status=400)

    ti = TurfImage.objects.create(turf=turf, image=img)

    log_action(request.user, "upload_turf_image", f"turf_id={turf.id}, image_id={ti.id}")

    return Response({
        "success": True,
        "image": TurfImageSerializer(ti, context={"request": request}).data
    }, status=201)


# DELETE IMAGE
@api_view(["DELETE"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_delete_turf_image(request, image_id):
    img = get_object_or_404(TurfImage, id=image_id)
    img.delete()

    log_action(request.user, "delete_turf_image", f"image_id={image_id}")

    return Response({"success": True, "message": "Image deleted"})


# TOGGLE TURF ACTIVE STATUS
@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_toggle_turf(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    turf.is_active = not turf.is_active
    turf.save()

    log_action(
        request.user,
        "toggle_turf_active",
        f"turf_id={turf.id}, active={turf.is_active}"
    )

    return Response({"success": True, "active": turf.is_active})

# ------------------------------
# Slots: create (generate), list, delete
# ------------------------------
@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_generate_slots(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    start = request.data.get("start", "06:00")
    end = request.data.get("end", "23:00")
    try:
        duration = int(request.data.get("duration", 60))
    except Exception:
        return Response({"success": False, "message": "Invalid duration"}, status=400)
    try:
        price = Decimal(request.data.get("price", "500"))
    except Exception:
        return Response({"success": False, "message": "Invalid price"}, status=400)

    try:
        start_dt = datetime.strptime(start, "%H:%M")
        end_dt = datetime.strptime(end, "%H:%M")
    except Exception:
        return Response({"success": False, "message": "Invalid time format (HH:MM)"}, status=400)

    created = []
    while start_dt < end_dt:
        next_dt = start_dt + timedelta(minutes=duration)
        slot = Slot.objects.create(
            turf=turf,
            start_time=datetime.combine(timezone.now().date(), start_dt.time()),
            end_time=datetime.combine(timezone.now().date(), next_dt.time()),
            price=price
        )
        created.append(slot.id)
        start_dt = next_dt

    log_action(request.user, "generate_slots", f"turf_id={turf.id}, count={len(created)}")
    return Response({"success": True, "slots_created": created})


@api_view(["GET"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_list_slots(request, turf_id):
    slots = Slot.objects.filter(turf_id=turf_id).order_by("start_time")
    serializer = SlotAdminSerializer(slots, many=True, context={"request": request})
    return Response({"success": True, "slots": serializer.data})


@api_view(["DELETE"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_delete_slot(request, slot_id):
    slot = get_object_or_404(Slot, id=slot_id)
    slot.delete()
    log_action(request.user, "delete_slot", f"slot_id={slot_id}")
    return Response({"success": True, "message": "Slot deleted"})


# ------------------------------
# Bookings: list, detail, cancel (with refund), update status, reschedule
# ------------------------------
@api_view(["GET"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_bookings(request):
    qs = Booking.objects.all().order_by("-booked_at")
    turf_id = request.GET.get("turf")
    user_id = request.GET.get("user")
    status_q = request.GET.get("status")
    if turf_id:
        qs = qs.filter(slot__turf_id=turf_id)
    if user_id:
        qs = qs.filter(player_id=user_id)
    if status_q:
        qs = qs.filter(payment_status__iexact=status_q)
    serializer = BookingAdminSerializer(qs, many=True)
    return Response({"success": True, "results": serializer.data})

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_create_booking(request):
    slot_id = request.data.get("slot_id")
    player_id = request.data.get("player_id")

    if not slot_id or not player_id:
        return Response({"success": False, "message": "slot_id & player_id required"}, status=400)

    slot = get_object_or_404(Slot, id=slot_id)

    if slot.is_booked:
        return Response({"success": False, "message": "Slot already booked"}, status=400)

    player = get_object_or_404(Player, id=player_id)

    # Mark slot booked
    slot.is_booked = True
    slot.save()

    booking = Booking.objects.create(
        player=player,
        slot=slot,
    )

    log_action(request.user, "admin_create_booking", f"booking_id={booking.id}")

    return Response({
        "success": True,
        "message": "Booking created successfully",
        "booking_id": booking.id
    }, status=201)



@api_view(["GET"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    serializer = BookingAdminSerializer(booking)
    return Response({"success": True, "booking": serializer.data})


@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    reason = request.data.get("reason", "Cancelled by admin")
    refund_amount = request.data.get("refund_amount")
    try:
        refund_amount = Decimal(refund_amount) if refund_amount is not None else booking.advance_amount or Decimal("0")
    except Exception:
        return Response({"success": False, "message": "Invalid refund amount"}, status=400)

    with transaction.atomic():
        booking.is_cancelled = True
        booking.cancel_reason = reason
        booking.refunded_amount = refund_amount
        booking.payment_status = "refunded"
        booking.save()

        slot = booking.slot
        slot.is_booked = False
        slot.save()

        if refund_amount > 0:
            player = booking.player
            player.wallet += refund_amount
            player.save()
            WalletTransaction.objects.create(player=player, amount=refund_amount, type="refund")

        log_action(request.user, "admin_cancel_booking", f"booking_id={booking.id}, refund={refund_amount}")

    return Response({"success": True, "message": "Booking cancelled & refunded", "refund": float(refund_amount)})


@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_update_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    status_val = request.data.get("status")
    allowed = ["pending", "confirmed", "completed", "cancelled", "refunded"]
    if status_val not in allowed:
        return Response({"success": False, "message": "Invalid status"}, status=400)
    booking.payment_status = status_val
    booking.save()
    log_action(request.user, "update_booking_status", f"booking_id={booking.id}, status={status_val}")
    return Response({"success": True, "message": "Status updated"})


@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_reschedule_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    new_slot_id = request.data.get("new_slot_id")
    new_slot = get_object_or_404(Slot, id=new_slot_id)

    if new_slot.is_booked:
        return Response({"success": False, "message": "Slot already booked"}, status=400)

    with transaction.atomic():
        old_slot = booking.slot
        old_slot.is_booked = False
        old_slot.save()

        new_slot.is_booked = True
        new_slot.save()

        booking.slot = new_slot
        booking.save()

        log_action(request.user, "reschedule_booking", f"booking_id={booking.id}, new_slot={new_slot.id}")

    return Response({"success": True, "message": "Booking rescheduled"})


# ------------------------------
# Users management: list, detail, update, wallet adjust
# ------------------------------
@api_view(["GET"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_users(request):
    qs = Player.objects.all().order_by("-created_at")
    q = request.GET.get("q")
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(phone__icontains=q)
    serializer = UserAdminSerializer(qs, many=True)
    return Response({"success": True, "results": serializer.data})


@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_wallet_adjust(request, user_id):
    user = get_object_or_404(Player, id=user_id)
    serializer = WalletAdjustSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"success": False, "errors": serializer.errors}, status=400)
    data = serializer.validated_data
    try:
        amt = Decimal(data["amount"])
    except Exception:
        return Response({"success": False, "message": "Invalid amount"}, status=400)

    if data["type"] == "add":
        user.wallet += amt
        ttype = "add"
    else:
        user.wallet -= amt
        ttype = "debit"
    user.save()
    WalletTransaction.objects.create(player=user, amount=amt, type=ttype)
    log_action(request.user, "wallet_adjust", f"user_id={user.id}, type={ttype}, amount={amt}")
    return Response({"success": True, "wallet": float(user.wallet)})


# ------------------------------
# Settings (get/update)
# ------------------------------
@api_view(["GET", "PUT"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_setting(request, key):
    obj, created = SiteSetting.objects.get_or_create(key=key)
    if request.method == "GET":
        return Response({"success": True, "setting": SiteSettingSerializer(obj).data})
    obj.value = request.data.get("value", obj.value)
    obj.save()
    log_action(request.user, "update_setting", f"key={key}")
    return Response({"success": True, "message": "Setting updated"})


# ------------------------------
# Coupons: campaign create/list, generate codes, list codes
# ------------------------------
@api_view(["GET", "POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_coupons(request):
    if request.method == "GET":
        qs = CouponCampaign.objects.all().order_by("-created_at")
        return Response({"success": True, "results": CouponCampaignSerializer(qs, many=True).data})
    serializer = CouponCampaignSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"success": False, "errors": serializer.errors}, status=400)
    campaign = serializer.save()
    log_action(request.user, "create_coupon_campaign", f"campaign_id={campaign.id}")
    return Response({"success": True, "campaign": CouponCampaignSerializer(campaign).data}, status=201)


@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_generate_codes(request):
    campaign_id = request.data.get("campaign_id")
    count = int(request.data.get("count", 10))
    campaign = get_object_or_404(CouponCampaign, id=campaign_id)
    created_codes = []
    for _ in range(count):
        code = f"{campaign.code}-{uuid.uuid4().hex[:6].upper()}"
        cc = CouponCode.objects.create(campaign=campaign, code=code)
        created_codes.append(cc.code)
    log_action(request.user, "generate_coupon_codes", f"campaign_id={campaign.id},count={count}")
    return Response({"success": True, "codes": created_codes})


@api_view(["GET"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_coupon_codes(request, campaign_id):
    campaign = get_object_or_404(CouponCampaign, id=campaign_id)
    qs = campaign.codes.all()
    return Response({"success": True, "results": CouponCodeSerializer(qs, many=True).data})


# ------------------------------
# Admin logs
# ------------------------------
@api_view(["GET"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_logs(request):
    qs = AdminActionLog.objects.all().order_by("-created_at")[:200]
    return Response({
        "success": True,
        "results": AdminActionLogSerializer(qs, many=True).data
    })

# ------------------------------
# Sales report
# ------------------------------
from django.db.models import Sum  # placed here to avoid import-order issues earlier

@api_view(["GET"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_sales_report(request):
    today = timezone.now().date()
    month_start = timezone.now().replace(day=1)

    daily = Booking.objects.filter(booked_at__date=today).aggregate(revenue=Sum("slot__price"))
    monthly = Booking.objects.filter(booked_at__gte=month_start).aggregate(revenue=Sum("slot__price"))

    return Response({
        "success": True,
        "daily_revenue": float(daily["revenue"] or 0),
        "monthly_revenue": float(monthly["revenue"] or 0),
    })

@api_view(["POST"])
@authentication_classes([AdminJWTAuthentication])
@permission_classes([IsAdmin])
def admin_create_booking(request):
    slot_id = request.data.get("slot_id")
    player_id = request.data.get("player_id")
    advance_amount = request.data.get("advance_amount", 0)
    payment_status = request.data.get("payment_status", "pending")

    if not slot_id or not player_id:
        return Response({"success": False, "message": "slot_id and player_id required"}, status=400)

    slot = get_object_or_404(Slot, id=slot_id)
    if slot.is_booked:
        return Response({"success": False, "message": "Slot already booked"}, status=400)

    player = get_object_or_404(Player, id=player_id)

    # Create booking
    booking = Booking.objects.create(
        slot=slot,
        player=player,
        payment_status=payment_status,
        advance_amount=advance_amount,
    )

    # Mark slot booked
    slot.is_booked = True
    slot.save()

    log_action(request.user, "admin_create_booking", f"booking_id={booking.id}")

    return Response({
        "success": True,
        "message": "Booking created successfully",
        "booking": BookingAdminSerializer(booking).data
    }, status=201)

