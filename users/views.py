from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from decimal import Decimal
import random

from .models import Player, OTP, WalletTransaction
from .serializers import PlayerSerializer, RegisterSerializer
from .models import Favourite
from .models import Review
from .models import Notification
from .models import CartItem





# ---------------------------------------------------
# REGISTER USER
# ---------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    s = RegisterSerializer(data=request.data)
    if not s.is_valid():
        return Response({"success": False, "errors": s.errors}, status=400)

    data = s.validated_data
    phone = data["phone"]

    user, created = Player.objects.get_or_create(phone=phone)
    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)

    if data.get("password"):
        user.set_password(data["password"])

    user.save()

    return Response({"success": True, "message": "Registered", "user_id": user.id})


# ---------------------------------------------------
# LOGIN (OTP / PASSWORD) → ONLY FOR PLAYERS
# ---------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def login_password(request):
    phone = request.data.get("phone")
    otp = request.data.get("otp")
    password = request.data.get("password")

    if otp:
        try:
            otp_obj = OTP.objects.filter(phone=phone).latest("created_at")
        except OTP.DoesNotExist:
            return Response({"success": False, "message": "OTP not found"}, status=400)

        if otp_obj.otp != str(otp):
            return Response({"success": False, "message": "Invalid OTP"}, status=400)

        user, _ = Player.objects.get_or_create(phone=phone)

    elif password:
        try:
            user = Player.objects.get(phone=phone)
        except Player.DoesNotExist:
            return Response({"success": False, "message": "User not found"}, status=404)

        if not user.check_password(password):
            return Response({"success": False, "message": "Invalid credentials"}, status=400)

    else:
        return Response({"success": False, "message": "Provide otp or password"}, status=400)

    refresh = RefreshToken.for_user(user)
    return Response({
        "success": True,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": PlayerSerializer(user, context={"request": request}).data
    })


# ---------------------------------------------------
# SEND OTP
# ---------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def send_otp(request):
    phone = request.data.get("phone")
    if not phone:
        return Response({"success": False, "message": "Phone number required"}, status=400)

    otp = random.randint(1000, 9999)
    OTP.objects.create(phone=phone, otp=str(otp))

    return Response({"success": True, "otp": str(otp)})


# ---------------------------------------------------
# VERIFY OTP
# ---------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = request.data.get("phone")
    otp = request.data.get("otp")

    try:
        otp_obj = OTP.objects.filter(phone=phone).latest("created_at")
    except OTP.DoesNotExist:
        return Response({"success": False, "message": "OTP not found"}, status=400)

    if otp_obj.otp != str(otp):
        return Response({"success": False, "message": "Invalid OTP"}, status=400)

    user, _ = Player.objects.get_or_create(phone=phone)
    refresh = RefreshToken.for_user(user)

    return Response({
        "success": True,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": PlayerSerializer(user, context={"request": request}).data
    })


# ---------------------------------------------------
# REFRESH TOKEN
# ---------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    token = request.data.get("refresh")

    if not token:
        return Response({"success": False, "message": "refresh token required"}, status=400)

    try:
        refresh = RefreshToken(token)
        new_access = refresh.access_token
    except Exception:
        return Response({"success": False, "message": "Invalid refresh token"}, status=400)

    return Response({"success": True, "access": str(new_access)})


# ---------------------------------------------------
# USER PROFILE
# ---------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    return Response(PlayerSerializer(user, context={"request": request}).data)


# ---------------------------------------------------
# UPLOAD PROFILE PHOTO
# ---------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_profile_photo(request):
    user = request.user
    img = request.FILES.get("photo")

    if not img:
        return Response({"success": False, "message": "No image provided"}, status=400)

    user.profile_photo = img
    user.save()

    return Response({
        "success": True,
        "photo_url": request.build_absolute_uri(user.profile_photo.url)
    })


# ---------------------------------------------------
# WALLET: ADD BALANCE
# ---------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_wallet_balance(request):
    user = request.user

    try:
        amount = Decimal(request.data.get("amount", 0))
    except:
        return Response({"success": False, "message": "Invalid amount"}, status=400)

    if amount <= 0:
        return Response({"success": False, "message": "Amount must be greater than 0"}, status=400)

    user.wallet += amount
    user.save()

    WalletTransaction.objects.create(
        player=user,
        amount=amount,
        type="add"
    )

    return Response({
        "success": True,
        "message": "Wallet updated successfully",
        "wallet": float(user.wallet)
    })


# ---------------------------------------------------
# WALLET BALANCE
# ---------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wallet_balance(request):
    user = request.user
    return Response({"wallet": float(user.wallet)})


