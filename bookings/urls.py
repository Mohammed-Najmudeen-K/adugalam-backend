from django.urls import path
from .views import (
    create_slot,
    turf_slots,
    book_slot,
    user_bookings,
    cancel_booking,
    owner_turf_bookings_specific,
    owner_all_turf_bookings,
    booking_create,
    check_slot_availability,
    booking_reschedule,
)

urlpatterns = [

    # OWNER - create slot
    path("turf/<int:turf_id>/slot/create/", create_slot),

    # PUBLIC - get slots
    path("turf/<int:turf_id>/slots/", turf_slots),

    # PLAYER - book slot
    path("book/", book_slot),

    # PLAYER - booking history
    path("my-bookings/", user_bookings),

    # PLAYER - cancel booking
    path("cancel/<int:booking_id>/", cancel_booking),

    # OWNER - bookings for 1 turf
    path("owner/turf/<int:turf_id>/bookings/", owner_turf_bookings_specific),

    # OWNER - bookings for all turfs
    path("owner/bookings/", owner_all_turf_bookings),
    path("booking/create/", booking_create),
    path("booking/check-availability/", check_slot_availability),
    path("booking/reschedule/", booking_reschedule),



]
