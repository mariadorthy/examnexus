import os
from datetime import datetime, timedelta, timezone

import jwt
from flask import request


JWT_ALGORITHM = "HS256"


def get_jwt_secret():
    secret = os.getenv("JWT_SECRET_KEY")

    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured."
        )

    return secret


def create_access_token(user_id, role):
    now = datetime.now(timezone.utc)

    expires_minutes = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60")
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(
            minutes=expires_minutes
        ),
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def get_bearer_token():
    authorization = request.headers.get("Authorization", "")

    if not authorization:
        return None

    parts = authorization.split()

    if len(parts) != 2:
        return None

    scheme, token = parts

    if scheme.lower() != "bearer":
        return None

    return token


def decode_access_token():
    token = get_bearer_token()

    if not token:
        return None

    try:
        return jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
        )

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
    ):
        return None