# ---------------------------------------------------
# WALLET HISTORY
# ---------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wallet_history(request):
    user = request.user

    history = WalletTransaction.objects.filter(player=user).order_by("-created_at")

    data = [
        {
            "amount": float(t.amount),
            "type": t.type,
            "created_at": t.created_at
        }
        for t in history
    ]

    return Response({"history": data})

#UPDATE PROFILE
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user

    user.name = request.data.get("name", user.name)
    user.email = request.data.get("email", user.email)
    user.save()

    return Response({
        "success": True,
        "message": "Profile updated",
        "user": PlayerSerializer(user, context={"request": request}).data
    })

#FAVOURITES

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_favourite(request):
    turf_id = request.data.get("turf_id")

    if not turf_id:
        return Response({"success": False, "message": "turf_id required"}, status=400)

    Favourite.objects.get_or_create(player=request.user, turf_id=turf_id)

    return Response({"success": True, "message": "Added to favourites"})

#REMOVE Favourite
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remove_favourite(request):
    turf_id = request.data.get("turf_id")

    Favourite.objects.filter(player=request.user, turf_id=turf_id).delete()

    return Response({"success": True, "message": "Removed from favourites"})

#GET MY FAVOURITES
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_favourites(request):
    favs = Favourite.objects.filter(player=request.user)

    data = [{"turf_id": f.turf_id} for f in favs]

    return Response({"success": True, "favourites": data})

#REVIEWS
#ADD Review
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_review(request):
    turf_id = request.data.get("turf_id")
    rating = request.data.get("rating")
    title = request.data.get("title", "")
    body = request.data.get("body", "")

    if not turf_id or not rating:
        return Response({"success": False, "message": "turf_id & rating required"}, status=400)

    Review.objects.create(
        player=request.user,
        turf_id=turf_id,
        rating=rating,
        title=title,
        body=body
    )

    return Response({"success": True, "message": "Review added"})

#GET Reviews for Turf
@api_view(["GET"])
@permission_classes([AllowAny])
def turf_reviews(request, turf_id):
    reviews = Review.objects.filter(turf_id=turf_id).order_by("-created_at")

    data = [{
        "player": r.player.name,
        "rating": r.rating,
        "title": r.title,
        "body": r.body,
        "created_at": r.created_at
    } for r in reviews]

    return Response({"success": True, "reviews": data})

#DELETE Review
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_review(request, review_id):
    rev = get_object_or_404(Review, id=review_id, player=request.user)
    rev.delete()

    return Response({"success": True, "message": "Review deleted"})


#NOTIFICATIONS
#LIST My Notifications
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_notifications(request):
    notes = Notification.objects.filter(player=request.user).order_by("-created_at")

    data = [{
        "id": n.id,
        "title": n.title,
        "body": n.body,
        "is_read": n.is_read,
        "created_at": n.created_at
    } for n in notes]

    return Response({"success": True, "notifications": data})

#Mark Notification as Read
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request):
    note_id = request.data.get("notification_id")

    n = get_object_or_404(Notification, id=note_id, player=request.user)
    n.is_read = True
    n.save()

    return Response({"success": True, "message": "Marked read"})

#Mark ALL Read
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    Notification.objects.filter(player=request.user, is_read=False).update(is_read=True)
    return Response({"success": True, "message": "All notifications marked read"})


#CART APIs
#ADD to Cart
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cart_add(request):
    turf_id = request.data.get("turf_id")
    slot_id = request.data.get("slot_id")

    if not turf_id or not slot_id:
        return Response({"success": False, "message": "turf_id & slot_id required"}, status=400)

    item, created = CartItem.objects.get_or_create(
        player=request.user,
        turf_id=turf_id,
        slot_id=slot_id,
        defaults={"qty": 1}
    )

    if not created:
        item.qty += 1
        item.save()

    return Response({"success": True, "message": "Added to cart"})

#REMOVE Cart Item
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cart_remove(request):
    item_id = request.data.get("item_id")

    CartItem.objects.filter(id=item_id, player=request.user).delete()

    return Response({"success": True, "message": "Removed from cart"})

#GET Cart Items
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cart_list(request):
    items = CartItem.objects.filter(player=request.user)

    data = [{
        "id": i.id,
        "turf_id": i.turf_id,
        "slot_id": i.slot_id,
        "qty": i.qty,
        "date": i.date,
        "price": float(i.price)
    } for i in items]

    return Response({"success": True, "cart": data})


#CLEAR Cart
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def cart_clear(request):
    CartItem.objects.filter(player=request.user).delete()
    return Response({"success": True, "message": "Cart cleared"})

