from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Allows access only if the authenticated user is an admin.
    """

    def has_permission(self, request, view):
        # request.user is set by AdminJWTAuthentication
        return bool(
            request.user
            and hasattr(request.user, "id")
        )
