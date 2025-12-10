from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from .models import Turf, TurfImage
from .serializers import TurfSerializer, TurfImageSerializer
from bookings.models import Slot
from bookings.serializers import SlotSerializer
from datetime import datetime
from django.db import models


# ---------------------------------------------
# ADD TURF (OWNER ONLY) - MULTIPLE IMAGES
# ---------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def add_turf(request):

    user = request.user

    # ADMIN ONLY CHECK
    if not user.is_staff and not user.is_superuser:
        return Response({
            "success": False,
            "message": "Only admin can add turfs"
        }, status=403)

    name = request.data.get("name")
    location = request.data.get("location")
    price_per_hour = request.data.get("price_per_hour")
    description = request.data.get("description", "")

    if not name or not location or not price_per_hour:
        return Response({
            "success": False,
            "message": "name, location and price_per_hour are required"
        }, status=400)

    turf = Turf.objects.create(
    owner=request.user,
    name=name,
    location=location,
    price_per_hour=price_per_hour,
    description=description,
)


    images = request.FILES.getlist("images")
    for img in images:
        TurfImage.objects.create(turf=turf, image=img)

    serializer = TurfSerializer(turf, context={"request": request})

    return Response({
        "success": True,
        "message": "Turf created successfully",
        "turf": serializer.data
    }, status=201)


# ---------------------------------------------
# PUBLIC TURF LIST
# ---------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def turf_list(request):
    turfs = Turf.objects.all().order_by("-created_at")
    serializer = TurfSerializer(turfs, many=True, context={"request": request})
    return Response(serializer.data)


# ---------------------------------------------
# PUBLIC TURF DETAIL
# ---------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def turf_detail(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    serializer = TurfSerializer(turf, context={"request": request})
    return Response(serializer.data)


# ---------------------------------------------
# UPLOAD SINGLE IMAGE TO EXISTING TURF (OWNER ONLY)
# ---------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_turf_image(request, turf_id):

    user = request.user
    turf = get_object_or_404(Turf, id=turf_id)

    # Owner check
    if turf.owner.phone != user.phone:
        return Response({
            "success": False,
            "message": "Not allowed. Only owner can upload images."
        }, status=403)

    img = request.FILES.get("image")

    if not img:
        return Response({
            "success": False,
            "message": "Image not provided"
        }, status=400)

    ti = TurfImage.objects.create(turf=turf, image=img)
    serializer = TurfImageSerializer(ti, context={"request": request})

    return Response({
        "success": True,
        "message": "Image uploaded successfully",
        "image": serializer.data
    }, status=201)

# ---------------------------------------------
# SEARCH TURF (PUBLIC)
# ---------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def turf_search(request):
    query = request.GET.get("q", "")

    if query == "":
        return Response({"success": False, "message": "Query 'q' is required"}, status=400)

    turfs = Turf.objects.filter(
        models.Q(name__icontains=query) |
        models.Q(location__icontains=query) |
        models.Q(description__icontains=query)
    )

    serializer = TurfSerializer(turfs, many=True, context={"request": request})
    return Response({"success": True, "results": serializer.data})

# ---------------------------------------------
# GET SLOTS BY DATE
# ---------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def turf_slots_by_date(request, turf_id):
    date_str = request.GET.get("date")

    if not date_str:
        return Response({"success": False, "message": "date is required (YYYY-MM-DD)"}, status=400)

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return Response({"success": False, "message": "Invalid date format"}, status=400)

    slots = Slot.objects.filter(
        turf_id=turf_id,
        start_time__date=selected_date
    ).order_by("start_time")

    serializer = SlotSerializer(slots, many=True)
    return Response({"success": True, "slots": serializer.data})

# ---------------------------------------------
# EDIT TURF (OWNER ONLY)
# ---------------------------------------------
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_turf(request, turf_id):
    user = request.user
    turf = get_object_or_404(Turf, id=turf_id)

    # Owner check
    if not turf.owner or turf.owner != request.user:
        return Response({"success": False, "message": "Not allowed"}, status=403)

    turf.name = request.data.get("name", turf.name)
    turf.location = request.data.get("location", turf.location)
    turf.price_per_hour = request.data.get("price_per_hour", turf.price_per_hour)
    turf.description = request.data.get("description", turf.description)

    turf.save()

    return Response({"success": True, "message": "Turf updated"})

# ---------------------------------------------
# DELETE TURF IMAGE (OWNER ONLY)
# ---------------------------------------------
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_turf_image(request, image_id):
    img = get_object_or_404(TurfImage, id=image_id)

    # Owner check
    if img.turf.owner.phone != request.user.phone:
        return Response({"success": False, "message": "Not allowed"}, status=403)

    img.delete()

    return Response({"success": True, "message": "Image deleted"})
