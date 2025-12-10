from django.contrib import admin
from .models import (
    SiteSetting,
    CouponCampaign,
    CouponCode,
    AdminActionLog,
    AdminAccount
)


# ----------------------------------------------
# SITE SETTINGS ADMIN
# ----------------------------------------------
@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
    search_fields = ("key",)


# ----------------------------------------------
# COUPON CODE INLINE (for Campaign)
# ----------------------------------------------
class CouponCodeInline(admin.TabularInline):
    model = CouponCode
    extra = 0
    readonly_fields = ("code", "assigned_to", "used_by", "used_at", "created_at")
    can_delete = False


# ----------------------------------------------
# COUPON CAMPAIGN ADMIN
# ----------------------------------------------
@admin.register(CouponCampaign)
class CouponCampaignAdmin(admin.ModelAdmin):
    list_display = (
        "name", "code", "type", "value",
        "usage_limit", "active", "created_at"
    )
    search_fields = ("name", "code")
    list_filter = ("type", "active", "valid_from", "valid_to")
    ordering = ("-created_at",)
    inlines = [CouponCodeInline]


# ----------------------------------------------
# COUPON CODE ADMIN (separate)
# ----------------------------------------------
@admin.register(CouponCode)
class CouponCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code", "campaign", "assigned_to",
        "used_by", "used_at", "created_at"
    )
    search_fields = ("code",)
    list_filter = ("campaign",)
    ordering = ("-created_at",)


# ----------------------------------------------
# ADMIN ACTION LOG ADMIN
# ----------------------------------------------
@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ("admin", "action", "created_at")
    search_fields = ("admin__username", "action", "details")
    ordering = ("-created_at",)
    readonly_fields = ("admin", "action", "details", "created_at")

    def has_add_permission(self, request):
        return False  # prevent manual addition

    def has_change_permission(self, request, obj=None):
        return False  # logs are system-generated


# ----------------------------------------------
# ADMIN ACCOUNT ADMIN
# ----------------------------------------------
@admin.register(AdminAccount)
class AdminAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "is_active", "created_at")
    search_fields = ("name", "phone")
    list_filter = ("is_active",)
    ordering = ("-created_at",)

    readonly_fields = ("password", "created_at")

    fieldsets = (
        ("Admin Details", {
            "fields": ("name", "phone", "is_active")
        }),
        ("Security", {
            "fields": ("password",),
        }),
        ("System Info", {
            "fields": ("created_at",),
        }),
    )
