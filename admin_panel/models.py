from django.db import models
from django.conf import settings
from users.models import Player
from django.contrib.auth.hashers import make_password, check_password


# ---------------------------------------------------
# SITE SETTINGS (Key → Value table)
# ---------------------------------------------------
class SiteSetting(models.Model):
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.key


# ---------------------------------------------------
# COUPON CAMPAIGN (Master coupons generator)
# ---------------------------------------------------
class CouponCampaign(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True, db_index=True)

    TYPE_CHOICES = (
        ("amount", "amount"),
        ("percent", "percent"),
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="amount")

    value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    usage_limit = models.IntegerField(default=1)

    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


# ---------------------------------------------------
# INDIVIDUAL COUPON CODES (assigned to users)
# ---------------------------------------------------
class CouponCode(models.Model):
    campaign = models.ForeignKey(
        CouponCampaign,
        on_delete=models.CASCADE,
        related_name="codes"
    )
    code = models.CharField(max_length=100, unique=True, db_index=True)

    assigned_to = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True
    )
    used_by = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="used_coupons"
    )

    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


# ---------------------------------------------------
# ADMIN ACTION LOG – EVERY ADMIN ACTIVITY SAVED HERE
# ---------------------------------------------------
class AdminActionLog(models.Model):
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=200)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        user = self.admin if self.admin else "Unknown Admin"
        return f"{user} → {self.action}"


# ---------------------------------------------------
# ADMIN ACCOUNT (Custom simple admin table)
# ---------------------------------------------------
class AdminAccount(models.Model):
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)   # (optional but needed)

    created_at = models.DateTimeField(auto_now_add=True)

    # Password methods
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name or self.phone
