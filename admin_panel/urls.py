from django.urls import path
from . import views

urlpatterns = [

    # ------------------------------------------------------
    # ADMIN AUTH
    # ------------------------------------------------------
    path("auth/create/", views.create_admin),
    path("auth/login/", views.admin_login),
    path("users/<int:user_id>/", views.admin_user_detail),


    # ------------------------------------------------------
    # DASHBOARD
    # ------------------------------------------------------
    path("dashboard/", views.dashboard_summary),

    # ------------------------------------------------------
    # TURFS
    # ------------------------------------------------------
    # ---------------------
    # ADMIN TURF MANAGEMENT
    # ---------------------

    # Add new turf
    path("turf/add/", views.add_turf, name="admin_add_turf"),

    # List all turfs
    path("turfs/", views.admin_list_turfs, name="admin_list_turfs"),

    # Get / Update / Delete (soft delete)
    path("turf/<int:turf_id>/", views.admin_turf_detail, name="admin_turf_detail"),

    # Upload turf images
    path("turf/<int:turf_id>/upload-image/", views.admin_upload_turf_image, name="admin_upload_turf_image"),

    # Delete a turf image
    path("turf/image/<int:image_id>/delete/", views.admin_delete_turf_image, name="admin_delete_turf_image"),

    # Activate / Deactivate turf
    path("turf/<int:turf_id>/toggle/", views.admin_toggle_turf, name="admin_toggle_turf"),
    # ------------------------------------------------------
    # SLOTS
    # ------------------------------------------------------
    # ---------------- SLOTS ----------------
    path("slots/generate/<int:turf_id>/", views.admin_generate_slots),
    path("slots/<int:turf_id>/", views.admin_list_slots),
    path("slot/<int:slot_id>/delete/", views.admin_delete_slot),

    # ------------------------------------------------------
    # BOOKINGS
    # ------------------------------------------------------
    path("bookings/", views.admin_bookings),
    path("bookings/<int:booking_id>/", views.admin_booking_detail),
    path("bookings/<int:booking_id>/cancel/", views.admin_cancel_booking),
    path("bookings/create/", views.admin_create_booking),



    # Booking extra operations
    path("bookings/<int:booking_id>/status/", views.admin_update_booking_status),
    path("bookings/<int:booking_id>/reschedule/", views.admin_reschedule_booking),

    # ------------------------------------------------------
    # USERS
    # ------------------------------------------------------
    path("users/", views.admin_users),
    path("users/<int:user_id>/", views.admin_user_detail),
    path("users/<int:user_id>/wallet/", views.admin_wallet_adjust),

    # ------------------------------------------------------
    # SETTINGS
    # ------------------------------------------------------
    path("settings/<str:key>/", views.admin_setting),

    # ------------------------------------------------------
    # COUPONS
    # ------------------------------------------------------
    path("coupons/", views.admin_coupons),                               # GET, POST
    path("coupons/generate/", views.admin_generate_codes),
    path("coupons/<int:campaign_id>/codes/", views.admin_coupon_codes),

    # ------------------------------------------------------
    # LOGS
    # ------------------------------------------------------
    path("logs/", views.admin_logs),

    # ------------------------------------------------------
    # REPORTS
    # ------------------------------------------------------
    path("reports/sales/", views.admin_sales_report),
]
