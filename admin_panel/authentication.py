from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from admin_panel.models import AdminAccount

class AdminJWTAuthentication(BaseAuthentication):
    """
    Custom authentication for Admin panel:
    Validates token, checks role, and returns AdminAccount instance.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        # No header → not authenticated
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            decoded = AccessToken(token)
        except Exception:
            return None

        # ROLE CHECK
        if decoded.get("role") != "admin":
            return None

        # USER ID CHECK
        user_id = decoded.get("user_id")
        if not user_id:
            return None

        # FETCH ADMIN ACCOUNT
        try:
            admin = AdminAccount.objects.get(id=user_id)
        except AdminAccount.DoesNotExist:
            return None

        return (admin, None)
