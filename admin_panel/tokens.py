# admin_panel/tokens.py
import jwt
from datetime import datetime, timedelta
from django.conf import settings


SECRET = settings.SECRET_KEY
ALGORITHM = "HS256"


# ------------------------------------------------------
# CREATE ACCESS TOKEN
# ------------------------------------------------------
def create_access_token(admin_id, exp_minutes=60 * 24):
    """
    Generates JWT token for AdminAccount.
    Default expiry = 24 hours.
    """
    payload = {
        "admin_id": admin_id,
        "exp": datetime.utcnow() + timedelta(minutes=exp_minutes),
        "iat": datetime.utcnow(),
        "scope": "admin_access"
    }

    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)

    # PyJWT v2 returns bytes → convert to str
    if isinstance(token, bytes):
        token = token.decode()

    return token


# ------------------------------------------------------
# DECODE TOKEN
# ------------------------------------------------------
def decode_access_token(token):
    """
    Validates and decodes token.
    Returns admin_id if token is valid.
    Otherwise returns None.
    """
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])

        # Security check: ensure token is for admin only
        if payload.get("scope") != "admin_access":
            return None

        return payload.get("admin_id")

    except jwt.ExpiredSignatureError:
        # Token expired
        return None

    except jwt.InvalidTokenError:
        # Any other invalid token
        return None
