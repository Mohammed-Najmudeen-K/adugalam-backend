from django.urls import path
from .views import (
    # AUTH
    register_user,
    send_otp,
    verify_otp,
    login_password,
    refresh_token,

    # PROFILE
    user_profile,
    update_profile,
    upload_profile_photo,

    # WALLET
    add_wallet_balance,
    wallet_balance,
    wallet_history,

    # FAVOURITES
    add_favourite,
    remove_favourite,
    list_favourites,

    # REVIEWS
    add_review,
    turf_reviews,
    delete_review,

    # NOTIFICATIONS
    my_notifications,
    mark_notification_read,
    mark_all_read,

    # CART
    cart_add,
    cart_remove,
    cart_list,
    cart_clear,
)

urlpatterns = [
    # ------------------
    # AUTH
    # ------------------
    path("auth/register/", register_user),
    path("auth/otp/send/", send_otp),
    path("auth/otp/verify/", verify_otp),
    path("auth/login-password/", login_password),
    path("auth/refresh/", refresh_token),

    # ------------------
    # PROFILE
    # ------------------
    path("user/profile/", user_profile),
    path("user/profile/update/", update_profile),
    path("user/profile/photo/", upload_profile_photo),

    # ------------------
    # WALLET
    # ------------------
    path("user/wallet/add/", add_wallet_balance),
    path("user/wallet/", wallet_balance),
    path("user/wallet/history/", wallet_history),

    # ------------------
    # FAVOURITES
    # ------------------
    path("user/favourites/add/", add_favourite),
    path("user/favourites/remove/", remove_favourite),
    path("user/favourites/", list_favourites),

    # ------------------
    # REVIEWS
    # ------------------
    path("user/review/add/", add_review),
    path("user/review/turf/<int:turf_id>/", turf_reviews),
    path("user/review/delete/<int:review_id>/", delete_review),

    # ------------------
    # NOTIFICATIONS
    # ------------------
    path("user/notifications/", my_notifications),
    path("user/notifications/read/", mark_notification_read),
    path("user/notifications/read-all/", mark_all_read),

    # ------------------
    # CART
    # ------------------
    path("user/cart/add/", cart_add),
    path("user/cart/remove/", cart_remove),
    path("user/cart/", cart_list),
    path("user/cart/clear/", cart_clear),
]
